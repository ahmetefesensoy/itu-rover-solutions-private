# İTÜ Rover çözümleri ve kendi çıktı videolarımız

Beş ödev ayrı klasörlerdedir. Her klasörde çözüm kodu, çalıştırma yönergesi,
bağımsız testler ve `media/solution` altında kendi sonuçlarımız bulunur.
Obstacle avoidance bu pakete dahil değildir.

**Videoları topluca izlemek için:** depoyu ZIP olarak indirip çıkarın ve
`SHOWCASE.html` dosyasını tarayıcıda açın. GitHub'dan da aşağıdaki video
bağlantılarıyla tek tek görüntüleyebilir veya indirebilirsiniz.

65 birim testi Jazzy ve Humble'da geçti. Bu bir test başarı oranıdır;
gerçek araç konumu için yüzde doğruluk ölçümü değildir. Odometry'nin 3,65 cm
farkı aynı girdilerle hesaplanan bağımsız sayısal referansa göredir.

## Görüntü işleme

4 filtre; 48 gerçek bag çıktısı kontrolü; 8/8 birim testi.

[![Görüntü işleme](iturover_processing_assignment_ros2/media/solution/preview.jpg)](iturover_processing_assignment_ros2/media/solution/solution_demo.mp4)

[Bizim videomuz](iturover_processing_assignment_ros2/media/solution/solution_demo.mp4) · [Kod ve kullanım](iturover_processing_assignment_ros2/README.md) · [Ölçümler](iturover_processing_assignment_ros2/tests/results.json)

## Odometry

23.483 mesaj; sayısal referansla 3,65 cm fark; 19/19 test.

[![Odometry](iturover_odometry_assignment_ros2/media/solution/preview.png)](iturover_odometry_assignment_ros2/media/solution/solution_demo.mp4)

[Bizim videomuz](iturover_odometry_assignment_ros2/media/solution/solution_demo.mp4) · [Kod ve kullanım](iturover_odometry_assignment_ros2/README.md) · [Ölçümler](iturover_odometry_assignment_ros2/tests/results.json)

## Klavye / Gazebo

Gazebo hareketi; gerçek X11 testinde 60,05 s duruş; 10/10 test.

[![Klavye / Gazebo](iturover_keyboard_control_assignment_ros2/media/solution/preview.jpg)](iturover_keyboard_control_assignment_ros2/media/solution/solution_demo.mp4)

[Bizim videomuz](iturover_keyboard_control_assignment_ros2/media/solution/solution_demo.mp4) · [Kod ve kullanım](iturover_keyboard_control_assignment_ros2/README.md) · [Ölçümler](iturover_keyboard_control_assignment_ros2/tests/results.json)

## Compression ROS 2

14/14 test; gerçek DDS'de geçerli/geçersiz girdiler.

[![Compression ROS 2](iturover_compression_assignment_ros2/media/solution/preview.jpg)](iturover_compression_assignment_ros2/media/solution/solution_demo.mp4)

[Bizim videomuz](iturover_compression_assignment_ros2/media/solution/solution_demo.mp4) · [Kod ve kullanım](iturover_compression_assignment_ros2/README.md) · [Ölçümler](iturover_compression_assignment_ros2/tests/results.json)

## Compression ROS 1

14/14 test; kurulu Noetic paketinde 10 mesaj senaryosu.

[![Compression ROS 1](iturover_compression_assignment/media/solution/preview.jpg)](iturover_compression_assignment/media/solution/solution_demo.mp4)

[Bizim videomuz](iturover_compression_assignment/media/solution/solution_demo.mp4) · [Kod ve kullanım](iturover_compression_assignment/README.md) · [Ölçümler](iturover_compression_assignment/tests/results.json)


**9 Kasım odometry incelemesi:** Mevcut teker modeli örnek dörtgen rotayı üretmiyor. Aynı kayıtta normalize edilmiş IMU yönelimiyle yapılan tanısal hesap dörtgen çıkıyor; ancak kayıt bu yönelimi geçersiz işaretliyor. [Karşılaştırma ve kapsam](validation/ODOMETRY_REVIEW.md). Önceki 3,65 cm sayısal uyum, gerçek rota doğruluğu değildir.

## Çalıştırma ve doğrulama

[Ayrıntılı test raporu](validation/RESULTS.md) sınanan durumları, ölçümleri ve
tekrar çalıştırma komutlarını açıklar. Görüntü ve odometry videoları gerçek
bag verilerinden; compression videoları kendi Python çözüm fonksiyonlarının
sonuçlarından üretilmiştir. Klavye videosu Gazebo kaydıdır; tuş olayları
kontrol node'una programla verilmiştir.

## Erişim

Bu depo private'dır. WhatsApp'tan link göndermek erişim vermez; alıcının
GitHub hesabını Settings → Collaborators bölümünden davet etmek gerekir.
GitHub'da yalnız linki bilenlerin erişebildiği bir repo görünürlüğü yoktur.

## Kaynaklar

Ödev iskeletleri ve bag verileri [İTÜ Rover](https://github.com/itu-rover)
depolarından alınmıştır. Her alt klasörde orijinal README ve kaynak dosyaları
korunur. Önceki çözüm dalları İTÜ Rover depolarından kaldırılmıştır.
