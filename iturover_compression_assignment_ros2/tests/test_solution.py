"""Run: python3 -m unittest discover -s tests -v"""
import math
import random
import itertools
import bz2
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from bz2_codec import solve_hex

class CodecCases:
    def test_assignment_example(self):
        self.assertEqual(self.solve(bz2.compress(b"abcdddef").hex()), (100, 3))

    def test_publisher_example(self):
        self.assertEqual(self.solve(bz2.compress(b"somewhere, something incredible is waiting to be known.").hex()), (101, 7))

    def test_first_occurrence_wins_tie(self):
        self.assertEqual(self.solve(bz2.compress(b"baba").hex()), (98, 2))

    def test_all_byte_values(self):
        self.assertEqual(self.solve(bz2.compress(bytes(range(256)) + b"\xff\xff").hex()), (255, 3))

    def test_whitespace_hex(self):
        data = bz2.compress(b"aaa").hex()
        self.assertEqual(self.solve(" \n".join(data[i:i+2] for i in range(0, len(data), 2))), (97, 3))

    def test_bad_hex(self):
        for value in ("", "z1", "0", "hello"):
            with self.subTest(value=value), self.assertRaises((ValueError, OSError, EOFError)):
                self.solve(value)

    def test_empty_decoded(self):
        with self.assertRaises(ValueError):
            self.solve(bz2.compress(b"").hex())

    def test_truncation(self):
        payload = bz2.compress(b"abcdddef")
        for size in range(1, len(payload)):
            with self.subTest(size=size), self.assertRaises((ValueError, OSError, EOFError)):
                self.solve(payload[:size].hex())

    def test_trailing_garbage(self):
        with self.assertRaises((ValueError, OSError, EOFError)):
            self.solve((bz2.compress(b"aaa") + b"garbage").hex())

    def test_concatenated_streams(self):
        data = bz2.compress(b"aa") + bz2.compress(b"bbbb")
        self.assertEqual(self.solve(data.hex()), (98, 4))

    def test_output_limit_and_exact_boundary(self):
        data = bz2.compress(b"a" * 4097).hex()
        with self.assertRaises(ValueError):
            self.solve(data, max_decoded_bytes=4096)
        self.assertEqual(self.solve(data, max_decoded_bytes=4097), (97, 4097))

    def test_input_limit(self):
        with self.assertRaises(ValueError):
            self.solve(bz2.compress(b"abc").hex(), max_compressed_bytes=4)

    def test_multistream_combined_limit(self):
        with self.assertRaises(ValueError):
            self.solve((bz2.compress(b"aaa") * 3).hex(), max_decoded_bytes=8)

    def test_random_reference_200_payloads(self):
        rng = random.Random(20261108)
        for i in range(200):
            data = bytes(rng.randrange(256) for _ in range(rng.randint(1, 1500)))
            # Independent brute-force count, preserving first occurrence on ties.
            best = max(dict.fromkeys(data), key=data.count)
            with self.subTest(case=i):
                self.assertEqual(self.solve(bz2.compress(data).hex()), (best, data.count(best)))

class TestCompression(CodecCases, unittest.TestCase):
    solve = staticmethod(solve_hex)


if __name__ == "__main__":
    unittest.main(verbosity=2)
