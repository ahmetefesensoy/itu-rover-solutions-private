"""Run: python3 -m unittest discover -s tests -v"""
import math
import itertools
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from control_state import ControlState

class TestKeyboard(unittest.TestCase):
    def test_all_16_combinations(self):
        for flags in itertools.product((False, True), repeat=4):
            state = ControlState()
            for key, pressed in zip("wasd", flags):
                if pressed:
                    state.press(key)
            w, a, s, d = flags
            self.assertEqual(state.command(0), ((w-s)*.2, (a-d)*.7))

    def test_uppercase_and_release(self):
        state = ControlState()
        state.press("W")
        self.assertEqual(state.command(0), (.2, 0))
        state.release("w")
        self.assertEqual(state.command(.1), (0, 0))

    def test_cancelled_keys_do_not_start_deadline(self):
        state = ControlState()
        state.press("w")
        state.press("s")
        state.command(100)
        self.assertIsNone(state.started_at)

    def test_exact_60_second_deadline(self):
        state = ControlState()
        state.press("w")
        state.command(100)
        self.assertEqual(state.command(159.999), (.2, 0))
        self.assertEqual(state.command(160), (0, 0))
        self.assertFalse(state.shutdown_ready(160.24))
        self.assertTrue(state.shutdown_ready(160.25))

    def test_idle_time_before_movement_not_counted(self):
        state = ControlState()
        state.command(1000)
        state.press("w")
        self.assertEqual(state.command(2000), (.2, 0))
        self.assertEqual(state.started_at, 2000)

    def test_repeated_keys_do_not_restart_deadline(self):
        state = ControlState()
        state.press("w")
        state.command(0)
        for t in range(1, 60):
            state.press("w")
            state.command(t)
        self.assertEqual(state.command(60), (0, 0))

    def test_escape_is_latched(self):
        state = ControlState()
        state.press("esc")
        state.press("w")
        self.assertEqual(state.command(0), (0, 0))

    def test_external_stop_is_latched(self):
        state = ControlState()
        state.press("w")
        state.command(0)
        state.stop("listener failure")
        self.assertEqual(state.command(.1), (0, 0))
        self.assertEqual(state.reason, "listener failure")

    def test_unknown_keys_ignored(self):
        state = ControlState()
        state.press(None)
        state.press("f")
        self.assertEqual(state.command(0), (0, 0))

    def test_invalid_parameters(self):
        for value in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                ControlState(duration=value)

if __name__ == "__main__":
    unittest.main(verbosity=2)
