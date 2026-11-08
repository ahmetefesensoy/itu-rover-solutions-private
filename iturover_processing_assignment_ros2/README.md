<div align="center">
<img src="media/iturover.png" width="256" height="225" />
</div>

**ITU Rover Görüntü İşleme Görevi**

Bu görevde, ROS 2 kullanarak bir görüntü işleme node'u oluşturmanızı beklemekteyiz. Sizlere sunduğumuz `rosbag/assignment` dosyasında bulunan **/video_topic/compressed** topic'i üzerinden bir video yayını sağlanmıştır. Ayrıca başlatacağınız **'itu_rover_node'** her 2 saniyede bir bu yayına uygulanacak rastgele bir görüntü işleme tekniği **/filter** topic'i üzerinden yayınlanmaktadır.

Göreviniz, dinlediğiniz görüntü işleme tekniklerini video yayınına uygulamak ve sonucu **/rover_view/compressed** topic'i üzerinden yayınlamaktır.

# Kurulum

### Ubuntu Kurulumu
Eğer Ubuntu 22.04 işletim sistemi kurulu bir bilgisayarınız varsa bu adımı atlayabilirsiniz.
İTÜ Rover takımında ROS 2 Humble dağıtımı kullanılıyor. Bu nedenle beraber çalışabilmemiz için
Ubuntu 22.04 yüklü bir sisteminiz olması gerekmektedir.

### Linux Kullanımı

Aşağıdaki linkten temel Linux komutlarını öğrenip deneyebilirsiniz.

https://aktif.net/linux-komutlari/

### ROS 2 Humble Kurulumu
Aşağıdaki linkten öğrenerek Ubuntu’ya ROS 2 Humble kurulumunu tamamlayın.

https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html

### Paket Kurulumu

Bir workspace oluşturun ve bu paketi klonlayıp derleyin.

```bash
mkdir -p ~/rover_ws/src
cd ~/rover_ws/src
git clone https://github.com/itu-rover/iturover_processing_assignment_ros2.git
cd ~/rover_ws
colcon build
source install/setup.bash
```

# Görev Adımları
Aşağıda adımları sırasıyla bulabilirsiniz:

1. ROS 2 bag dosyasını başlatın:
   ```bash
   ros2 launch iturover_processing_assignment rosbag.launch.py
   ```

2. Görüntü işleme komutlarını içeren scripti çalıştırın:
   ```bash
   ros2 run iturover_processing_assignment filter_publisher.py
   ```

3. Başka bir terminalde görüntü işleme node'unu çalıştırın:
   ```bash
   ros2 run iturover_processing_assignment image_processor.py
   ```

4. **/video_topic/compressed** topic'ine gelen [sensor_msgs/msg/CompressedImage](https://docs.ros2.org/humble/api/sensor_msgs/msg/CompressedImage.html) mesaj türündeki video akışını ve **/filter** topic'ine gelen [std_msgs/msg/String](https://docs.ros2.org/humble/api/std_msgs/msg/String.html) komutlarını dinleyin.

5. Gelen görüntü işleme tekniklerini video akışına uygulayın.

   **GRAY**: Video akışını gri tonlamalı hale dönüştürür.

   **RGB**: Video akışını RGB tonlamalı hale dönüştürür.

   **RESIZE_UP**: Video akışının boyutunu iki katına çıkarır.

   **RESIZE_DOWN** :Video akışının boyutunu ikiye böler.

6. Elde edilen işlenmiş görüntüyü [sensor_msgs/msg/CompressedImage](https://docs.ros2.org/humble/api/sensor_msgs/msg/CompressedImage.html) mesaj türünde **/rover_view/compressed** topic'ine yayınlayın.

Bu adımları takip ederek görevinizi tamamlayabilirsiniz. Başarılar dileriz!


https://github.com/itu-rover/iturover_processing_assignment/assets/99661459/57722f7b-8e00-47a1-9cb1-2acb91781dcc



# Ayrıca bakınız
* https://docs.opencv.org/
* https://docs.ros.org/en/humble/p/cv_bridge/

## Çözümün davranışı ve önizleme

`RGB` filtresi renkleri korur: ham çıkış `rgb8`, JPEG kodlayıcısına verilen veri
BGR'dir. Böylece kırmızı ile mavi yer değiştirmez. `GRAY` tek kanallı,
`RESIZE_UP` iki kat, `RESIZE_DOWN` yarı boyut üretir; tek piksellik giriş
sıfır boyuta düşmez. JPEG kayıplı olduğu için piksel değerleri birebir korunmaz.

`/rover_view/compressed` yanında `/rover_view` üzerinde `sensor_msgs/Image`
önizlemesi de yayınlanır. İkisi de kaynak görüntünün zamanını ve frame_id'sini
korur. Önizleme:

```bash
ros2 run rqt_image_view rqt_image_view /rover_view
```

Boş/bozuk veya sınırları aşan görüntüler atlanır; node sonraki geçerli görüntüyü
işlemeye devam eder. Bilinmeyen filtre son geçerli filtreyi değiştirmez.
Girdi aboneliği sensör QoS kullanır; çıktılar reliable ve kuyruk derinliği 1'dir.
Başlangıç parametreleri: `jpeg_quality=90` (1–100),
`max_compressed_bytes=16777216`, `max_output_pixels=16777216`, `publish_raw=true`.
Piksel sınırı görüntü çözüldükten sonra kontrol edilir; decode belleği için
tam bir sınır değildir. Filtre ve görüntü bağımsız topic'lerdir; komutun
ulaşmasından önce gelen kare son uygulanmış filtreyle işlenir.

## Çözüm testleri

Bu depoyu bağımsız test etmek için [tests/README.md](tests/README.md) dosyasına bakın.
Ölçümler [tests/results.json](tests/results.json) içindedir.

## Bizim çözümümüzün görüntüsü

[Önizleme ve açıklama](media/solution/README.md) · [Çözüm videosu](media/solution/solution_demo.mp4)
