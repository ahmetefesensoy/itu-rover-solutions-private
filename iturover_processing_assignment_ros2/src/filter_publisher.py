#!/usr/bin/env python3

# @author yerenkl
# Date: 05/09/2023 (ROS 2 version)

import random

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ItuRoverNode(Node):
    def __init__(self):
        super().__init__('itu_rover_node')

        # Create a publisher for the '/filter' topic
        self.filter_publisher = self.create_publisher(String, '/filter', 10)

        self.filters = ["GRAY", "RESIZE_UP", "RESIZE_DOWN", "RGB"]
        # 0.5 Hz -> every 2.0 seconds
        self.timer = self.create_timer(2.0, self.timer_callback)

    def timer_callback(self):
        random_filter = random.choice(self.filters)
        self.filters.remove(random_filter)

        self.get_logger().info(f"Publishing: {random_filter}")
        msg = String()
        msg.data = random_filter
        self.filter_publisher.publish(msg)

        if not self.filters:
            self.filters = ["GRAY", "RESIZE_UP", "RESIZE_DOWN", "RGB"]

def main(args=None):
    rclpy.init(args=args)
    node = ItuRoverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
