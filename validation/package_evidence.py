"""Ship scoped evidence with each solution so a clone includes its tests."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"
ros2 = json.loads((VALIDATION / "ros2_results.json").read_text())
humble = json.loads((VALIDATION / "humble/ros2_results.json").read_text())
bag = json.loads((VALIDATION / "bag_results.json").read_text())
cases = [
    ("iturover_processing_assignment_ros2", "processing_ros2", "8 test; 12 bag karesinde 48 filtre çıktısı kontrolü. JPEG kayıplıdır.", "processing"),
    ("iturover_odometry_assignment_ros2", "odometry_ros2", "27 test; 23.483 bag mesajı. Teker hızı + normalize IMU yönü; gerçek ROS2 çıktısı dörtgen rota üretir. assignment_q14 kayıt varsayımı açıktır; fiziksel doğruluk ölçülmemiştir.", "odometry"),
    ("iturover_keyboard_control_assignment_ros2", "keyboard_ros2", "10 test; 16 tuş birleşimi ve duruş/kapanış senaryoları. Gazebo Classic ile hareket ve duruş ölçümü.", None),
    ("iturover_compression_assignment_ros2", "compression_ros2", "14 test; 200 sabit tohumlu rastgele payload ve bozuk/kesik/büyük veri kontrolleri.", None),
    ("iturover_compression_assignment", None, "14 test; 200 sabit tohumlu rastgele payload. Noetic üzerinde 5 geçerli ve 5 geçersiz girdi.", None),
]
for repo, key, description, bag_key in cases:
    directory = ROOT / repo / "tests"
    evidence = {"date": "2026-11-09", "scope": description}
    if key:
        evidence.update(jazzy=ros2[key], humble=humble[key])
    else:
        evidence["noetic"] = json.loads((VALIDATION / "noetic/ros1_results.json").read_text())
    if bag_key:
        evidence["recorded_bag"] = bag[bag_key]
    if key=="odometry_ros2":
        evidence["q14_ros2_jazzy"]=ros2.get("odometry_imu_recording_ros2")
        evidence["q14_ros2_humble"]=humble.get("odometry_imu_recording_ros2")
        evidence["actual_ros2_bag"]=json.loads((VALIDATION/"odometry_live_results.json").read_text())
        if (VALIDATION/"humble/odometry_live_results.json").exists():
            evidence["actual_ros2_bag_humble"]=json.loads((VALIDATION/"humble/odometry_live_results.json").read_text())
    if key == "keyboard_ros2":
        evidence["gazebo"] = json.loads((VALIDATION / "gazebo_results.json").read_text())
        live = VALIDATION / "keyboard_live_results.json"
        if live.exists():
            evidence["real_time_x11"] = json.loads(live.read_text())
            shutil.copy2(VALIDATION / "keyboard_live_check.py", directory / "keyboard_live_check.py")
    (directory / "results.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
    (directory / "README.md").write_text(
        "# Çözüm testleri\n\n9 Kasım 2026 son kontrolü: " + description +
        "\n\nDepo kökünden:\n\n```bash\n" +
        ("source /opt/ros/humble/setup.bash\n" if key == "processing_ros2" else "") +
        "python3 -m unittest discover -s tests -v\n```\n\n" +
        "Testler çözüme ait algoritmayı gerçek girdiler ve beklenen sonuçlarla karşılaştırır. "
        "ROS/Gazebo çalışma ölçümleri [results.json](results.json) içindedir. "
        "Bunlar sınanan senaryoların sonuçlarıdır; bütün olası çalışma koşulları için garanti değildir.\n",
        encoding="utf-8")
    if key == "odometry_ros2":
        shutil.copy2(VALIDATION / "trajectory.png", directory / "trajectory.png")
