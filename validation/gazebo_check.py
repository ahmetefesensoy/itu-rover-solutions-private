"""Drive the assignment's Gazebo Classic world on an isolated ROS domain/master.

Keyboard events and the deadline are injected; actual Gazebo motion is measured.
"""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from ament_index_python.packages import get_package_prefix

sys.path.insert(0, str(Path(get_package_prefix("reactive_robot_sim")) / "lib/reactive_robot_sim"))
from keyboard_control import KeyboardControl


def main():
    os.environ["GAZEBO_MASTER_URI"] = "http://127.0.0.1:11365"
    log = open("/tmp/itu-gazebo-check.log", "w")
    process = subprocess.Popen(["ros2", "launch", "reactive_robot_sim", "reactive_robot_sim.launch.py", "gui:=false", "model:=burger"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    rclpy.init()
    node = Node("gazebo_assignment_validation")
    odom, commands = [], []
    node.create_subscription(Odometry, "/odom", odom.append, 10)
    node.create_subscription(Twist, "/cmd_vel", commands.append, 10)
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    controller = None

    def pump(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=.01)

    def position():
        p = odom[-1].pose.pose.position
        return (p.x, p.y)

    try:
        end = time.monotonic() + 45
        while not odom and time.monotonic() < end:
            assert process.poll() is None, "Simulation launch exited; see log"
            pump(.1)
        assert odom, "Gazebo did not publish /odom"
        pump(1)
        clock = [100.0]
        controller = KeyboardControl(enable_listener=False, monotonic=lambda: clock[0])
        executor.add_node(controller)
        pump(.5)
        assert controller.publisher.get_subscription_count() >= 2, "Gazebo cmd_vel subscriber missing"
        before = position()
        controller.on_press(SimpleNamespace(char="w"))
        pump(1.5)
        after_move = position()
        distance = math.dist(before, after_move)
        assert distance > .03, (before, after_move)
        clock[0] = 160.0
        pump(1)
        assert controller.state.reason == "Time limit reached"
        assert commands[-1].linear.x == 0 and commands[-1].angular.z == 0
        assert abs(odom[-1].twist.twist.linear.x) < .03
        stopped = position()
        pump(.5)
        drift = math.dist(stopped, position())
        assert drift < .02, drift
        assert all(m.linear.x == 0 and m.angular.z == 0 for m in commands[-3:])
        # Exercise the shutdown branch after the zero-command grace period.
        clock[0] = 160.3
        controller.publish_command()
        assert controller.shutdown_requested
        result = {"world": "obs_corridor_world", "model": "burger", "distance_m": distance,
                  "drift_after_stop_m": drift, "stopped_speed_m_s": odom[-1].twist.twist.linear.x,
                  "deadline_stop_and_shutdown": True,
                  "note": "Headless Gazebo Classic; synthetic keyboard events and accelerated monotonic deadline."}
        Path("/tmp/itu-gazebo-results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2), flush=True)
    finally:
        if controller is not None:
            executor.remove_node(controller)
            controller.close()
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
        log.close()


if __name__ == "__main__":
    main()
