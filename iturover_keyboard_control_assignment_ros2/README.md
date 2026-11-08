# Klavye kontrolü

`pynput` ile okunan WASD tuşları TurtleBot'a `/cmd_vel` üzerinden hız komutu
gönderir. `w/s` ileri ve geri, `a/d` sola ve sağa dönüş içindir. Birlikte
basılan tuşlar birleşir; zıt yönler birbirini götürür. Tuş bırakıldığında
ilgili hız sıfırlanır. Hareket değişimleri terminale yazılır.

İlk sıfırdan farklı hız komutuyla 60 saniyelik süre başlar. Süre dolunca,
`Esc` basılınca veya kapanış sinyali gelince node 0.25 saniye sıfır hız
yayınlayıp kapanır. Süre monoton saatle ölçülür; simülasyonun duraklaması
süreyi uzatmaz.

## Kurulum

Ubuntu 22.04, ROS 2 Humble ve klavyeye erişebilen bir masaüstü oturumu gerekir.
Bu klasörü `~/rover_ws/src/` içine koyun:

```bash
source /opt/ros/humble/setup.bash
sudo apt install ros-humble-turtlebot3 ros-humble-turtlebot3-simulations ros-humble-gazebo-ros-pkgs python3-pynput
cd ~/rover_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select reactive_robot_sim
source install/setup.bash
```

## Çalıştırma

```bash
ros2 launch reactive_robot_sim reactive_robot.launch.py
```

Bu komut Gazebo Classic simülasyonunu ve klavye node'unu birlikte başlatır.
Robot görsellerinin bulunması için launch dosyası `turtlebot3_description`
paketinin üst dizinini `GAZEBO_MODEL_PATH`'e ekler.

Varsayılan hızlar `linear_speed=0.20` m/s ve `angular_speed=0.70` rad/s'dir.
Yalnız kontrol node'unu çalıştırmak için:

```bash
ros2 run reactive_robot_sim keyboard_control.py
```

## Test ve sonuç

Paket klasöründen:

```bash
python3 -m unittest discover -s tests -v
```

`tests/keyboard_live_check.py`, X11 üzerinde süre sonu ve sinyalle kapanış
davranışlarını sınar; derlenmiş workspace, Xvfb ve python-xlib gerektirir.

[Gazebo ekran kaydı](media/result.mp4)

[Ödev kaynağı](https://github.com/itu-rover/iturover_keyboard_control_assignment_ros2)
