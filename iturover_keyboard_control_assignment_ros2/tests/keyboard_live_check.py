"""Real pynput/X11 events, real 60 seconds, SIGINT and SIGTERM checks.

Run under xvfb-run after sourcing the built Humble workspace.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from Xlib import X, display
from ament_index_python.packages import get_package_prefix


def main():
    rclpy.init()
    node = Node("keyboard_live_validation")
    messages = []
    node.create_subscription(Twist, "/cmd_vel", lambda m: messages.append((time.monotonic(), m.linear.x, m.angular.z)), 20)
    # XTEST events pass through X11's normal keyboard path (unlike XSendEvent).
    connection = display.Display()
    screen = connection.screen()
    window = screen.root.create_window(0, 0, 300, 200, 0, screen.root_depth,
                                      X.InputOutput, X.CopyFromParent,
                                      background_pixel=screen.white_pixel,
                                      event_mask=X.KeyPressMask | X.KeyReleaseMask)
    window.set_wm_name("ITU keyboard validation")
    window.map()
    connection.sync()
    window.set_input_focus(X.RevertToParent, X.CurrentTime)
    connection.sync()
    results = {}

    def pump(seconds):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            rclpy.spin_once(node, timeout_sec=.02)

    try:
        for mode in ("deadline", "SIGINT", "SIGTERM"):
            messages.clear()
            log = open("/tmp/itu-keyboard-" + mode + ".log", "w")
            executable = str(Path(get_package_prefix("reactive_robot_sim")) / "lib/reactive_robot_sim/keyboard_control.py")
            duration = os.environ.get("ITU_KEY_DURATION", "60.0")
            process = subprocess.Popen([sys.executable, executable, "--ros-args", "-p", "duration:=" + duration], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            pressed = False
            try:
                end = time.monotonic() + 10
                while not messages and time.monotonic() < end and process.poll() is None:
                    pump(.05)
                assert messages, "Controller did not publish idle commands"
                subprocess.run(["xdotool", "keydown", "w"], check=True)
                pressed = True
                end = time.monotonic() + 3
                while not any(v > 0 for _, v, _ in messages) and time.monotonic() < end:
                    pump(.05)
                assert any(v > 0 for _, v, _ in messages), "Real X11 key was not received"
                start = next(t for t, v, _ in messages if v > 0)
                if mode != "deadline":
                    os.killpg(process.pid, getattr(signal, mode))
                    deadline = time.monotonic() + 5
                else:
                    deadline = start + float(duration) + 4
                while process.poll() is None and time.monotonic() < deadline:
                    pump(.05)
                pump(.15)
                assert process.poll() == 0, (mode, process.poll())
                stop_commands = [(t, v, w) for t, v, w in messages if t > start and v == 0 and w == 0]
                assert len(stop_commands) >= 3, "Missing repeated zero commands"
                stop_time = stop_commands[0][0] - start
                if mode == "deadline":
                    assert float(duration)-.2 <= stop_time <= float(duration)+.3, stop_time
                else:
                    assert stop_time < 1.0, stop_time
                results[mode] = {"real_x11_key_received": True, "stop_after_seconds": stop_time,
                                 "zero_commands": len(stop_commands), "exit_code": process.returncode}
                print("PASS", mode, results[mode], flush=True)
            finally:
                if pressed:
                    subprocess.run(["xdotool", "keyup", "w"], check=True)
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                log.close()
        Path("/tmp/itu-keyboard-live-results.json").write_text(json.dumps(results, indent=2) + "\n")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        window.destroy()
        connection.close()


if __name__ == "__main__":
    main()
