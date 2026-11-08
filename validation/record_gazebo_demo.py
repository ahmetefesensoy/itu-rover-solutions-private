"""Record the actual assignment world and controller using a private Xvfb display."""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import rclpy
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from nav_msgs.msg import Odometry
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

sys.path.insert(0, str(Path(get_package_prefix("reactive_robot_sim")) / "lib/reactive_robot_sim"))
from keyboard_control import KeyboardControl


def main():
    os.environ["GAZEBO_MASTER_URI"] = "http://127.0.0.1:11366"
    os.environ["GAZEBO_MODEL_DATABASE_URI"] = ""
    description_parent=os.path.dirname(get_package_share_directory("turtlebot3_description"))
    os.environ["GAZEBO_MODEL_PATH"]=os.pathsep.join(filter(None,(os.environ.get("GAZEBO_MODEL_PATH"),description_parent)))
    original = Path(get_package_share_directory("reactive_robot_sim")) / "worlds/obs_corridor_world.world"
    tree = ET.parse(original)
    # The supplied world references decorative Husky/Mars meshes that are not
    # shipped in the repo. Hide their visuals; preserve every collision body.
    hidden_visuals = 0
    for parent in tree.iter():
        for child in list(parent):
            if child.tag == "visual" and child.find("geometry/mesh") is not None:
                parent.remove(child)
                hidden_visuals += 1
    tree.find("world/gui/camera/pose").text = "3 6.5 3 0 0.6 2.35"
    tree.write("/tmp/itu-showcase.world")
    log = open("/tmp/itu-showcase.log", "w")
    sim = subprocess.Popen(["ros2", "launch", "reactive_robot_sim", "reactive_robot_sim.launch.py", "gui:=false", "model:=burger", "world:=/tmp/itu-showcase"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    rclpy.init()
    node = Node("showcase_recorder")
    samples = []
    phase = ["Ready"]
    node.create_subscription(Odometry, "/odom", lambda m: samples.append({"time":time.monotonic(), "x":m.pose.pose.position.x, "y":m.pose.pose.position.y, "v":m.twist.twist.linear.x, "phase":phase[0]}), 10)
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    controller = None
    recorder = None
    client = None

    def pump(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=.01)

    try:
        end = time.monotonic() + 55
        while not samples and time.monotonic() < end:
            pump(.1)
        assert samples, "No Gazebo odometry"
        client = subprocess.Popen(["gzclient", "-g", "/tmp/librobot_recording_camera.so"], stdout=log, stderr=subprocess.STDOUT)
        pump(25)
        windows = subprocess.run(["xdotool", "search", "--name", "Gazebo"], text=True, capture_output=True)
        graphical = windows.returncode == 0 and bool(windows.stdout.strip())
        if graphical:
            window = windows.stdout.splitlines()[-1]
            subprocess.run(["xdotool", "windowmove", window, "0", "0", "windowsize", window, "1280", "720"], check=True)
            subprocess.run(["xdotool", "windowfocus", window], check=True)
        controller = KeyboardControl(enable_listener=True)
        executor.add_node(controller)
        pump(1)
        if graphical:
            recorder = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "x11grab", "-video_size", "1280x720", "-framerate", "20", "-i", os.environ["DISPLAY"], "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "/tmp/itu-keyboard-demo.mp4"], stdout=log, stderr=log)
        beginning = samples[-1].copy()
        pump(2)
        phase[0] = "W: forward"
        subprocess.run(["xdotool", "keydown", "w"], check=True)
        pump(3)
        phase[0] = "W+A: forward and left"
        subprocess.run(["xdotool", "keydown", "a"], check=True)
        pump(2)
        subprocess.run(["xdotool", "keyup", "w", "keyup", "a"], check=True)
        phase[0] = "Released: stopped"
        pump(2)
        phase[0] = "S: reverse"
        subprocess.run(["xdotool", "keydown", "s"], check=True)
        pump(2)
        subprocess.run(["xdotool", "keyup", "s"], check=True)
        subprocess.run(["xdotool", "key", "Escape"], check=True)
        phase[0] = "Esc: stopped"
        pump(3)
        assert controller.shutdown_requested
        assert abs(samples[-1]["v"]) < .03
        assert math.hypot(samples[-1]["x"]-beginning["x"], samples[-1]["y"]-beginning["y"]) > .1
        Path("/tmp/itu-keyboard-demo.json").write_text(json.dumps({"world":"obs_corridor_world", "viewport_recorded": graphical,"camera":"rendering-only close-up plugin tracks existing robot world pose", "missing_decorative_mesh_visuals_hidden":hidden_visuals,"collision_geometry_unchanged":True, "input":"XTEST X11 key events read by the real pynput listener", "samples":samples}, indent=2))
    finally:
        if recorder is not None:
            recorder.send_signal(signal.SIGINT)
            recorder.wait(timeout=15)
        if client is not None and client.poll() is None:
            client.terminate()
            try:
                client.wait(timeout=3)
            except subprocess.TimeoutExpired:
                client.kill()
                client.wait(timeout=3)
        if controller is not None:
            executor.remove_node(controller)
            controller.close()
        executor.shutdown()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        if sim.poll() is None:
            os.killpg(sim.pid, signal.SIGINT)
            try:
                sim.wait(timeout=8)
            except subprocess.TimeoutExpired:
                os.killpg(sim.pid, signal.SIGKILL)
                sim.wait()
        log.close()


if __name__ == "__main__":
    main()
