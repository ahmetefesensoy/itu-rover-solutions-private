"""Planar wheel/IMU integration with sensor freshness and clock resets."""
import math
from dataclasses import dataclass


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def average_pair(values):
    if len(values) != 2 or not all(math.isfinite(v) for v in values):
        return None
    return values[0] / 2.0 + values[1] / 2.0


def quaternion_yaw(x, y, z, w):
    if not all(math.isfinite(v) for v in (x, y, z, w)):
        return None
    norm = math.hypot(x, y, z, w)
    if norm < 1e-12 or not math.isfinite(norm):
        return None
    x, y, z, w = (v / norm for v in (x, y, z, w))
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


@dataclass(frozen=True)
class Estimate:
    x: float
    y: float
    yaw: float
    linear: float
    angular: float
    fresh: bool


class OdometryIntegrator:
    def __init__(self, wheel_radius=0.135, sensor_timeout=0.5, max_dt=0.5, wheel_separation=0.890, heading_source="wheel"):
        if not all(math.isfinite(v) and v > 0 for v in (wheel_radius, sensor_timeout, max_dt, wheel_separation)):
            raise ValueError("odometry parameters must be finite and positive")
        if heading_source not in ("wheel", "imu"):
            raise ValueError("heading_source must be wheel or imu")
        self.wheel_radius = wheel_radius
        self.sensor_timeout = sensor_timeout
        self.max_dt = max_dt
        self.wheel_separation = wheel_separation
        self.heading_source = heading_source
        self.reset_count = 0
        self.reset()

    def reset(self):
        self.left = self.right = self.heading = None
        self.origin = None
        self.x = self.y = self.yaw = 0.0
        self.observed_time = self.last_step = None
        self.was_fresh = False

    def observe_time(self, now):
        if not math.isfinite(now):
            raise ValueError("invalid timestamp")
        if self.observed_time is not None and now < self.observed_time - 1e-6:
            # A restarted/looped bag represents a new run, not more distance.
            self.reset()
            self.reset_count += 1
        self.observed_time = now

    def wheel(self, side, values, now):
        # Integrate up to the receipt time with the PREVIOUS wheel speeds.
        # Applying a new speed to the preceding timer interval biases distance.
        if self.heading_source == "wheel":
            self.step(now)
        self.observe_time(now)
        rpm = average_pair(values)
        if side not in ("left", "right"):
            raise ValueError("unknown wheel side")
        setattr(self, side, None if rpm is None else (rpm, now))
        if self.heading_source == "wheel":
            # The interval starts when BOTH samples become available, rather
            # than one timer tick later. This also anchors recovery after gaps.
            self.was_fresh = all(s is not None and 0 <= now - s[1] <= self.sensor_timeout
                                 for s in (self.left, self.right))
        return rpm is not None

    def imu(self, quaternion, now, orientation_available=True):
        self.observe_time(now)
        yaw = quaternion_yaw(*quaternion) if orientation_available else None
        if yaw is None:
            self.heading = None
            return False
        if self.origin is None:
            self.origin = yaw
        self.heading = (wrap(yaw - self.origin), now)
        return True

    def step(self, now):
        self.observe_time(now)
        dt = 0.0 if self.last_step is None else now - self.last_step
        self.last_step = now
        samples = (self.left, self.right) if self.heading_source == "wheel" else (self.left, self.right, self.heading)
        fresh = all(s is not None and 0 <= now - s[1] <= self.sensor_timeout for s in samples)
        linear = angular = 0.0
        if fresh:
            left_speed = self.left[0] * (2.0 * math.pi / 60.0) * self.wheel_radius
            right_speed = self.right[0] * (2.0 * math.pi / 60.0) * self.wheel_radius
            linear = left_speed / 2.0 + right_speed / 2.0
            wheel_angular = (right_speed - left_speed) / self.wheel_separation
            if not all(math.isfinite(v) for v in (left_speed, right_speed, linear, wheel_angular)):
                self.was_fresh = False
                return Estimate(self.x, self.y, self.yaw, 0.0, 0.0, False)
            valid_interval = self.was_fresh and 0 < dt <= self.max_dt
            if self.heading_source == "wheel":
                angular = wheel_angular
                yaw = wrap(self.yaw + angular * dt) if valid_interval else self.yaw
            else:
                yaw = self.heading[0]
            if valid_interval:
                delta = angular * dt if self.heading_source == "wheel" else wrap(yaw - self.yaw)
                half = delta / 2.0
                # Exact arc displacement for constant speed and yaw rate.
                scale = math.sin(half) / half if abs(half) > 1e-9 else 1.0
                distance = linear * dt * scale
                self.x += distance * math.cos(self.yaw + half)
                self.y += distance * math.sin(self.yaw + half)
                angular = delta / dt
            self.yaw = yaw
        self.was_fresh = fresh
        return Estimate(self.x, self.y, self.yaw, linear, angular, fresh)
