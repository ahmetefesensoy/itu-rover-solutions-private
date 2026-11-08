<div align="center">
<img src="media/iturover.png" width="256" height="225" />
</div>

# ITU Rover Odometry Assignment

Yukarıda gördüğünüz gezegen gezgini aracımızı Elektrik Elektronik Fakültesi'nde bir gezintiye çıkardık. Sizlere tahsis ettiğimiz **rosbag** dosyasında araç, gezintisini sürdürürken geri bildirim olarak aldığı teker hızı ve IMU verileri yer alıyor. Tekerleklerin yarıçapı ve hızları gibi bilgiler bilindiği için aracın başlangıç konumuna göre ne kadar ilerlediğini tahmin etmek mümkün.

<div align="center">
<img src="media/rolling.jpeg" width="400" height="250" />
</div>


Ödevle ilgili daha fazla bilgiye ve yardımcı olacak kaynaklara aşağıdan ulaşabilirsiniz.

# Kurulum

Bir workspace oluşturun ve bu paketi klonlayıp derleyin.

```bash
mkdir -p ~/rover_ws/src
cd ~/rover_ws/src
git clone https://github.com/itu-rover/iturover_odometry_assignment_ros2.git
cd ~/rover_ws
colcon build
source install/setup.bash
```

# Kullanım

ROS 2 bag dosyasını çalıştırın.

```bash
ros2 launch iturover_odometry_assignment rosbag.launch.py
```

Bu launch dosyası rosbag ile `odometry.py` node'unu başlatır. Bu kayıt için
ilerleme hızı dört tekerin RPM değerlerinden, yön normalize edilmiş IMU
quaternion'undan alınır. Teker yarıçapı 0.135 m'dir; `v=(vR+vL)/2` hesaplanır.
Yön ilk geçerli IMU ölçümüne göre sıfırlanır; konum dönüş yayı boyunca entegre
edilir. Node `/odom` ve `odom -> base_link` TF yayınlar. Zaman `/clock`'tan gelir.

Hızlandırılmış tekrar: `ros2 launch iturover_odometry_assignment rosbag.launch.py rate:=4.0`.
Varsayılan hız 1.0, başlangıç ofseti 0.0 saniyedir (`start_offset` ile değiştirilebilir).

Yalnızca odometri node'unu çalıştırmak için:

```bash
ros2 run iturover_odometry_assignment odometry.py
```

RViz2'de Fixed Frame alanını `odom` yapıp `/odom` için Odometry gösterimi ekleyin.
Sağ ve sol sensörlerden tam iki sonlu RPM değeri gerekir. Gerekli sensör verisi
0.5 saniyeden eskiyse konum sabit tutulur ve sıfır hız yayınlanır. Saat geri
sarıldığında konum ve sensör geçmişi sıfırlanır; bag tekrarı mesafeyi biriktirmez.

Bag'deki 21.571 IMU mesajı yaklaşık 16384 uzunluklu (Q14 ölçekli) quaternion
taşıyor; buna rağmen `orientation_covariance[0] == -1` yazılmış. Bu nedenle
yalnız bu kayıt için launch dosyası açıkça `orientation_policy=assignment_q14`
seçer. Bu uyumluluk modu, geçersiz işaretli mesajı ancak quaternion uzunluğu
16384 değerinin %1 yakınındaysa kabul eder ve normalize eder. Başlangıçta
uyarı logu yazılır. Sıfır, NaN, yanlış ölçek ve geçersiz işaretli birim quaternion
kabul edilmez. Bu bir kayıt uyumluluğu varsayımıdır; fiziksel konum doğrulaması değildir.

Node doğrudan çalıştırıldığında `heading_source=imu`, `orientation_policy=strict`
varsayılandır: ROS geçersizlik işareti korunur. Canlı sensörlerde strict kullanın.
Teker yönelim modeli `--ros-args -p heading_source:=wheel` ile seçilebilir;
bu bag'de 939° dönüş tahmin ederek örneğe uymayan bir rota ürettiği için
ödev launch'ında kullanılmaz. Kayıtlı IMU toplam dönüşü yaklaşık 361°'dir.

Başlangıç parametreleri: `wheel_radius=0.135`, `wheel_separation=0.890`,
`sensor_timeout=0.5`, `max_dt=0.5`, `heading_source=imu`, `orientation_policy=strict`,
`publish_tf=true`, `odom_frame=odom`,
`base_frame=base_link`. Kovaryans değerleri yaklaşık başlangıç değerleridir,
sensör kalibrasyonundan çıkarılmamıştır. Teker kayması ve etkin iz genişliği
gerçek araçta konum hatası oluşturabilir; bu bag gerçek konum referansı sağlamaz.

Tam bag'in gerçek ROS oynatımında dörtgen rota oluştu. Başlangıç-bitiş uzaklığı
yaklaşık 2.25 m'dir; bu fiziksel konum hatası olarak yorumlanmamalıdır. Sonuç
videosu gerçek `/odom` mesajlarının hızlandırılmış rota animasyonudur.

Yukarıdaki komutu yazdıktan sonra gezintimiz sırasında araçta gerçekleşen veri transferlerinin aynıları bilgisayarınızda da gerçekleşecektir.

Aşağıdaki komut ile rosbag'in doğru bir şekilde çalışıp çalışmadığını anlayabilirsiniz:

```bash
ros2 topic echo /drive_system_left_motors_feedbacks
```

## Rosbag içeriği
Rosbag aşağıdaki topiclerden mesajlar içermektedir:

**/drive_system_left_motors_feedbacks**

Bu topicte 2 elemanlı bir [std_msgs/msg/Float64MultiArray](https://docs.ros2.org/humble/api/std_msgs/msg/Float64MultiArray.html) türünde veri bulunmaktadır.
array'deki elemanlar sırasıyla sol ön ve sol arka tekerleğin dakikadaki dönüş sayılarıdır.

`Örneğin; [30, 40] verisi sol ön tekerleğin 30 RPM, sol arka tekerleğin 40 RPM hızda döndüğünü gösterir.`

**/drive_system_right_motors_feedbacks**

Bu topicte 2 elemanlı bir [std_msgs/msg/Float64MultiArray](https://docs.ros2.org/humble/api/std_msgs/msg/Float64MultiArray.html) türünde veri bulunmaktadır.
array'deki elemanlar sırasıyla sağ ön ve sağ arka tekerleğin dakikadaki dönüş sayılarıdır.

`Örneğin; [30, 40] verisi sağ ön tekerleğin 30 RPM, sağ arka tekerleğin 40 RPM hızda döndüğünü gösterir.`

**/imu1/data**

Bu topicte aracın üzerindeki imudan gelen [sensor_msgs/msg/Imu](https://docs.ros2.org/humble/api/sensor_msgs/msg/Imu.html) sensör verilerini bulabilirsiniz. Teker odometrisi için gerekli olmasa da dilerseniz bu veriyi de kullanabilirsiniz.

IMU verisindeki oryantasyon bilgisi quaternion olarak gelmektedir. (x,y,z,w) Oryantasyon bilgisini kullanabilmek için quaternion olan oryantasyon bilgisini euler (roll,pitch,yaw) şekline çevirmeniz gerekebilir.

**Bknz.**
* https://docs.ros.org/en/humble/Tutorials/Intermediate/Tf2/Quaternion-Fundamentals.html
* `tf_transformations` (`euler_from_quaternion`) veya `scipy.spatial.transform.Rotation`


# Gerekli bilgiler
Aşağıdaki ölçütlere ek olarak aracımızın teker yarıçapı 135mm'dir.


<div align="center">
<img src="media/rover.jpeg" width="536" height="577" />
</div>


# Ekran görüntüleri


Ödevi tamamladığınızda göreceğiniz görüntü aşağıdaki gibidir.

<div align="center">
<img src="media/groundtruth.jpeg" width="960" height="540" />
</div>

# Ayrıca bakınız

* https://www.cs.columbia.edu/~allen/F17/NOTES/icckinematics.pdf
* https://www.cs.cmu.edu/~16311/s07/labs/NXTLabs/Lab%203.html
* https://www.youtube.com/watch?v=aE7RQNhwnPQ
* https://www.youtube.com/watch?v=XbXhA4k7Ur8

## Çözüm testleri

Bu depoyu bağımsız test etmek için [tests/README.md](tests/README.md) dosyasına bakın.
Ölçümler [tests/results.json](tests/results.json) içindedir.

## Bizim çözümümüzün görüntüsü

[Önizleme ve açıklama](media/solution/README.md) · [Çözüm videosu](media/solution/solution_demo.mp4)
