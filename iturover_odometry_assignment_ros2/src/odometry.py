#!/usr/bin/env python3
"""Publish wheel/IMU odometry, with stale-input stops and bag replay resets."""
import math

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu
from std_msgs.msg import Float64MultiArray
from tf2_ros import TransformBroadcaster

from odometry_core import OdometryIntegrator, average_pair


class RoverOdometry(Node):
    average_pair = staticmethod(average_pair)

    def __init__(self):
        super().__init__("rover_odometry")
        defaults = {"publish_tf": True, "odom_frame": "odom", "base_frame": "base_link",
                    "wheel_radius": 0.135, "sensor_timeout": 0.5, "max_dt": 0.5,
                    "wheel_separation": 0.890, "heading_source": "wheel"}
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        self.odom_frame = self.get_parameter("odom_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        if not self.odom_frame or not self.base_frame or self.odom_frame == self.base_frame:
            raise ValueError("odom_frame and base_frame must be nonempty and distinct")
        self.integrator = OdometryIntegrator(**{n: self.get_parameter(n).value for n in ("wheel_radius", "sensor_timeout", "max_dt", "wheel_separation", "heading_source")})
        self.create_subscription(Float64MultiArray, "/drive_system_left_motors_feedbacks", self.left_callback, qos_profile_sensor_data)
        self.create_subscription(Float64MultiArray, "/drive_system_right_motors_feedbacks", self.right_callback, qos_profile_sensor_data)
        self.create_subscription(Imu, "/imu1/data", self.imu_callback, qos_profile_sensor_data)
        self.odom_publisher = self.create_publisher(Odometry, "/odom", 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.last_fresh = None
        self.last_published_time = None
        self.timer = self.create_timer(0.02, self.update, clock=Clock(clock_type=ClockType.STEADY_TIME))
        self.get_logger().info(f"Odometry ready; heading={self.integrator.heading_source}, track={self.integrator.wheel_separation}m; stale inputs stop integration, clock rewinds reset pose.")

    def seconds(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def left_callback(self, message):
        self.integrator.wheel("left", message.data, self.seconds())

    def right_callback(self, message):
        self.integrator.wheel("right", message.data, self.seconds())

    def imu_callback(self, message):
        q = message.orientation
        self.integrator.imu((q.x, q.y, q.z, q.w), self.seconds(), message.orientation_covariance[0] != -1.0)

    def update(self):
        now = self.get_clock().now()
        seconds = now.nanoseconds * 1e-9
        if self.last_published_time == seconds:
            return  # Paused /clock: do not publish duplicate timestamps.
        self.last_published_time = seconds
        estimate = self.integrator.step(seconds)
        if estimate.fresh != self.last_fresh:
            self.get_logger().info("Sensor inputs ready." if estimate.fresh else "Waiting for fresh, valid required sensor inputs; holding position.")
            self.last_fresh = estimate.fresh
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = estimate.x
        odom.pose.pose.position.y = estimate.y
        odom.pose.pose.orientation.z = math.sin(estimate.yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(estimate.yaw / 2.0)
        odom.twist.twist.linear.x = estimate.linear
        odom.twist.twist.angular.z = estimate.angular
        # Conservative, uncalibrated estimates; unobserved axes are uncertain.
        for index, variance in zip((0, 7, 14, 21, 28, 35), (0.05, 0.05, 1e6, 1e6, 1e6, 0.02)):
            odom.pose.covariance[index] = variance
            odom.twist.covariance[index] = variance if estimate.fresh else max(variance, 1.0)
        self.odom_publisher.publish(odom)
        if self.get_parameter("publish_tf").value:
            transform = TransformStamped()
            transform.header = odom.header
            transform.child_frame_id = self.base_frame
            transform.transform.translation.x = estimate.x
            transform.transform.translation.y = estimate.y
            transform.transform.rotation = odom.pose.pose.orientation
            self.tf_broadcaster.sendTransform(transform)


def main(args=None):
    rclpy.init(args=args)
    node = RoverOdometry()
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
