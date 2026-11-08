"""Run: python3 -m unittest discover -s tests -v"""
import math
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from odometry_core import OdometryIntegrator, average_pair, quaternion_yaw

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

if __name__ == "__main__":
    unittest.main(verbosity=2)
