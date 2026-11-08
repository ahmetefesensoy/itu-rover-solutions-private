"""Render review media from real assignment data and solution outputs."""
import bz2
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import CompressedImage
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "iturover_processing_assignment_ros2/src"))
from image_processor import process_frame
from bag_evaluation import read_bag, replay, reference


def media(repo):
    path = ROOT / repo / "media/solution"
    path.mkdir(parents=True, exist_ok=True)
    return path


class Movie:
    def __init__(self, path, fps=20, size=(1280, 720)):
        self.path = path
        self.fps = fps
        self.pipe = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pixel_format", "bgr24", "-video_size", f"{size[0]}x{size[1]}", "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)

    def write(self, frame):
        self.pipe.stdin.write(np.ascontiguousarray(frame).tobytes())

    def close(self):
        self.pipe.stdin.close()
        assert self.pipe.wait() == 0, self.path


def text(frame, content, position, size=.7, color=(225, 233, 242)):
    cv2.putText(frame, content, position, cv2.FONT_HERSHEY_SIMPLEX, size, color, 1, cv2.LINE_AA)


def panel(frame, image, x, y, w=600, h=460):
    factor = min(w / image.shape[1], h / image.shape[0])
    scaled = cv2.resize(image, (round(image.shape[1]*factor), round(image.shape[0]*factor)))
    xx, yy = x + (w-scaled.shape[1])//2, y + (h-scaled.shape[0])//2
    frame[yy:yy+scaled.shape[0], xx:xx+scaled.shape[1]] = scaled


def processing():
    target = media("iturover_processing_assignment_ros2")
    bag = ROOT / "iturover_processing_assignment_ros2/rosbag/assignment/assignment_0.db3"
    with sqlite3.connect(str(bag)) as conn:
        topic = conn.execute("SELECT id FROM topics WHERE name='/video_topic/compressed'").fetchone()[0]
        rows = conn.execute("SELECT data FROM messages WHERE topic_id=? ORDER BY timestamp LIMIT 360", (topic,)).fetchall()
    movie = Movie(target / "solution_demo.mp4")
    covers = []
    for i, (data,) in enumerate(rows):
        msg = deserialize_message(data, CompressedImage)
        original = cv2.imdecode(np.frombuffer(msg.data, np.uint8), cv2.IMREAD_COLOR)
        mode = ("GRAY", "RGB", "RESIZE_UP", "RESIZE_DOWN")[min(3, i*4//len(rows))]
        jpeg, raw, encoding = process_frame(msg.data, mode)
        output = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
        frame = np.full((720, 1280, 3), (27, 22, 18), np.uint8)
        text(frame, "ITU ROVER | OUR PROCESSING SOLUTION", (32, 43), .95)
        text(frame, f"Filter: {mode}   |   actual bag frame {i+1}", (32, 82))
        text(frame, f"Input: {original.shape[1]} x {original.shape[0]}", (35, 126))
        text(frame, f"Output: {output.shape[1]} x {output.shape[0]} | {encoding}", (660, 126))
        panel(frame, original, 25, 145)
        panel(frame, output, 655, 145)
        text(frame, "Original recorded video", (35, 635))
        text(frame, "JPEG from our image_processor.py", (660, 635))
        text(frame, "Panels fit to the same display area; actual pixel dimensions are shown above.", (35, 682), .58)
        movie.write(frame)
        if i % max(1, len(rows)//4) == len(rows)//8:
            covers.append(frame.copy())
    movie.close()
    cv2.imwrite(str(target / "preview.jpg"), covers[0])
    if len(covers) == 4:
        contact = np.vstack([np.hstack([cv2.resize(covers[j], (640,360)), cv2.resize(covers[j+1], (640,360))]) for j in (0,2)])
        cv2.imwrite(str(target / "all_filters.jpg"), contact)
    (target / "README.md").write_text("# Bizim görüntü işleme sonucumuz\n\n[solution_demo.mp4](solution_demo.mp4) verilen bag'deki 360 gerçek kare üzerinde çözümün dört filtresini gösterir. Solda orijinal, sağda çözüm JPEG çıktısı vardır. Panel boyutları görsel karşılaştırma için eşittir; gerçek piksel boyutları videoda yazılıdır.\n\n![Önizleme](preview.jpg)\n", encoding="utf-8")
    print("processing media complete", flush=True)


def odometry():
    target = media("iturover_odometry_assignment_ros2")
    samples = list(read_bag(ROOT / "iturover_odometry_assignment_ros2/rosbag/scenario/scenario_0.db3"))
    core, path, _, _ = replay(samples)
    rx, ry, distance, ref_path = reference(samples)
    path, ref_path = np.array(path), np.array(ref_path)
    fig, ax = plt.subplots(figsize=(12.8, 7.2), dpi=100)
    ax.plot(ref_path[:,0], ref_path[:,1], color="#bec7cf", lw=3, label="Independent numerical reference")
    route, = ax.plot([], [], color="#126ad4", lw=2, label="Our wheel odometry")
    dot, = ax.plot([], [], "o", color="#ee7920", ms=8)
    title = ax.set_title("Recorded wheel data | our solution replay")
    ax.set(xlabel="x (m)", ylabel="y (m)")
    ax.axis("equal")
    ax.grid(alpha=.25)
    ax.legend(loc="upper left")
    fig.text(.5, .02, f"23,483 sensor messages | numerical endpoint difference: {math.hypot(core.x-rx,core.y-ry):.4f} m | no measured ground truth", ha="center", fontsize=10)
    fig.tight_layout(rect=[0,.04,1,.98])
    movie = Movie(target / "solution_demo.mp4")
    for index in np.linspace(1, len(path), 320, dtype=int):
        route.set_data(path[:index,0], path[:index,1])
        dot.set_data([path[index-1,0]], [path[index-1,1]])
        title.set_text(f"Our odometry | recorded time {index/len(path)*191.3149:.1f} / 191.3 s | accelerated replay")
        fig.canvas.draw()
        rgb = np.asarray(fig.canvas.buffer_rgba())[:,:,:3]
        movie.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    movie.close()
    fig.savefig(target / "preview.png")
    plt.close(fig)
    (target / "README.md").write_text("# Bizim odometry sonucumuz\n\n[solution_demo.mp4](solution_demo.mp4) gerçek bag'deki sensörlerden hesaplanan rotanın hızlandırılmış çizimidir. Bu bir rota animasyonudur. Gri çizgi bağımsız sayısal referans, mavi çizgi çözümümüzdür. 3,65 cm son konum farkı sayısal tutarlılık ölçüsüdür; gerçek araç konum hatası değildir.\n\n![Rota](preview.png)\n", encoding="utf-8")
    print("odometry media complete", flush=True)


def compression(repo, label):
    target = media(repo)
    spec = importlib.util.spec_from_file_location(repo+"_codec", ROOT / repo / "scripts/bz2_codec.py")
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    cases = [b"somewhere, something incredible is waiting to be known.", b"abcdddef", b"baba", None]
    movie = Movie(target / "solution_demo.mp4")
    records = []
    for case, data in enumerate(cases):
        payload = bz2.compress(data).hex() if data is not None else "not_hex"
        try:
            code, count = codec.solve_hex(payload)
            result = f"/solution -> {code}  |  character: {chr(code)!r}  |  count: {count}"
            records.append({"text":data.decode(),"code":code,"count":count})
        except ValueError:
            result = "Invalid payload rejected | no /solution message"
            records.append({"invalid":"not_hex","rejected":True})
        frame = np.full((720,1280,3), (27,22,18), np.uint8)
        text(frame, f"ITU ROVER | OUR COMPRESSION SOLUTION | {label}", (35,55), .9)
        text(frame, "Actual output of our bz2_codec.py", (35,110))
        text(frame, "1. Hex input", (35,190), .85, (111,203,255))
        for line, start in enumerate(range(0,min(len(payload),180),90)):
            text(frame, payload[start:start+90], (35,235+line*30), .6)
        text(frame, "2. BZ2 decompression", (35,345), .85, (111,203,255))
        text(frame, repr(data.decode()) if data else "Rejected before decoding", (35,395), .65)
        text(frame, "3. Most frequent byte", (35,480), .85, (111,203,255))
        text(frame, result, (35,540), .85, (133,235,154))
        text(frame, "Ties: first occurrence wins. ROS topic transport is checked in tests/results.json.", (35,670), .6)
        if case == 0:
            cv2.imwrite(str(target / "preview.jpg"), frame)
        for _ in range(60):
            movie.write(frame)
    movie.close()
    (target / "demonstrated_cases.json").write_text(json.dumps(records, indent=2)+"\n")
    (target / "README.md").write_text(f"# Bizim compression sonucumuz ({label})\n\n[solution_demo.mp4](solution_demo.mp4) çözüm fonksiyonumuz gerçekten çalıştırılarak üretilmiştir. Örnek metin, ödevdeki abcdddef, eşitlik ve bozuk hex durumlarını gösterir. Bu video Python hesap sonucunu sunar; ROS topic doğrulaması tests/results.json dosyasındadır.\n\n![Çıktı](preview.jpg)\n", encoding="utf-8")
    print(repo+" media complete", flush=True)


if __name__ == "__main__":
    processing()
    odometry()
    compression("iturover_compression_assignment_ros2", "ROS 2")
    compression("iturover_compression_assignment", "ROS 1 Noetic")
