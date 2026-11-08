"""Replay recorded sensor samples offline; compare to an independent integrator.

The reference is numerical consistency, not measured ground-truth position.
"""
import json
import math
import os
from pathlib import Path
import sqlite3
import statistics
import sys
import time

import cv2
import numpy as np
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "iturover_odometry_assignment_ros2/src"))
sys.path.insert(0, str(ROOT / "iturover_processing_assignment_ros2/src"))
from odometry_core import OdometryIntegrator
from image_processor import process_frame


def read_bag(path):
    with sqlite3.connect(str(path)) as conn:
        topics = {row[0]: (row[1], get_message(row[2])) for row in conn.execute("SELECT id, name, type FROM topics")}
        for topic_id, timestamp, data in conn.execute("SELECT topic_id, timestamp, data FROM messages ORDER BY timestamp, id"):
            name, msg_type = topics[topic_id]
            yield name, timestamp * 1e-9, deserialize_message(data, msg_type)


def replay(samples):
    core = OdometryIntegrator()
    next_tick = samples[0][1]
    path = []
    invalid = 0
    invalid_imu = 0
    for topic, stamp, msg in samples:
        while next_tick < stamp:
            state = core.step(next_tick)
            path.append((state.x, state.y))
            next_tick += .02
        if topic.endswith("left_motors_feedbacks"):
            valid = core.wheel("left", msg.data, stamp)
        elif topic.endswith("right_motors_feedbacks"):
            valid = core.wheel("right", msg.data, stamp)
        else:
            q = msg.orientation
            valid = core.imu((q.x, q.y, q.z, q.w), stamp, msg.orientation_covariance[0] != -1)
        if topic == "/imu1/data":
            invalid_imu += not valid
        else:
            invalid += not valid
    # Do not move backwards to the previous timer tick at the end of the bag.
    state = core.step(samples[-1][1])
    path.append((state.x, state.y))
    stopped = core.step(samples[-1][1] + 1)
    assert stopped.linear == 0 and stopped.x == state.x and stopped.y == state.y
    return core, path, invalid, invalid_imu


def reference(samples):
    # Event-time Euler integration, independent of the 50 Hz arc integrator.
    left = right = None
    yaw = 0.0
    last = samples[0][1]
    x = y = distance = 0.0
    path = []
    for topic, stamp, msg in samples:
        if left is not None and right is not None:
            speed = .135 * math.pi / 60 * (left + right)
            angular = .135 * 2 * math.pi / 60 * (right - left) / .890
            dt = stamp - last
            x += speed * math.cos(yaw) * dt
            y += speed * math.sin(yaw) * dt
            yaw += angular * dt
            distance += abs(speed) * dt
        last = stamp
        if topic.endswith("left_motors_feedbacks"):
            left = float(np.mean(msg.data))
        elif topic.endswith("right_motors_feedbacks"):
            right = float(np.mean(msg.data))
        path.append((x, y))
    return x, y, distance, path


def main():
    results_dir = Path(os.environ.get("ITU_RESULTS", str(ROOT / "validation")))
    bag = ROOT / "iturover_odometry_assignment_ros2/rosbag/scenario/scenario_0.db3"
    samples = list(read_bag(bag))
    core, path, invalid, invalid_imu = replay(samples)
    again, second_path, _, _ = replay(samples)
    assert path == second_path, "Replay is nondeterministic"
    rx, ry, distance, ref_path = reference(samples)
    error = math.hypot(core.x-rx, core.y-ry)
    assert all(math.isfinite(v) for point in path for v in point)
    assert invalid == 0, f"Unexpected invalid bag samples: {invalid}"
    assert error < max(.1, distance * .01), (error, distance)
    # Replay the beginning into the same core to prove it resets on rewind.
    core.observe_time(samples[0][1])
    assert core.reset_count == 1 and core.x == 0 and core.y == 0
    results = {"odometry": {"sensor_messages": len(samples), "duration_s": samples[-1][1]-samples[0][1],
                           "solution_final_xy_m": [again.x, again.y], "reference_final_xy_m": [rx, ry],
                           "reference_path_length_m": distance, "endpoint_difference_m": error,
                           "invalid_wheel_samples": invalid, "invalid_imu_samples_ignored_in_wheel_mode": invalid_imu,
                           "heading_source": "wheel", "wheel_separation_m": .890,
                           "replay_identical": True, "rewind_reset": True,
                           "note": "Numerical comparison only; no measured ground-truth trajectory provided."}}
    image_bag = ROOT / "iturover_processing_assignment_ros2/rosbag/assignment/assignment_0.db3"
    timings = {name: [] for name in ("GRAY", "RGB", "RESIZE_UP", "RESIZE_DOWN")}
    frames_checked = 0
    with sqlite3.connect(str(image_bag)) as conn:
        topic_id, msg_type = conn.execute("SELECT id, type FROM topics WHERE name='/video_topic/compressed'").fetchone()
        count = conn.execute("SELECT COUNT(*) FROM messages WHERE topic_id=?", (topic_id,)).fetchone()[0]
        for offset in np.linspace(0, count - 1, 12, dtype=int):
            data = conn.execute("SELECT data FROM messages WHERE topic_id=? ORDER BY timestamp LIMIT 1 OFFSET ?", (topic_id, int(offset))).fetchone()[0]
            msg = deserialize_message(data, get_message(msg_type))
            original = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
            h, w = original.shape[:2]
            for mode in timings:
                start = time.perf_counter()
                jpeg, raw, encoding = process_frame(msg.data, mode)
                timings[mode].append((time.perf_counter()-start)*1000)
                decoded = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
                shape = (2*h, 2*w) if mode == "RESIZE_UP" else (max(1,h//2), max(1,w//2)) if mode == "RESIZE_DOWN" else (h,w)
                assert raw.shape[:2] == decoded.shape[:2] == shape
                if mode == "RGB":
                    np.testing.assert_array_equal(raw, original[..., ::-1])
                if mode == "GRAY":
                    np.testing.assert_array_equal(raw, cv2.cvtColor(original, cv2.COLOR_BGR2GRAY))
                frames_checked += 1
    results["processing"] = {"frames_sampled": 12, "filter_outputs_checked": frames_checked,
                             "median_ms_per_filter": {key: statistics.median(value) for key, value in timings.items()}}
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "bag_results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(*zip(*ref_path), label="Event-time reference", color="gray", linewidth=3)
    ax.plot(*zip(*path), label="Solution (50 Hz)", color="#1177cc", linewidth=1)
    ax.set(xlabel="x (m)", ylabel="y (m)", title="Recorded odometry: numerical consistency")
    ax.axis("equal")
    ax.grid(alpha=.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(results_dir / "trajectory.png", dpi=160)


if __name__ == "__main__":
    main()
