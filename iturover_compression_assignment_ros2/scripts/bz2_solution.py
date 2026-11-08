#!/usr/bin/env python3
"""Decode /bz2_message hex payloads and publish the most common byte."""

from bz2_codec import solve_hex

import rclpy
from rclpy.node import Node
from std_msgs.msg import Char, String


class Bz2Solution(Node):
    def __init__(self):
        super().__init__("bz2_solution")
        self.declare_parameter("max_compressed_bytes", 1048576)
        self.declare_parameter("max_decoded_bytes", 4194304)
        self.max_compressed_bytes = self.get_parameter("max_compressed_bytes").value
        self.max_decoded_bytes = self.get_parameter("max_decoded_bytes").value
        if min(self.max_compressed_bytes, self.max_decoded_bytes) <= 0:
            raise ValueError("BZ2 size limits must be positive")
        self.last_result = None
        self.publisher = self.create_publisher(Char, "/solution", 10)
        self.subscription = self.create_subscription(
            String, "/bz2_message", self.message_callback, 10
        )
        self.get_logger().info("Listening for hexadecimal BZ2 payloads on /bz2_message")

    def message_callback(self, message):
        try:
            most_common_byte, count = solve_hex(message.data, self.max_compressed_bytes, self.max_decoded_bytes)
        except (ValueError, OSError, EOFError) as error:
            self.get_logger().warning(f"Ignoring invalid BZ2 message: {error}", throttle_duration_sec=2.0)
            return
        result = Char()
        result.data = most_common_byte
        self.publisher.publish(result)
        if self.last_result != (most_common_byte, count):
            self.get_logger().info(f"Published byte {most_common_byte} ({chr(most_common_byte)!r}), occurring {count} times")
            self.last_result = (most_common_byte, count)


def main(args=None):
    rclpy.init(args=args)
    node = Bz2Solution()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
