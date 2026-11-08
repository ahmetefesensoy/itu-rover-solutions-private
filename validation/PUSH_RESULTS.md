# GitHub paylaşımı — 8 Kasım 2026

Kullanıcının sonraki talebiyle aşağıdaki beş uzak çözüm dalı kaldırıldı.
Çözümler, testler ve kendi çıktı medyaları tek private depoda toplanmaktadır:
https://github.com/ahmetefesensoy/itu-rover-solutions-private

Aşağıdaki commit listesi önceki push işleminin yerel kaydıdır; bağlantılardaki
uzak dallar artık mevcut değildir.

Beş depoda `solutions/validated-2026-11-08` dalı pushlandı. GitHub API'den
okunan dal SHA değerleri yerel commit'lerle karşılaştırıldı ve eşleşti.

| Depo | Commit |
|---|---|
| [Processing](https://github.com/itu-rover/iturover_processing_assignment_ros2/tree/solutions/validated-2026-11-08) | `29d188bef278e50cde43e08ed271bf204c3fa6a0` |
| [Odometry](https://github.com/itu-rover/iturover_odometry_assignment_ros2/tree/solutions/validated-2026-11-08) | `e00bd16c3b827105287b06bfef0b5c5489306783` |
| [Keyboard](https://github.com/itu-rover/iturover_keyboard_control_assignment_ros2/tree/solutions/validated-2026-11-08) | `ac70abc7f22a6575e697df5f436f6a8d5db4e05e` |
| [Compression ROS 2](https://github.com/itu-rover/iturover_compression_assignment_ros2/tree/solutions/validated-2026-11-08) | `89d72dc0eaf1d95a37d36dac7489a27ced1ab454` |
| [Compression ROS 1](https://github.com/itu-rover/iturover_compression_assignment/tree/solutions/validated-2026-11-08) | `afd2103b4a93bc23466e301f78520f036f3be236` |

Her depoda çözüm, bağımsız testler, test sonuçları ve kullanım açıklamaları bulunur.
Main dalına merge yapılmadı. Klavye deposunda işlem öncesinden bulunan takip
edilmeyen `iturover_keyboard_control_assignment_ros2` bağlantısı commit'e eklenmedi.

Son doğrulama: Jazzy/Humble'da 65 birim testi; ROS 2 DDS entegrasyonu; Noetic
kurulum dizininden entegrasyon; gerçek bag; Gazebo Classic; gerçek X11 tuşları
ile 60 saniye, SIGINT ve SIGTERM denemeleri başarılı.
Ölçümler ve kapsam sınırları [RESULTS.md](RESULTS.md) dosyasındadır.
