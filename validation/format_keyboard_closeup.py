"""Crop actual Gazebo viewport and add measured phase labels; no rendered robot."""
import json
from pathlib import Path
import cv2
import numpy as np

from create_media import Movie, text

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/"iturover_keyboard_control_assignment_ros2/media/solution"
record=json.loads((TARGET/"gazebo_telemetry.json").read_text())
samples=record["samples"]
start=next(s["time"] for s in samples if s["phase"]=="W: forward")-2.0
times=np.array([s["time"]-start for s in samples])
capture=cv2.VideoCapture(str(TARGET/"gazebo_viewport.mp4"))
assert capture.isOpened()
fps=capture.get(cv2.CAP_PROP_FPS)
movie=Movie(TARGET/"solution_demo.mp4",fps=fps)
index=0
while True:
    ok,footage=capture.read()
    if not ok:break
    # Remove the model tree and toolbars; preserve the actual viewport pixels.
    viewport=footage[80:637,270:1260]
    frame=cv2.resize(viewport,(1280,720),interpolation=cv2.INTER_CUBIC)
    overlay=frame.copy()
    cv2.rectangle(overlay,(0,0),(1280,80),(13,20,29),-1)
    cv2.rectangle(overlay,(0,625),(1280,720),(13,20,29),-1)
    frame=cv2.addWeighted(frame,.2,overlay,.8,0)
    k=min(len(samples)-1,max(0,np.searchsorted(times,index/fps,side="right")-1))
    text(frame,"OUR KEYBOARD CONTROLLER | REAL GAZEBO RECORDING",(25,36),.88)
    text(frame,"Camera follows the existing TurtleBot3; actual X11 keys are read by pynput.",(25,66),.55)
    text(frame,f"{samples[k]['phase']}",(25,662),.92,(133,235,154))
    text(frame,f"Measured /odom speed: {samples[k]['v']:+.3f} m/s   |   x={samples[k]['x']:+.3f} m   y={samples[k]['y']:+.3f} m",(25,701),.65)
    movie.write(frame)
    if index in (int(fps*3),int(fps*6),int(fps*10)):
        cv2.imwrite(str(TARGET/f"visible_robot_{round(index/fps)}s.jpg"),frame)
    if index==int(fps*6):
        cv2.imwrite(str(TARGET/"preview.jpg"),frame)
    index+=1
capture.release();movie.close()
(TARGET/"README.md").write_text("""# Robotun göründüğü yeni klavye kontrolü kaydı

[solution_demo.mp4](solution_demo.mp4), gerçek Gazebo ekran kaydının yalnız
viewport'u kırpılıp tuş ve ölçülen hız etiketleri eklenmiş halidir. Robot
videoya sonradan çizilmemiştir. Kamera, gerçek TurtleBot3 görselinin simülasyondaki
konumunu takip eden yalnızca çizim tarafında çalışan bir istemci eklentisiyle
yakın planda tutulur. Bu eklenti fizik veya robot komutlarını değiştirmez.

X11/XTEST ile üretilen W, A ve S tuşlarını gerçek pynput dinleyicisi okur;
çözüm node'u /cmd_vel yayınlar. İleri, ileri+sol, tuş bırakınca duruş, geri ve
son duruş sırasıyla gösterilir. Video kısa gösterimdir; 60 saniye kuralının
ayrı gerçek zaman testi tests/results.json içindedir.

Ham kayıt: [gazebo_viewport.mp4](gazebo_viewport.mp4).
Ölçümler: [gazebo_telemetry.json](gazebo_telemetry.json).
Ödevin corridor dünyası ve TurtleBot3 Burger kullanılır. Eksik dekoratif
mesh görselleri gizlidir; çarpışma geometrisi korunur.

![Yakın plan robot](preview.jpg)
""",encoding="utf-8")
print(f"Formatted {index} actual Gazebo frames")
