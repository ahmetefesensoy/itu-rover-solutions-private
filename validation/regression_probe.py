"""Repeat the three checks originally captured in baseline_results.json."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import rclpy
from sensor_msgs.msg import CompressedImage

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    sys.path.insert(0, str((ROOT / path).parent))
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    image_module = load("baseline_image", "iturover_processing_assignment_ros2/src/image_processor.py")
    odom_module = load("baseline_odom", "iturover_odometry_assignment_ros2/src/odometry.py")
    rclpy.init()
    node = image_module.ImageProcessor()
    captured = []
    node.image_publisher = SimpleNamespace(publish=captured.append)
    findings = {}
    try:
        try:
            node.image_callback(CompressedImage())
            findings["empty_image_rejected_without_crash"] = True
        except cv2.error:
            findings["empty_image_rejected_without_crash"] = False
        red_bgr = np.full((16, 16, 3), (0, 0, 255), dtype=np.uint8)
        msg = CompressedImage(data=cv2.imencode(".png", red_bgr)[1].tobytes())
        node.current_filter = "RGB"
        node.image_callback(msg)
        decoded = cv2.imdecode(np.frombuffer(captured[-1].data, np.uint8), cv2.IMREAD_COLOR)
        findings["rgb_red_remains_red"] = bool(decoded[8, 8, 2] > 240 and decoded[8, 8, 0] < 15)
        findings["incomplete_rpm_pair_rejected"] = odom_module.RoverOdometry.average_pair([60.0]) is None
    finally:
        node.destroy_node()
        rclpy.shutdown()
    print(json.dumps(findings, indent=2))
    (ROOT / "validation/regression_results.json").write_text(json.dumps(findings, indent=2) + "\n")


if __name__ == "__main__":
    main()
