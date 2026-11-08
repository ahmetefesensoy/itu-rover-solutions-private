#!/usr/bin/env python3
"""Decode /bz2_message hex payloads and publish the most common byte (ROS 1)."""

from bz2_codec import solve_hex

import rospy
from std_msgs.msg import Char, String


class Bz2Solution:
    def __init__(self):
        rospy.init_node("bz2_solution", anonymous=False)
        self.max_compressed_bytes = rospy.get_param("~max_compressed_bytes", 1048576)
        self.max_decoded_bytes = rospy.get_param("~max_decoded_bytes", 4194304)
        if min(self.max_compressed_bytes, self.max_decoded_bytes) <= 0:
            raise ValueError("BZ2 size limits must be positive")
        self.last_result = None
        self.publisher = rospy.Publisher("/solution", Char, queue_size=10)
        self.subscription = rospy.Subscriber(
            "/bz2_message", String, self.message_callback, queue_size=10
        )
        rospy.loginfo("Listening for hexadecimal BZ2 payloads on /bz2_message")

    def message_callback(self, message):
        try:
            code, count = solve_hex(message.data, self.max_compressed_bytes, self.max_decoded_bytes)
        except (ValueError, OSError, EOFError) as error:
            rospy.logwarn_throttle(2.0, "Ignoring invalid BZ2 message: %s" % error)
            return
        result = Char()
        result.data = code
        self.publisher.publish(result)
        if self.last_result != (code, count):
            rospy.loginfo("Published byte %d (%r), occurring %d times", code, chr(code), count)
            self.last_result = (code, count)


if __name__ == "__main__":
    Bz2Solution()
    rospy.spin()
