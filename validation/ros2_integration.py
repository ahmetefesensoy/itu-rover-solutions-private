"""Real ROS 2 DDS checks against built executables, isolated by ROS_DOMAIN_ID."""
import bz2
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import cv2
import numpy as np
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import CompressedImage, Image, Imu
from std_msgs.msg import Char, String, Float64MultiArray
from tf2_msgs.msg import TFMessage
from ament_index_python.packages import get_package_prefix

ROOT = Path(__file__).resolve().parents[1]
RESULTS = Path(os.environ.get("ITU_RESULTS", str(ROOT / "validation")))
RESULTS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(get_package_prefix("reactive_robot_sim")) / "lib/reactive_robot_sim"))
from keyboard_control import KeyboardControl


class Harness:
    def __init__(self):
        rclpy.init()
        self.node = Node("assignment_validation")
        self.executor = SingleThreadedExecutor()
        self.executor.add_node(self.node)
        self.children = []
        self.handles = []
        self.report = {}

    def pump(self, seconds=.1):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.executor.spin_once(timeout_sec=.01)

    def wait(self, predicate, timeout=5):
        end = time.monotonic() + timeout
        while not predicate() and time.monotonic() < end:
            self.pump(.02)
        assert predicate(), "Timed out waiting for ROS message/discovery"

    def start(self, package, executable, *args):
        log = open(RESULTS / (executable + ".log"), "w")
        self.handles.append(log)
        process = subprocess.Popen(["ros2", "run", package, executable, *args], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        self.children.append(process)
        return process

    def stop(self, process):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)

    def compression(self):
        received = []
        sub = self.node.create_subscription(Char, "/solution", lambda m: received.append(m.data), 10)
        pub = self.node.create_publisher(String, "/bz2_message", 10)
        proc = self.start("iturover_compression_assignment", "bz2_solution.py", "--ros-args", "-p", "max_decoded_bytes:=1024")
        self.wait(lambda: pub.get_subscription_count() > 0 and self.node.count_publishers("/solution") > 0)
        cases = [(b"abcdddef", 100), (b"baba", 98), (b"\xff\xffa", 255)]
        for data, expected in cases:
            before = len(received)
            pub.publish(String(data=bz2.compress(data).hex()))
            self.wait(lambda: len(received) > before)
            assert received[-1] == expected
        self.pump(.1)
        before = len(received)
        for data in ("", "not hex", bz2.compress(b"").hex(), bz2.compress(b"a" * 1025).hex(), bz2.compress(b"abc")[:-2].hex()):
            pub.publish(String(data=data))
            self.pump(.1)
        assert len(received) == before, "Invalid BZ2 input produced a result"
        pub.publish(String(data=bz2.compress(b"zzzz").hex()))
        self.wait(lambda: len(received) > before)
        assert received[-1] == 122
        self.report["compression_ros2"] = {"valid_cases": 4, "invalid_cases_rejected": 5, "recovery": True}
        self.stop(proc)
        self.node.destroy_publisher(pub)
        self.node.destroy_subscription(sub)

    def images(self):
        raw, compressed = [], []
        subs = [self.node.create_subscription(Image, "/rover_view", raw.append, 10),
                self.node.create_subscription(CompressedImage, "/rover_view/compressed", compressed.append, 10)]
        pub = self.node.create_publisher(CompressedImage, "/video_topic/compressed", qos_profile_sensor_data)
        filters = self.node.create_publisher(String, "/filter", 10)
        proc = self.start("iturover_processing_assignment", "image_processor.py", "--ros-args", "-p", "max_compressed_bytes:=4096")
        self.wait(lambda: pub.get_subscription_count() > 0 and filters.get_subscription_count() > 0 and self.node.count_publishers("/rover_view") > 0 and self.node.count_publishers("/rover_view/compressed") > 0)
        data = cv2.imencode(".png", np.full((16, 20, 3), (0, 0, 255), np.uint8))[1].tobytes()
        for number, (mode, shape) in enumerate((("RGB", (16, 20)), ("GRAY", (16, 20)), ("RESIZE_UP", (32, 40)), ("RESIZE_DOWN", (8, 10))), 1):
            filters.publish(String(data=mode))
            self.pump(.1)
            msg = CompressedImage(data=data, format="png")
            msg.header.frame_id = "camera_test"
            msg.header.stamp.sec = number
            encoding = "rgb8" if mode == "RGB" else "mono8" if mode == "GRAY" else "bgr8"
            # Independent topics do not guarantee cross-topic callback ordering.
            # Observe a frame using the requested filter before checking pixels.
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                pub.publish(msg)
                self.pump(.1)
                if raw and compressed and raw[-1].header.stamp.sec == number and raw[-1].encoding == encoding and (raw[-1].height, raw[-1].width) == shape and compressed[-1].header.stamp.sec == number:
                    break
            assert raw and raw[-1].encoding == encoding
            assert (raw[-1].height, raw[-1].width) == shape
            assert compressed[-1].header == msg.header
            decoded = cv2.imdecode(np.frombuffer(compressed[-1].data, np.uint8), cv2.IMREAD_COLOR)
            assert decoded.shape[:2] == shape
            if mode == "RGB":
                assert decoded[5, 5, 2] > 240 and decoded[5, 5, 0] < 15, (decoded[5, 5].tolist(), raw[-1].encoding, compressed[-1].format)
                assert raw[-1].encoding == "rgb8" and bytes(raw[-1].data)[:3] == b"\xff\0\0"
            if mode == "GRAY":
                assert raw[-1].encoding == "mono8"
        before = len(compressed)
        for payload in (b"", b"bad image", b"x" * 4097):
            pub.publish(CompressedImage(data=payload))
            self.pump(.1)
        assert len(compressed) == before
        filters.publish(String(data="INVALID"))
        self.pump(.05)
        pub.publish(CompressedImage(data=data))
        self.wait(lambda: len(compressed) > before)
        assert (raw[-1].height, raw[-1].width) == (8, 10), "Invalid filter changed last valid filter"
        self.report["processing_ros2"] = {"filters": 4, "invalid_frames_rejected": 3, "header_preserved": True, "raw_and_compressed_agree": True, "recovery": True}
        self.stop(proc)
        for s in subs:
            self.node.destroy_subscription(s)
        self.node.destroy_publisher(pub)
        self.node.destroy_publisher(filters)

    def odometry(self):
        odom, transforms = [], []
        subs = [self.node.create_subscription(Odometry, "/odom", odom.append, 10), self.node.create_subscription(TFMessage, "/tf", transforms.append, 10)]
        left = self.node.create_publisher(Float64MultiArray, "/drive_system_left_motors_feedbacks", qos_profile_sensor_data)
        right = self.node.create_publisher(Float64MultiArray, "/drive_system_right_motors_feedbacks", qos_profile_sensor_data)
        imu = self.node.create_publisher(Imu, "/imu1/data", qos_profile_sensor_data)
        clock = self.node.create_publisher(Clock, "/clock", 10)
        proc = self.start("iturover_odometry_assignment", "odometry.py", "--ros-args", "-p", "use_sim_time:=true")
        self.wait(lambda: all(p.get_subscription_count() > 0 for p in (left, right, imu, clock)) and self.node.count_publishers("/odom") > 0)

        def send(t, sensors=True):
            msg = Clock()
            ns = round(t * 1e9)
            msg.clock.sec, msg.clock.nanosec = divmod(ns, 10**9)
            clock.publish(msg)
            self.pump(.03)
            if sensors:
                rpm = 60 / (2 * math.pi * .135)
                left.publish(Float64MultiArray(data=[rpm, rpm]))
                right.publish(Float64MultiArray(data=[rpm, rpm]))
                orientation = Imu()
                orientation.orientation.w = 1.0
                imu.publish(orientation)
            self.pump(.03)

        send(10)
        for i in range(1, 12):
            send(10 + i * .1)
        self.wait(lambda: odom and odom[-1].twist.twist.linear.x > .9)
        moving = odom[-1]
        assert .85 <= moving.pose.pose.position.x <= 1.15, moving.pose.pose.position.x
        assert abs(moving.pose.pose.position.y) < 1e-6
        send(12, sensors=False)
        self.wait(lambda: odom[-1].twist.twist.linear.x == 0)
        assert abs(odom[-1].pose.pose.position.x - moving.pose.pose.position.x) < .01
        send(1, sensors=False)
        self.wait(lambda: odom[-1].header.stamp.sec == 1)
        assert abs(odom[-1].pose.pose.position.x) < 1e-9
        assert odom[-1].twist.twist.linear.x == 0
        send(1.1)
        send(1.2)
        send(1.3)
        self.wait(lambda: odom[-1].twist.twist.linear.x > .9)
        assert odom[-1].pose.pose.position.x < .3
        assert transforms
        latest = transforms[-1].transforms[0]
        self.wait(lambda: odom[-1].header.stamp == latest.header.stamp)
        assert latest.transform.translation.x == odom[-1].pose.pose.position.x
        self.report["odometry_ros2"] = {"commanded_speed_m_s": 1.0, "observed_x_m": moving.pose.pose.position.x, "stale_stop": True, "clock_reset": True, "tf_matches_odom": True}
        self.stop(proc)
        for s in subs:
            self.node.destroy_subscription(s)
        for p in (left, right, imu, clock):
            self.node.destroy_publisher(p)

    def keyboard(self):
        received = []
        sub = self.node.create_subscription(Twist, "/cmd_vel", received.append, 10)
        now = [100.0]
        controller = KeyboardControl(enable_listener=False, monotonic=lambda: now[0])
        controller.timer.cancel()
        self.executor.add_node(controller)
        self.wait(lambda: controller.publisher.get_subscription_count() > 0)
        controller.on_press(SimpleNamespace(char="W"))
        controller.on_press(SimpleNamespace(char="a"))
        controller.publish_command()
        self.wait(lambda: received)
        assert received[-1].linear.x == .2 and received[-1].angular.z == .7
        controller.on_release(SimpleNamespace(char="W"))
        controller.publish_command()
        self.pump(.1)
        assert received[-1].linear.x == 0 and received[-1].angular.z == .7
        now[0] = 160.0
        controller.publish_command()
        self.pump(.1)
        assert received[-1].linear.x == 0 and received[-1].angular.z == 0
        assert controller.state.reason == "Time limit reached"
        now[0] = 160.3
        controller.publish_command()
        assert controller.shutdown_requested and rclpy.ok()
        controller.close()
        self.executor.remove_node(controller)
        self.node.destroy_subscription(sub)
        self.report["keyboard_ros2"] = {"uppercase": True, "combined_keys": True, "release": True, "60_second_stop": True, "headless_event_injection": True}

    def close(self):
        for proc in self.children:
            self.stop(proc)
        for handle in self.handles:
            handle.close()
        self.executor.shutdown()
        self.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    harness = Harness()
    try:
        for check in (harness.compression, harness.images, harness.odometry, harness.keyboard):
            check()
            print("PASS", check.__name__, flush=True)
        (RESULTS / "ros2_results.json").write_text(json.dumps(harness.report, indent=2) + "\n")
    finally:
        harness.close()
