"""Run with a sourced ROS 2 environment: python3 -m unittest discover -s validation -v."""
import bz2
import importlib.util
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for directory in ("iturover_odometry_assignment_ros2/src", "iturover_keyboard_control_assignment_ros2/scripts", "iturover_processing_assignment_ros2/src", "iturover_compression_assignment_ros2/scripts"):
    sys.path.insert(0, str(ROOT / directory))

from control_state import ControlState
from image_processor import process_frame
from odometry_core import OdometryIntegrator, average_pair, quaternion_yaw


def codec_at(repo):
    spec = importlib.util.spec_from_file_location(repo + "_codec", ROOT / repo / "scripts/bz2_codec.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.solve_hex


class CodecCases:
    def test_assignment_example(self):
        self.assertEqual(self.solve(bz2.compress(b"abcdddef").hex()), (100, 3))

    def test_publisher_example(self):
        self.assertEqual(self.solve(bz2.compress(b"somewhere, something incredible is waiting to be known.").hex()), (101, 7))

    def test_first_occurrence_wins_tie(self):
        self.assertEqual(self.solve(bz2.compress(b"baba").hex()), (98, 2))

    def test_all_byte_values(self):
        self.assertEqual(self.solve(bz2.compress(bytes(range(256)) + b"\xff\xff").hex()), (255, 3))

    def test_whitespace_hex(self):
        data = bz2.compress(b"aaa").hex()
        self.assertEqual(self.solve(" \n".join(data[i:i+2] for i in range(0, len(data), 2))), (97, 3))

    def test_bad_hex(self):
        for value in ("", "z1", "0", "hello"):
            with self.subTest(value=value), self.assertRaises((ValueError, OSError, EOFError)):
                self.solve(value)

    def test_empty_decoded(self):
        with self.assertRaises(ValueError):
            self.solve(bz2.compress(b"").hex())

    def test_truncation(self):
        payload = bz2.compress(b"abcdddef")
        for size in range(1, len(payload)):
            with self.subTest(size=size), self.assertRaises((ValueError, OSError, EOFError)):
                self.solve(payload[:size].hex())

    def test_trailing_garbage(self):
        with self.assertRaises((ValueError, OSError, EOFError)):
            self.solve((bz2.compress(b"aaa") + b"garbage").hex())

    def test_concatenated_streams(self):
        data = bz2.compress(b"aa") + bz2.compress(b"bbbb")
        self.assertEqual(self.solve(data.hex()), (98, 4))

    def test_output_limit_and_exact_boundary(self):
        data = bz2.compress(b"a" * 4097).hex()
        with self.assertRaises(ValueError):
            self.solve(data, max_decoded_bytes=4096)
        self.assertEqual(self.solve(data, max_decoded_bytes=4097), (97, 4097))

    def test_input_limit(self):
        with self.assertRaises(ValueError):
            self.solve(bz2.compress(b"abc").hex(), max_compressed_bytes=4)

    def test_multistream_combined_limit(self):
        with self.assertRaises(ValueError):
            self.solve((bz2.compress(b"aaa") * 3).hex(), max_decoded_bytes=8)

    def test_random_reference_200_payloads(self):
        rng = random.Random(20261108)
        for i in range(200):
            data = bytes(rng.randrange(256) for _ in range(rng.randint(1, 1500)))
            # Independent brute-force count, preserving first occurrence on ties.
            best = max(dict.fromkeys(data), key=data.count)
            with self.subTest(case=i):
                self.assertEqual(self.solve(bz2.compress(data).hex()), (best, data.count(best)))


class TestCompressionROS1(CodecCases, unittest.TestCase):
    solve = staticmethod(codec_at("iturover_compression_assignment"))


class TestCompressionROS2(CodecCases, unittest.TestCase):
    solve = staticmethod(codec_at("iturover_compression_assignment_ros2"))


class TestImage(unittest.TestCase):
    def png(self, frame):
        return cv2.imencode(".png", frame)[1].tobytes()

    def test_rgb_color_roundtrip(self):
        for color in ((0, 0, 255), (255, 0, 0), (0, 255, 0)):
            data, raw, encoding = process_frame(self.png(np.full((32, 32, 3), color, np.uint8)), "RGB")
            decoded = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            np.testing.assert_allclose(decoded[16, 16], color, atol=3)
            np.testing.assert_equal(raw[16, 16], color[::-1])
            self.assertEqual(encoding, "rgb8")

    def test_gray_luminance(self):
        _, frame, encoding = process_frame(self.png(np.full((16, 16, 3), (0, 0, 255), np.uint8)), "GRAY")
        self.assertEqual(frame.shape, (16, 16))
        self.assertAlmostEqual(int(frame[0, 0]), 76, delta=1)
        self.assertEqual(encoding, "mono8")

    def test_resize_up(self):
        _, frame, _ = process_frame(self.png(np.zeros((7, 9, 3), np.uint8)), "RESIZE_UP")
        self.assertEqual(frame.shape, (14, 18, 3))

    def test_resize_down_odd_dimensions(self):
        _, frame, _ = process_frame(self.png(np.zeros((7, 9, 3), np.uint8)), "RESIZE_DOWN")
        self.assertEqual(frame.shape, (3, 4, 3))

    def test_single_pixel(self):
        _, frame, _ = process_frame(self.png(np.zeros((1, 1, 3), np.uint8)), "RESIZE_DOWN")
        self.assertEqual(frame.shape, (1, 1, 3))

    def test_empty_and_corrupt(self):
        for data in (b"", b"not an image", b"\xff\xd8"):
            with self.subTest(data=data), self.assertRaises((ValueError, cv2.error)):
                process_frame(data, "RGB")

    def test_pixel_limit(self):
        with self.assertRaises(ValueError):
            process_frame(self.png(np.zeros((10, 10, 3), np.uint8)), "RESIZE_UP", max_output_pixels=399)

    def test_unknown_filter(self):
        with self.assertRaises(ValueError):
            process_frame(b"", "INVALID")


class TestOdometry(unittest.TestCase):
    def test_strict_policy_rejects_flagged_q14(self):
        core = OdometryIntegrator(heading_source="imu")
        self.assertFalse(core.imu((0, 0, 0, 16384), 0, orientation_available=False))

    def test_recording_policy_accepts_only_flagged_q14_scale(self):
        core = OdometryIntegrator(heading_source="imu", orientation_policy="assignment_q14")
        self.assertTrue(core.imu((0, 0, 0, 16384), 0, orientation_available=False))
        for bad in ((0,0,0,1), (0,0,0,100), (0,0,0,0), (math.nan,0,0,16384)):
            with self.subTest(q=bad):
                self.assertFalse(core.imu(bad, .1, orientation_available=False))

    def test_scaled_recording_heading_ignores_wheel_turn_bias(self):
        core = OdometryIntegrator(heading_source="imu", orientation_policy="assignment_q14")
        for i in range(101):
            t = i*.1
            factor = 60 / (2*math.pi*.135)
            core.wheel("left", [.8*factor]*2, t)
            core.wheel("right", [1.2*factor]*2, t)
            core.imu((0,0,0,16384), t, orientation_available=False)
            state = core.step(t)
        self.assertAlmostEqual(state.x, 10, places=10)
        self.assertEqual((state.y,state.yaw), (0,0))

    def test_recording_square_has_four_corners_and_closes(self):
        core = OdometryIntegrator(heading_source="imu", orientation_policy="assignment_q14")
        factor = 60 / (2*math.pi*.135)
        t=0.0
        for side in range(4):
            angle=side*math.pi/2
            for _ in range(101):
                core.wheel("left",[factor]*2,t)
                core.wheel("right",[factor]*2,t)
                core.imu((0,0,16384*math.sin(angle/2),16384*math.cos(angle/2)),t,False)
                state=core.step(t)
                t+=.01
            # Turn in place: keep movement at zero while heading changes.
            for j in range(1,101):
                yaw=angle+j*.01*math.pi/2
                core.wheel("left",[0,0],t)
                core.wheel("right",[0,0],t)
                core.imu((0,0,16384*math.sin(yaw/2),16384*math.cos(yaw/2)),t,False)
                state=core.step(t)
                t+=.01
        self.assertLess(math.hypot(state.x,state.y),.03)
        self.assertAlmostEqual(state.yaw,0,places=8)

    def test_imu_rate_does_not_depend_on_timer_tick(self):
        core=OdometryIntegrator(heading_source="imu")
        self.samples(core,0,yaw=0)
        self.samples(core,.1,yaw=.1)
        self.assertAlmostEqual(core.step(.1).angular,1)
        self.assertAlmostEqual(core.step(.11).angular,1)

    def test_recording_policy_keeps_stale_imu_stopped(self):
        core=OdometryIntegrator(heading_source="imu",orientation_policy="assignment_q14")
        self.samples(core,0)
        core.step(0)
        core.wheel("left",[60,60],1)
        core.wheel("right",[60,60],1)
        self.assertFalse(core.step(1).fresh)

    def test_recording_clock_rewind_reanchors_heading(self):
        core=OdometryIntegrator(heading_source="imu",orientation_policy="assignment_q14")
        core.imu((0,0,16384,0),10,False)
        core.step(1)
        core.imu((0,0,0,16384),1,False)
        self.assertEqual(core.reset_count,1)
        self.assertEqual(core.heading[0],0)

    def test_unknown_orientation_policy_rejected(self):
        with self.assertRaises(ValueError):
            OdometryIntegrator(orientation_policy="ignore_everything")

    def test_first_interval_is_not_lost(self):
        core = OdometryIntegrator()
        rpm = 60 / (2 * math.pi * .135)
        core.wheel("left", [rpm]*2, 0)
        core.wheel("right", [rpm]*2, 0)
        self.assertAlmostEqual(core.step(.1).x, .1)

    def test_constant_speed_independent_of_timer_frequency(self):
        for interval in (.01, .05, .1, .2):
            core = OdometryIntegrator()
            rpm = 60 / (2 * math.pi * .135)
            for i in range(round(10/interval)+1):
                t = i * interval
                core.wheel("left", [rpm]*2, t)
                core.wheel("right", [rpm]*2, t)
                state = core.step(t)
            self.assertAlmostEqual(state.x, 10, places=10)

    def test_overflowing_speed_holds_finite_pose(self):
        core = OdometryIntegrator(wheel_radius=1e308)
        core.wheel("left", [1e308]*2, 0)
        core.wheel("right", [1e308]*2, 0)
        state = core.step(.1)
        self.assertFalse(state.fresh)
        self.assertEqual((state.x, state.y, state.linear, state.angular), (0, 0, 0, 0))

    def test_new_wheel_speed_does_not_change_previous_interval(self):
        core = OdometryIntegrator()
        core.wheel("left", [0, 0], 0)
        core.wheel("right", [0, 0], 0)
        core.step(0)
        rpm = 60 / (2 * math.pi * .135)
        core.wheel("left", [rpm, rpm], .1)
        core.wheel("right", [rpm, rpm], .1)
        self.assertEqual(core.step(.1).x, 0)
        self.assertAlmostEqual(core.step(.2).x, .1)

    def test_wheel_circle_without_imu(self):
        core = OdometryIntegrator()
        # v=1, yaw rate=1 -> unit radius circle with known analytic endpoint.
        for i in range(1001):
            t = i * .01
            factor = 60 / (2 * math.pi * .135)
            core.wheel("left", [(1-.890/2)*factor]*2, t)
            core.wheel("right", [(1+.890/2)*factor]*2, t)
            state = core.step(t)
        self.assertAlmostEqual(state.x, math.sin(10), places=10)
        self.assertAlmostEqual(state.y, 1-math.cos(10), places=10)

    def test_wheel_in_place_rotation(self):
        core = OdometryIntegrator()
        for i in range(101):
            core.wheel("left", [-60, -60], i*.1)
            core.wheel("right", [60, 60], i*.1)
            state = core.step(i*.1)
        self.assertEqual((state.x, state.y), (0, 0))
        self.assertGreater(abs(state.angular), 0)

    def samples(self, core, t, speed=1.0, yaw=0.0):
        rpm = speed * 60 / (2 * math.pi * core.wheel_radius)
        core.wheel("left", [rpm, rpm], t)
        core.wheel("right", [rpm, rpm], t)
        core.imu((0, 0, math.sin(yaw / 2), math.cos(yaw / 2)), t)

    def test_exact_pair_required(self):
        for bad in ([], [60], [1, 2, 3], [math.nan, 60], [math.inf, 60]):
            self.assertIsNone(average_pair(bad))
        self.assertEqual(average_pair([30, 50]), 40)

    def test_normalized_quaternion(self):
        self.assertAlmostEqual(quaternion_yaw(0, 0, 2, 2), math.pi / 2)
        self.assertIsNone(quaternion_yaw(0, 0, 0, 0))
        self.assertIsNone(quaternion_yaw(0, math.nan, 0, 1))

    def test_straight_10_m(self):
        core = OdometryIntegrator(heading_source="imu")
        for i in range(101):
            self.samples(core, i * .1)
            state = core.step(i * .1)
        self.assertAlmostEqual(state.x, 10.0, places=10)
        self.assertAlmostEqual(state.y, 0.0, places=10)

    def test_reverse_10_m(self):
        core = OdometryIntegrator(heading_source="imu")
        for i in range(101):
            self.samples(core, i * .1, speed=-1)
            state = core.step(i * .1)
        self.assertAlmostEqual(state.x, -10.0, places=10)

    def test_analytic_circle(self):
        core = OdometryIntegrator(heading_source="imu")
        for i in range(1001):
            t = i * .01
            self.samples(core, t, yaw=t)
            state = core.step(t)
        self.assertAlmostEqual(state.x, math.sin(10), places=10)
        self.assertAlmostEqual(state.y, 1 - math.cos(10), places=10)

    def test_yaw_wrap(self):
        core = OdometryIntegrator(heading_source="imu")
        self.samples(core, 0, yaw=math.radians(179))
        core.step(0)
        self.samples(core, .1, yaw=math.radians(-179))
        self.assertAlmostEqual(core.step(.1).angular, math.radians(2) / .1)

    def test_stale_data_stops_and_holds(self):
        core = OdometryIntegrator(heading_source="imu")
        self.samples(core, 0)
        core.step(0)
        core.step(.1)
        stopped = core.step(.7)
        self.assertFalse(stopped.fresh)
        self.assertEqual(stopped.linear, 0)
        self.assertEqual(core.step(100).x, stopped.x)

    def test_missing_one_side(self):
        core = OdometryIntegrator(heading_source="imu")
        core.wheel("left", [60, 60], 0)
        core.imu((0, 0, 0, 1), 0)
        self.assertFalse(core.step(.1).fresh)

    def test_invalid_imu_covariance(self):
        core = OdometryIntegrator(heading_source="imu")
        self.samples(core, 0)
        core.imu((0, 0, 0, 1), .1, orientation_available=False)
        self.assertFalse(core.step(.1).fresh)

    def test_clock_rewind_resets_pose_and_inputs(self):
        core = OdometryIntegrator(heading_source="imu")
        self.samples(core, 10)
        core.step(10)
        self.samples(core, 10.1)
        self.assertGreater(core.step(10.1).x, 0)
        reset = core.step(1)
        self.assertEqual(reset.x, 0)
        self.assertFalse(reset.fresh)
        self.assertEqual(core.reset_count, 1)

    def test_clock_pause_and_forward_jump(self):
        core = OdometryIntegrator(heading_source="imu")
        self.samples(core, 1)
        core.step(1)
        self.assertEqual(core.step(1).x, 0)
        self.samples(core, 50)
        self.assertEqual(core.step(50).x, 0)

    def test_recovery_does_not_bridge_missing_interval(self):
        core = OdometryIntegrator(heading_source="imu")
        self.samples(core, 0)
        core.step(0)
        core.step(1)
        self.samples(core, 1.1)
        self.assertEqual(core.step(1.1).x, 0)
        self.samples(core, 1.2)
        self.assertAlmostEqual(core.step(1.2).x, .1)

    def test_bad_parameters(self):
        for value in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                OdometryIntegrator(wheel_radius=value)


class TestKeyboard(unittest.TestCase):
    def test_all_16_combinations(self):
        for flags in itertools.product((False, True), repeat=4):
            state = ControlState()
            for key, pressed in zip("wasd", flags):
                if pressed:
                    state.press(key)
            w, a, s, d = flags
            self.assertEqual(state.command(0), ((w-s)*.2, (a-d)*.7))

    def test_uppercase_and_release(self):
        state = ControlState()
        state.press("W")
        self.assertEqual(state.command(0), (.2, 0))
        state.release("w")
        self.assertEqual(state.command(.1), (0, 0))

    def test_cancelled_keys_do_not_start_deadline(self):
        state = ControlState()
        state.press("w")
        state.press("s")
        state.command(100)
        self.assertIsNone(state.started_at)

    def test_exact_60_second_deadline(self):
        state = ControlState()
        state.press("w")
        state.command(100)
        self.assertEqual(state.command(159.999), (.2, 0))
        self.assertEqual(state.command(160), (0, 0))
        self.assertFalse(state.shutdown_ready(160.24))
        self.assertTrue(state.shutdown_ready(160.25))

    def test_idle_time_before_movement_not_counted(self):
        state = ControlState()
        state.command(1000)
        state.press("w")
        self.assertEqual(state.command(2000), (.2, 0))
        self.assertEqual(state.started_at, 2000)

    def test_repeated_keys_do_not_restart_deadline(self):
        state = ControlState()
        state.press("w")
        state.command(0)
        for t in range(1, 60):
            state.press("w")
            state.command(t)
        self.assertEqual(state.command(60), (0, 0))

    def test_escape_is_latched(self):
        state = ControlState()
        state.press("esc")
        state.press("w")
        self.assertEqual(state.command(0), (0, 0))

    def test_external_stop_is_latched(self):
        state = ControlState()
        state.press("w")
        state.command(0)
        state.stop("listener failure")
        self.assertEqual(state.command(.1), (0, 0))
        self.assertEqual(state.reason, "listener failure")

    def test_unknown_keys_ignored(self):
        state = ControlState()
        state.press(None)
        state.press("f")
        self.assertEqual(state.command(0), (0, 0))

    def test_invalid_parameters(self):
        for value in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                ControlState(duration=value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
