# Görüntü işleme

ROS 2 node'u `/video_topic/compressed` görüntülerine `/filter` üzerinden gelen
`GRAY`, `RGB`, `RESIZE_UP` ve `RESIZE_DOWN` komutlarını uygular. İşlenmiş JPEG
`/rover_view/compressed`, ham önizleme `/rover_view` üzerinde yayınlanır.
Kaynak mesajın zamanı ve `frame_id` değeri korunur.

## Kurulum

Ubuntu 22.04 ve ROS 2 Humble gerekir. Bu klasörü `~/rover_ws/src/` içine koyun:

```bash
source /opt/ros/humble/setup.bash
cd ~/rover_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select iturover_processing_assignment
source install/setup.bash
```

## Çalıştırma

Her terminalde `~/rover_ws/install/setup.bash` dosyasını kaynaklayın.
Aşağıdaki komutları ayrı terminallerde çalıştırın:

```bash
ros2 launch iturover_processing_assignment rosbag.launch.py
ros2 run iturover_processing_assignment filter_publisher.py
ros2 run iturover_processing_assignment image_processor.py
ros2 run rqt_image_view rqt_image_view /rover_view
```

`GRAY` tek kanal, `RGB` renkli görüntü üretir. JPEG kodlamasında OpenCV'nin
BGR sırası kullanılır; ham RGB çıkışı `rgb8` biçimindedir. Büyütme iki kat,
küçültme yarı boyuttur; tek piksellik görüntü sıfır boyuta indirilmez.
Bozuk görüntü atlanır, bilinmeyen komutta son geçerli filtre korunur.

## Test ve sonuç

Paket klasöründen, ROS ortamı kaynaklandıktan sonra:

```bash
python3 -m unittest discover -s tests -v
```

[Sonuç videosu](media/result.mp4) bag görüntülerine uygulanan dört filtreyi gösterir.
`media/example.mp4` ödevin verilen örneğidir.

[Ödev kaynağı](https://github.com/itu-rover/iturover_processing_assignment_ros2)
