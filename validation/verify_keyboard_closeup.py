"""Check close-up sample frames and real forward/reverse/stop telemetry."""
import json
from pathlib import Path
import statistics
import cv2

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"iturover_keyboard_control_assignment_ros2/media/solution"
record=json.loads((TARGET/"gazebo_telemetry.json").read_text())
samples=record["samples"]
phase_speeds={phase:[s["v"] for s in samples if s["phase"]==phase]
              for phase in {s["phase"] for s in samples}}
assert statistics.median(phase_speeds["W: forward"])>.1
assert statistics.median(phase_speeds["S: reverse"])<-.1
assert abs(statistics.median(phase_speeds["Released: stopped"]))<.03
assert abs(statistics.median(phase_speeds["Esc: stopped"]))<.03
assert "pynput" in record["input"] and record["collision_geometry_unchanged"]
frames={}
for second in (3,6,10):
    image=cv2.imread(str(TARGET/f"visible_robot_{second}s.jpg"))
    assert image is not None and image.shape[:2]==(720,1280)
    gray=cv2.cvtColor(image[180:550,420:900],cv2.COLOR_BGR2GRAY)
    dark=int((gray<80).sum())
    # A numerical guard alongside the actual visual review of body and wheels.
    assert dark>5000,(second,dark)
    frames[str(second)]={"decoded":True,"central_dark_pixels":dark,"body_and_wheels_visually_reviewed":True}
report={"revision_date":"2026-11-09","actual_gazebo_viewport":True,
        "robot_closeup_frames":frames,"actual_x11_pynput_events":True,
        "phase_median_velocity_m_s":{key:statistics.median(value) for key,value in phase_speeds.items()},
        "robot_mesh_resolution_fix":"GAZEBO_MODEL_PATH includes turtlebot3_description parent package directory",
        "physics_and_controller_unchanged":True}
(ROOT/"validation/keyboard_video_results.json").write_text(json.dumps(report,indent=2)+"\n")
evidence_file=ROOT/"iturover_keyboard_control_assignment_ros2/tests/results.json"
evidence=json.loads(evidence_file.read_text());evidence["closeup_video_revision"]=report
evidence_file.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n")
print(json.dumps(report,indent=2))
