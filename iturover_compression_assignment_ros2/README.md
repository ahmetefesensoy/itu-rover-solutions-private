# BZ2 sıkıştırma — ROS 2

`/bz2_message` üzerindeki hex biçimindeki `String` mesajı BZ2 ile açılır.
En sık geçen baytın sayısal değeri `/solution` üzerinde `std_msgs/msg/Char`
olarak yayınlanır. `abcdddef` için `d = 100`, verilen publisher metni
için `e = 101` elde edilir.

## Kurulum ve çalıştırma

Ubuntu 22.04 ve ROS 2 Humble içindir. Bu klasörü `~/rover_ws/src/` içine koyun.

```bash
source /opt/ros/humble/setup.bash
cd ~/rover_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select iturover_compression_assignment
source install/setup.bash
```

Her terminalde workspace ortamını kaynaklayıp şu komutları ayrı terminallerde çalıştırın:

```bash
ros2 run iturover_compression_assignment bz2_solution.py
ros2 run iturover_compression_assignment bz2_publisher.py
ros2 topic echo /solution
```

Eşitlikte metinde ilk görülen bayt seçilir (`baba` → 98). Boş, bozuk ve
kesilmiş veri atlanır. Birleştirilmiş BZ2 akışları desteklenir; sondaki çöp
veri reddedilir. Varsayılan sınırlar sıkıştırılmış veride 1 MiB, açılmış
veride 4 MiB'dir. `Char` tek bayt taşıdığı için Unicode karakter sayımı yapılmaz.

## Test ve sonuç

Paket klasöründen:

```bash
python3 -m unittest discover -s tests -v
```

[Sonuç videosu](media/result.mp4), Python çözüm fonksiyonunun örnek girdilerdeki
sonuçlarını gösterir. Canlı ROS çıktısı yukarıdaki komutlarla izlenebilir.

İki compression sürümü aynı paket adını kullanır; ayrı workspace'lerde derleyin.

[Ödev kaynağı](https://github.com/itu-rover/iturover_compression_assignment_ros2)
