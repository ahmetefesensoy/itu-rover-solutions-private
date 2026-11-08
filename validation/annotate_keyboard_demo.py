"""Combine actual Gazebo footage with the recorded controller/odometry result."""
import json
from pathlib import Path
import shutil
import sys
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from create_media import Movie, text, panel

ROOT = Path(__file__).resolve().parents[1]
target = ROOT/"iturover_keyboard_control_assignment_ros2/media/solution"
video = target/"solution_demo.mp4"
raw = target/"gazebo_viewport.mp4"
shutil.copy2(video, raw)
record = json.loads((target/"gazebo_telemetry.json").read_text())
samples = record["samples"]
start = next(s["time"] for s in samples if s["phase"] == "W: forward") - 2.0
times = np.array([s["time"]-start for s in samples])
positions = np.array([[s["x"],s["y"]] for s in samples])
origin = positions[np.searchsorted(times,0)]
positions -= origin
active = positions[times >= 0]
fig, ax = plt.subplots(figsize=(5.8,4.4), dpi=100)
ax.plot(active[:,0],active[:,1], color="#d2d8e0",lw=3,label="Complete measured route")
line, = ax.plot([],[],color="#1672cf",lw=2,label="Measured route so far")
point, = ax.plot([],[],"o",color="#ed841c",ms=9)
ax.set(xlabel="Relative x (m)",ylabel="Relative y (m)",title="Actual Gazebo /odom measurements")
ax.grid(alpha=.3)
ax.axis("equal")
ax.legend(fontsize=8)
fig.tight_layout()
capture=cv2.VideoCapture(str(raw))
fps=capture.get(cv2.CAP_PROP_FPS)
movie=Movie(video,fps=fps)
index=0
while True:
    ok,footage=capture.read()
    if not ok:
        break
    stamp=index/fps
    k=min(len(samples)-1,max(0,np.searchsorted(times,stamp,side="right")-1))
    selected=(times[:k+1]>=0)
    line.set_data(positions[:k+1][selected,0],positions[:k+1][selected,1])
    point.set_data([positions[k,0]],[positions[k,1]])
    fig.canvas.draw()
    graph=cv2.cvtColor(np.asarray(fig.canvas.buffer_rgba())[:,:,:3],cv2.COLOR_RGB2BGR)
    frame=np.full((720,1280,3),(27,22,18),np.uint8)
    text(frame,"ITU ROVER | OUR WASD CONTROLLER IN GAZEBO",(30,45),.93)
    text(frame,"Actual simulation capture + measured robot trajectory",(30,87),.7)
    panel(frame,footage,15,150,640,450)
    panel(frame,graph,670,150,580,450)
    text(frame,f"Input phase: {samples[k]['phase']}",(30,635),.78,(133,235,154))
    text(frame,f"Measured speed: {samples[k]['v']:+.3f} m/s | x={positions[k,0]:+.3f} m | y={positions[k,1]:+.3f} m",(30,675),.65)
    movie.write(frame)
    if index==int(fps*6):
        cv2.imwrite(str(target/"preview.jpg"),frame)
    index+=1
capture.release()
movie.close()
plt.close(fig)
(target/"README.md").write_text("""# Bizim klavye kontrolü sonucumuz

[solution_demo.mp4](solution_demo.mp4) solda gerçek Gazebo ekran kaydını,
sağda aynı çalıştırmanın gerçek `/odom` konum ölçümlerini gösterir. Alt satırda
o anda kontrol node'umuza verilen tuş olayı ve ölçülen hız bulunur.

Sıra: W ile ileri, W+A ile ileri/sol, tuşları bırakma, S ile geri ve duruş.
Olaylar kontrol node'umuza programla verilmiştir. Dünya `obs_corridor_world`,
robot TurtleBot3 Burger'dır. Kayıtta depoyla gelmeyen dekoratif mesh görselleri
gizlenmiştir; çarpışma geometrisi değiştirilmemiştir. Kamera sahneyi gösterir;
robotun konum değişimi sağdaki ölçüm panelinde izlenir.

[gazebo_viewport.mp4](gazebo_viewport.mp4) ham ekran kaydı,
[gazebo_telemetry.json](gazebo_telemetry.json) ölçümlerin kendisidir.
Gerçek zamanlı 60 saniye kuralının ayrı sonucu `tests/results.json` içindedir.

![Önizleme](preview.jpg)
""",encoding="utf-8")
print("Keyboard footage and measured trajectory combined")
