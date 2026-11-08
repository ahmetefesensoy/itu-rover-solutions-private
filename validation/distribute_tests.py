"""Copy the corresponding tests into each independently cloneable assignment."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / "validation/test_solutions.py").read_text()
tree = ast.parse(source)
classes = {n.name: ast.get_source_segment(source, n) for n in tree.body if isinstance(n, ast.ClassDef)}
common = '''"""Run: python3 -m unittest discover -s tests -v"""
import math
import random
import itertools
import bz2
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
'''
for repo, folder, imports, names in (
    ("iturover_processing_assignment_ros2", "src", "import cv2\nimport numpy as np\nfrom image_processor import process_frame", ["TestImage"]),
    ("iturover_odometry_assignment_ros2", "src", "from odometry_core import OdometryIntegrator, average_pair, quaternion_yaw", ["TestOdometry"]),
    ("iturover_keyboard_control_assignment_ros2", "scripts", "from control_state import ControlState", ["TestKeyboard"]),
    ("iturover_compression_assignment_ros2", "scripts", "from bz2_codec import solve_hex", ["CodecCases"]),
    ("iturover_compression_assignment", "scripts", "from bz2_codec import solve_hex", ["CodecCases"]),
):
    content = common + f'sys.path.insert(0, str(ROOT / "{folder}"))\n' + imports + "\n\n"
    content += "\n\n".join(classes[name] for name in names)
    if names == ["CodecCases"]:
        content += "\n\nclass TestCompression(CodecCases, unittest.TestCase):\n    solve = staticmethod(solve_hex)\n"
    content += '\n\nif __name__ == "__main__":\n    unittest.main(verbosity=2)\n'
    tests = ROOT / repo / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "test_solution.py").write_text(content)
    print(repo)
