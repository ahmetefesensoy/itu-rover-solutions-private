# Robotun göründüğü klavye kaydı — 9 Kasım 2026

Eski video robotu göstermiyordu. Kayıt yenilendi; gövde ve iki teker yakın
planda görünür. 3., 6. ve 10. saniye kareleri ayrıca görsel olarak incelendi.

İki neden düzeltildi:

- Gazebo, `model://turtlebot3_description/...` gövde ve teker dosyalarını
  çözemiyordu. Paket üst dizini `GAZEBO_MODEL_PATH`'e eklendi. Bu düzeltme
  normal simülasyon launch dosyasına da uygulandı.
- İlk kamera açısı koridor duvarının arkasında kalıyordu. Yalnız çizim
  tarafında çalışan istemci eklentisi, gerçek robot görselini yüksek açıdan
  ve yakın mesafeden takip ediyor. Robotun fiziksel pozuna yazmıyor.

Kayıt gerçek Gazebo Classic viewport'udur. Son videoda yalnız model ağacı ve
araç çubukları kırpılmış, tuş ve ölçülen hız etiketleri eklenmiştir. Robot
görüntüsü, rota veya hareket sonradan üretilmemiştir.

Bu turda W, A, S ve Escape olayları X11/XTEST üzerinden gönderildi;
gerçek pynput dinleyicisi olayları okudu, çözüm node'u `/cmd_vel` yayınladı.
İleri, ileri+sol, tuş bırakınca duruş, geri ve Escape ile duruş doğrulandı.
Bu kısa gösterim yaklaşık 14 saniyedir. Gerçek 60 saniye sonu kapanışı ve
SIGINT/SIGTERM için önceki ayrı zaman testlerinin ölçümleri korunur.

- [Yeni video](../iturover_keyboard_control_assignment_ros2/media/solution/solution_demo.mp4)
- [Ham viewport](../iturover_keyboard_control_assignment_ros2/media/solution/gazebo_viewport.mp4)
- [6. saniye](../iturover_keyboard_control_assignment_ros2/media/solution/visible_robot_6s.jpg)
- [Ölçüm ve görsel kontrol](keyboard_video_results.json)
- [Kamera eklentisinin kaynağı](robot_recording_camera.cc)

Eksik dekoratif mesh görselleri kayıt dünyasında gizlidir; orijinal çarpışma
geometrisi, robot kontrolü ve hız parametreleri korunmuştur.
