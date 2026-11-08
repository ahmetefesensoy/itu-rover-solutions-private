# Bizim klavye kontrolü sonucumuz

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
