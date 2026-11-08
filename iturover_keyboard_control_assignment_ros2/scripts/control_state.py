"""Deterministic WASD state machine; time is supplied by the caller."""
import math


class ControlState:
    def __init__(self, linear_speed=0.20, angular_speed=0.70, duration=60.0):
        if not all(math.isfinite(v) and v > 0 for v in (linear_speed, angular_speed, duration)):
            raise ValueError("speeds and duration must be finite and positive")
        self.linear_speed = linear_speed
        self.angular_speed = angular_speed
        self.duration = duration
        self.keys = set()
        self.started_at = None
        self.stopped_at = None
        self.reason = None

    def press(self, name):
        name = name.lower() if isinstance(name, str) else None
        if name == "esc":
            self.reason = "Escape pressed"
        elif name in {"w", "a", "s", "d"} and self.reason is None:
            self.keys.add(name)

    def release(self, name):
        if isinstance(name, str):
            self.keys.discard(name.lower())

    def stop(self, reason):
        if self.reason is None:
            self.reason = reason

    def command(self, now):
        if not math.isfinite(now):
            raise ValueError("invalid monotonic time")
        if self.started_at is not None and now - self.started_at >= self.duration:
            self.stop("Time limit reached")
        if self.reason is not None:
            self.keys.clear()
            if self.stopped_at is None:
                self.stopped_at = now
            return 0.0, 0.0
        linear = (int("w" in self.keys) - int("s" in self.keys)) * self.linear_speed
        angular = (int("a" in self.keys) - int("d" in self.keys)) * self.angular_speed
        # Opposing keys cancel: the run starts only with a nonzero command.
        if self.started_at is None and (linear != 0.0 or angular != 0.0):
            self.started_at = now
        return linear, angular

    def shutdown_ready(self, now):
        return self.stopped_at is not None and now - self.stopped_at >= 0.25
