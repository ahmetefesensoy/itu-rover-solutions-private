#!/usr/bin/env python3
"""WASD control with a monotonic deadline and repeated zero commands on exit."""
import signal
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions

from control_state import ControlState


class KeyboardControl(Node):
    def __init__(self, enable_listener=True, monotonic=time.monotonic):
        super().__init__("keyboard_control")
        for name, value in (("linear_speed", 0.20), ("angular_speed", 0.70), ("duration", 60.0)):
            self.declare_parameter(name, value)
        self.state = ControlState(*(self.get_parameter(n).value for n in ("linear_speed", "angular_speed", "duration")))
        self.monotonic = monotonic
        self.keys_lock = threading.RLock()
        self.publisher = self.create_publisher(Twist, "/cmd_vel", 1)
        self.previous_command = (0.0, 0.0)
        self.stop_logged = False
        self.shutdown_requested = False
        self.listener = None
        if enable_listener:
            # Lazy import permits headless logic/integration tests without X11.
            from pynput import keyboard
            self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
            self.listener.start()
        self.timer = self.create_timer(0.05, self.publish_command, clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.get_logger().info(f"WASD ready; {self.state.duration:g}s from first nonzero command. Esc/Ctrl+C stop the rover.")

    @staticmethod
    def key_name(key):
        if str(key) == "Key.esc":
            return "esc"
        name = getattr(key, "char", None)
        return name.lower() if isinstance(name, str) else None

    def on_press(self, key):
        name = self.key_name(key)
        with self.keys_lock:
            self.state.press(name)
        if name == "esc":
            return False

    def on_release(self, key):
        with self.keys_lock:
            self.state.release(self.key_name(key))

    def request_stop(self, reason="Stop requested"):
        with self.keys_lock:
            self.state.stop(reason)

    def publish_command(self):
        now = self.monotonic()
        with self.keys_lock:
            if self.listener is not None and not self.listener.is_alive():
                self.state.stop("Keyboard listener stopped")
            linear, angular = self.state.command(now)
            reason = self.state.reason
            finished = self.state.shutdown_ready(now)
        command = Twist()
        command.linear.x, command.angular.z = linear, angular
        self.publisher.publish(command)
        if (linear, angular) != self.previous_command:
            motion = "forward" if linear > 0 else "backward" if linear < 0 else "no translation"
            rotation = "left" if angular > 0 else "right" if angular < 0 else "no rotation"
            self.get_logger().info(f"Movement: {motion}, {rotation}; v={linear:.2f}, w={angular:.2f}")
            self.previous_command = (linear, angular)
        if reason is not None and not self.stop_logged:
            self.get_logger().info(f"{reason}. Publishing zero velocity before shutdown.")
            self.stop_logged = True
        # Humble's global executor waits for callbacks during shutdown.
        # Calling shutdown from this callback deadlocks on itself.
        if finished:
            self.shutdown_requested = True
            self.timer.cancel()

    def close(self):
        if rclpy.ok():
            self.publisher.publish(Twist())
        if self.listener is not None:
            self.listener.stop()
            self.listener.join(1.0)
        self.destroy_node()


def main(args=None):
    # Keep the ROS context alive long enough to send stop commands on signals.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = None
    old_handlers = {}
    try:
        node = KeyboardControl()
        for signum in (signal.SIGINT, signal.SIGTERM):
            old_handlers[signum] = signal.signal(signum, lambda sig, frame: node.request_stop(f"Signal {sig}"))
        while rclpy.ok() and not node.shutdown_requested:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.close()
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
