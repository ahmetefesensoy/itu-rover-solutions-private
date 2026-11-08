# ITU Rover ödevleri: çalışma planı

Depodaki beş repo, ekrandaki sırayla ele alınacak. Obstacle Avoidance repo kapsam dışında.

1. [x] `iturover_processing_assignment_ros2`: görüntü filtresi node'u, senaryo çalıştırma yönergeleri ve filtre yayın döngüsü tamamlandı.
2. [x] `iturover_odometry_assignment_ros2`: teker odometrisi ve isteğe bağlı geçerli IMU modu, `/odom` ve `odom -> base_link` TF yayını.
3. [x] `iturover_keyboard_control_assignment_ros2`: WASD kontrolü, 60 saniye sınırı, durum logları ve birleşik launch dosyası eklendi.
4. [x] `iturover_compression_assignment_ros2`: BZ2 çözme ve ASCII kodunu `/solution`'a yayınlama node'u eklendi.
5. [x] `iturover_compression_assignment`: ROS 1 Noetic için catkin manifesti, BZ2 çözüm node'u ve çalıştırma yönergeleri eklendi.

Mevcut manifest, kaynak, launch ve README iskeletleri korunup gerekli dosyalar düzenlendi.

## İlk çalıştırma sonuçları (mesaj akışı kontrolleri)

- Görüntü işleme: ROS 2 Jazzy'de colcon derlemesi başarılı; bag oynatımı `/rover_view/compressed` üzerinde JPEG üretti, filtre publisher'ı `/filter` mesajları yayımladı.
- Odometri: ROS 2 Jazzy'de colcon derlemesi ve rosbag launch başarılı; `/odom` üzerinde pozisyon ve hız örneği alındı.
- Klavye kontrolü: ROS 2 Jazzy'de derlendi; W callback'i `/cmd_vel` üzerinde `linear.x=0.2` üretti. WSL'den yapay X11 klavye olayı `pynput`'a ulaşmadı; gerçek pencere tuş girdisiyle sonraki denemede callback loglandı.
- Compression ROS 2: ROS 2 Jazzy'de derleme ve uçtan uca publisher-subscriber denemesi başarılı; mevcut örnek metin için `/solution` değeri `101` (`e`).
- Klavye Gazebo Classic doğrulaması: Resmî ROS 2 Humble konteynerinde repo derlendi ve `reactive_robot_sim.launch.py gui:=false` başlatıldı. TurtleBot3 Burger spawn edildi, Gazebo eklentisi `/cmd_vel` dinledi ve `/odom` yayımladı. `/cmd_vel` ile hareket gönderildiğinde odometri konumu değişti.
- Ekrandaki simülasyon: WSLg üzerinden Gazebo Sim (Harmonic) diff-drive örneği açıldı; ROS-Gazebo köprüsüyle klavye node'u bağlandı. W tuş olayı node logunda görüldü, rover'a hız komutu gönderildi ve Gazebo odometrisinde yaklaşık 0.53 m ilerleme kaydedildi. Bu görünür demo repo'nun Classic corridor dünyası değil; repo'nun kendi Classic launch'ı Humble konteynerinde headless çalışıyor.
- Compression ROS 1: Noetic konteynerinde catkin derlemesi ve gerçek `roscore`/publisher/solution çalıştırması başarılı; publisher örneği için `/solution` `101` (`e`) verdi. İlk çalıştırmada publisher shebang'i `python` bulunamadığı için düzeltilip tekrar denendi. Çözüm callback'i ayrıca `abcdddef` girdisinde `100` (`d`) verdi.

İlk kontroller mesaj akışını doğruladı; sayısal doğruluk için aşağıdaki geliştirme
ve test çalışması yapıldı. Önceki IMU tabanlı varsayılan çözüm değiştirildi.

## 8 Kasım 2026 geliştirme ve doğrulama

- [x] RGB kanal sırası ve boş/bozuk görüntüde çökme düzeltildi; ham önizleme eklendi.
- [x] Bag'deki geçersiz IMU yönelimi saptandı. Çizimdeki 0.890 m iz genişliğiyle teker odometrisi varsayılan yapıldı.
- [x] Eski sensör verisiyle ilerleme, saat geri sarımı ve yeni hızın önceki aralığa uygulanması düzeltildi.
- [x] Klavyede yön değişimi logları, tuş birleşimleri, monoton süre ve kontrollü kapanış geliştirildi.
- [x] Her iki BZ2 çözümünde boyut sınırları, kesilmiş/bozuk mesaj kontrolü ve eşitlik kuralı eklendi.
- [x] 65 birim testi Jazzy ve Humble'da geçti; iki ROS 2 ortamında gerçek DDS denemeleri geçti.
- [x] ROS 1 Noetic'te catkin derleme ve 10 girdi senaryosu geçti.
- [x] Gerçek bag üzerinde 23.483 sensör mesajı ve 48 görüntü filtresi çıktısı kontrol edildi.
- [x] Gazebo Classic'te güncellenmiş kontrol node'u hareket, duruş ve kapanış testini geçti.

Ayrıntılı ölçümler, kapsam sınırları ve tekrar çalıştırma komutu:
[validation/RESULTS.md](validation/RESULTS.md).
