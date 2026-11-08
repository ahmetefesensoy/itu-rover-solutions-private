"""Check the installed Noetic solution over real rospy topics."""
import bz2
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import rospy
from std_msgs.msg import Char, String


def wait(predicate, timeout=6):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not predicate():
        time.sleep(.02)
    assert predicate(), "Timed out waiting for ROS 1 communication"


def main():
    rospy.init_node("noetic_assignment_validation", anonymous=True)
    received = []
    sub = rospy.Subscriber("/solution", Char, lambda m: received.append(m.data), queue_size=20)
    pub = rospy.Publisher("/bz2_message", String, queue_size=10)
    with open("/results/ros1_solution.log", "w") as log:
        proc = subprocess.Popen(["rosrun", "iturover_compression_assignment", "bz2_solution.py", "_max_decoded_bytes:=1024"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            wait(lambda: pub.get_num_connections() > 0 and sub.get_num_connections() > 0)
            # Registration can precede completion of the TCPROS handshake.
            time.sleep(.5)
            for data, expected in ((b"abcdddef", 100), (b"baba", 98), (b"\xff\xffa", 255), (b"somewhere, something incredible is waiting to be known.", 101)):
                before = len(received)
                pub.publish(String(data=bz2.compress(data).hex()))
                wait(lambda: len(received) > before)
                assert received[-1] == expected
            before = len(received)
            for data in ("", "NOT HEX", bz2.compress(b"").hex(), bz2.compress(b"a"*1025).hex(), bz2.compress(b"abc")[:-1].hex()):
                pub.publish(String(data=data))
                time.sleep(.1)
            assert len(received) == before
            pub.publish(String(data=bz2.compress(b"zzzz").hex()))
            wait(lambda: len(received) > before)
            assert received[-1] == 122
            result = {"valid_cases": 5, "invalid_cases_rejected": 5, "recovery": True, "ROS_DISTRO": "noetic"}
            Path("/results/ros1_results.json").write_text(json.dumps(result, indent=2) + "\n")
            print(json.dumps(result))
        finally:
            os.killpg(proc.pid, signal.SIGINT)
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            rospy.signal_shutdown("validation finished")


if __name__ == "__main__":
    main()
