# Odometri

Sol ve sağ teker geri bildirimlerindeki ikişer RPM değerinden ilerleme hızı,
IMU quaternion'undan yön hesaplanır. Teker yarıçapı 0.135 m'dir:
`v = (v_left + v_right) / 2`, `v_side = mean(RPM) * 2π * 0.135 / 60`.
Başlangıç konumu ve yönü sıfır alınır. Node `/odom` mesajı ve
`odom -> base_link` dönüşümü yayınlar.

## Kurulum ve çalıştırma

Ubuntu 22.04 ve ROS 2 Humble gerekir. Bu klasörü `~/rover_ws/src/` içine koyun:

```bash
source /opt/ros/humble/setup.bash
cd ~/rover_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select iturover_odometry_assignment
source install/setup.bash
ros2 launch iturover_odometry_assignment rosbag.launch.py
```

Launch dosyası bag'i ve odometri node'unu birlikte başlatır; zaman `/clock`'tan
alınır. Hızlandırılmış oynatım için `rate:=4.0` eklenebilir. RViz2'de Fixed
Frame olarak `odom` seçip `/odom` için Odometry gösterimi ekleyin.

Girdiler `/drive_system_left_motors_feedbacks`,
`/drive_system_right_motors_feedbacks` (`Float64MultiArray`) ve `/imu1/data`
(`Imu`) topic'leridir. Gerekli sensör verisi 0.5 saniyeden eskiyse ilerleme
durdurulur. Bag saati geri sarıldığında konum ve sensör geçmişi sıfırlanır.

## Kayıttaki IMU biçimi

Verilen bag'deki quaternion uzunluğu yaklaşık 16384'tür (Q14 ölçeği), ancak
mesajlar yönelimi `orientation_covariance[0] = -1` ile geçersiz işaretler.
Bu kayıt için launch dosyası `orientation_policy=assignment_q14` seçer:
geçersiz işaretli quaternion yalnızca uzunluğu 16384'ün %1 yakınındaysa
kabul edilip normalize edilir. Node bu durumu başlangıçta uyarı olarak yazar.
Bu, kaydın biçimine ilişkin bir uyumluluk varsayımıdır.

Node tek başına çalıştırıldığında `orientation_policy=strict` varsayılandır
ve geçersiz yönelimler reddedilir:

```bash
ros2 run iturover_odometry_assignment odometry.py
```

Tekerlerden yön hesaplamak için `--ros-args -p heading_source:=wheel`
kullanılabilir. Bu modelin iz genişliği parametresi `wheel_separation=0.890` m'dir.
Verilen bag için launch dosyası IMU yönünü kullanır.

## Test ve sonuç

Paket klasöründen:

```bash
python3 -m unittest discover -s tests -v
```

[Sonuç videosu](media/result.mp4), tam bag oynatımında kaydedilen gerçek
`/odom` mesajlarının hızlandırılmış rota animasyonudur. Mavi çizgi node
çıktısı, gri çizgi aynı girdilerle bağımsız sayısal hesaptır. Başlangıç ve
bitiş arası yaklaşık 2.25 m'dir. Bag ölçülmüş konum referansı içermediğinden
bu mesafe fiziksel konum hatası veya yüzde doğruluk olarak yorumlanamaz.

[Ödev kaynağı](https://github.com/itu-rover/iturover_odometry_assignment_ros2)
