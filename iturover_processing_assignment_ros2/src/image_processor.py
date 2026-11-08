#!/usr/bin/env python3
"""Apply the current /filter command to /video_topic/compressed frames."""

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage, Image
from std_msgs.msg import String


FILTERS = {"GRAY", "RGB", "RESIZE_UP", "RESIZE_DOWN"}


def process_frame(data, command, jpeg_quality=90, max_output_pixels=16777216):
    """Return (JPEG bytes, raw pixels, ROS encoding), preserving visible colors.

    OpenCV's JPEG encoder accepts BGR. RGB output is converted back to BGR
    for encoding, while the optional raw preview really uses rgb8 pixels.
    """
    if command not in FILTERS:
        raise ValueError("unsupported filter")
    if not data:
        raise ValueError("empty compressed image")
    frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("undecodable compressed image")
    height, width = frame.shape[:2]
    target = (width * 2, height * 2) if command == "RESIZE_UP" else (width, height)
    if target[0] * target[1] > max_output_pixels:
        raise ValueError("image exceeds max_output_pixels")
    encoding = "bgr8"
    if command == "GRAY":
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        encoding = "mono8"
    elif command == "RGB":
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encoding = "rgb8"
    elif command == "RESIZE_UP":
        frame = cv2.resize(frame, target, interpolation=cv2.INTER_CUBIC)
    elif command == "RESIZE_DOWN":
        frame = cv2.resize(frame, (max(1, width // 2), max(1, height // 2)), interpolation=cv2.INTER_AREA)
    jpeg_input = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) if encoding == "rgb8" else frame
    success, output = cv2.imencode(".jpg", jpeg_input, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    if not success:
        raise ValueError("JPEG encoding failed")
    return output.tobytes(), frame, encoding


class ImageProcessor(Node):
    FILTERS = FILTERS

    def __init__(self):
        super().__init__("image_processor")
        self.current_filter = "GRAY"
        self.declare_parameter("jpeg_quality", 90)
        self.declare_parameter("max_compressed_bytes", 16777216)
        self.declare_parameter("max_output_pixels", 16777216)
        self.declare_parameter("publish_raw", True)
        self.jpeg_quality = self.get_parameter("jpeg_quality").value
        self.max_compressed_bytes = self.get_parameter("max_compressed_bytes").value
        self.max_output_pixels = self.get_parameter("max_output_pixels").value
        if not 1 <= self.jpeg_quality <= 100 or min(self.max_compressed_bytes, self.max_output_pixels) <= 0:
            raise ValueError("jpeg_quality must be 1..100 and image limits must be positive")
        self.filter_subscription = self.create_subscription(
            String, "/filter", self.filter_callback, 10
        )
        self.image_subscription = self.create_subscription(
            CompressedImage,
            "/video_topic/compressed",
            self.image_callback,
            qos_profile_sensor_data,
        )
        self.image_publisher = self.create_publisher(
            CompressedImage, "/rover_view/compressed", 1
        )
        # Reliable output works with both reliable and best-effort viewers.
        self.raw_publisher = self.create_publisher(Image, "/rover_view", 1) if self.get_parameter("publish_raw").value else None
        self.get_logger().info("Image processor ready; initial filter: GRAY")

    def filter_callback(self, message):
        command = message.data.strip().upper()
        if command not in self.FILTERS:
            self.get_logger().warning(f"Ignoring unsupported filter: {message.data[:80]!r}", throttle_duration_sec=2.0)
            return
        if command != self.current_filter:
            self.current_filter = command
            self.get_logger().info(f"Applying {command}")

    def image_callback(self, message):
        try:
            if len(message.data) > self.max_compressed_bytes:
                raise ValueError("compressed image exceeds max_compressed_bytes")
            output, frame, encoding = process_frame(
                message.data, self.current_filter, self.jpeg_quality, self.max_output_pixels
            )
        except (ValueError, cv2.error) as error:
            self.get_logger().warning(f"Ignoring invalid image: {error}", throttle_duration_sec=2.0)
            return

        result = CompressedImage()
        result.header = message.header
        result.format = "mono8; jpeg compressed" if encoding == "mono8" else f"{encoding}; jpeg compressed bgr8"
        result.data = output
        self.image_publisher.publish(result)
        if self.raw_publisher is not None:
            raw = Image()
            raw.header = message.header
            raw.height, raw.width = frame.shape[:2]
            raw.encoding = encoding
            raw.step = raw.width * (1 if encoding == "mono8" else 3)
            raw.data = frame.tobytes()
            self.raw_publisher.publish(raw)


def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessor()
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
