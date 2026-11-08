"""Run: python3 -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import cv2
import numpy as np
from image_processor import process_frame

class TestImage(unittest.TestCase):
    def png(self, frame):
        return cv2.imencode(".png", frame)[1].tobytes()

    def test_rgb_color_roundtrip(self):
        for color in ((0, 0, 255), (255, 0, 0), (0, 255, 0)):
            data, raw, encoding = process_frame(self.png(np.full((32, 32, 3), color, np.uint8)), "RGB")
            decoded = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            np.testing.assert_allclose(decoded[16, 16], color, atol=3)
            np.testing.assert_equal(raw[16, 16], color[::-1])
            self.assertEqual(encoding, "rgb8")

    def test_gray_luminance(self):
        _, frame, encoding = process_frame(self.png(np.full((16, 16, 3), (0, 0, 255), np.uint8)), "GRAY")
        self.assertEqual(frame.shape, (16, 16))
        self.assertAlmostEqual(int(frame[0, 0]), 76, delta=1)
        self.assertEqual(encoding, "mono8")

    def test_resize_up(self):
        _, frame, _ = process_frame(self.png(np.zeros((7, 9, 3), np.uint8)), "RESIZE_UP")
        self.assertEqual(frame.shape, (14, 18, 3))

    def test_resize_down_odd_dimensions(self):
        _, frame, _ = process_frame(self.png(np.zeros((7, 9, 3), np.uint8)), "RESIZE_DOWN")
        self.assertEqual(frame.shape, (3, 4, 3))

    def test_single_pixel(self):
        _, frame, _ = process_frame(self.png(np.zeros((1, 1, 3), np.uint8)), "RESIZE_DOWN")
        self.assertEqual(frame.shape, (1, 1, 3))

    def test_empty_and_corrupt(self):
        for data in (b"", b"not an image", b"\xff\xd8"):
            with self.subTest(data=data), self.assertRaises((ValueError, cv2.error)):
                process_frame(data, "RGB")

    def test_pixel_limit(self):
        with self.assertRaises(ValueError):
            process_frame(self.png(np.zeros((10, 10, 3), np.uint8)), "RESIZE_UP", max_output_pixels=399)

    def test_unknown_filter(self):
        with self.assertRaises(ValueError):
            process_frame(b"", "INVALID")

if __name__ == "__main__":
    unittest.main(verbosity=2)
