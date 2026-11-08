<p align="center">
  <img src="https://github.com/itu-rover/iturover_obstacle_avoidance_assignment/assets/99661459/ac4adfa5-b237-4c0e-9f1e-56532de83b65" alt="iturover" width="300"/>
</p>
<p align="center">
</p>


# ITU Rover Keyboard Control Robot Assignment

Bu ödevde göreviniz python'da `pynput` kütüphanesini kullanarak klavyenizde basılan tuşları okuyan ve klavyenizdeki w,a,s,d tuşlarını kullanarak Turtlebot simülasyonunda robotu aktif bir şekilde hareket ettirmemizi sağlayan bir ROS 2 node'u yazmaktır.

<br>
<br>



<p align="center">
  <img src="https://github.com/itu-rover/iturover_obstacle_avoidance_assignment/assets/99661459/e3828def-fe18-4531-a2a4-796c0e6797b1" alt="harita" width="1200"/>
</p>
<p align="center">
  <em>Robotun hareketini gerçekleştireceği parkur</em>
</p>
<br>
<br>


https://github.com/user-attachments/assets/d7e383b6-136e-4b9b-8a4f-ac0c907ff49b




Ödevle ilgili daha fazla bilgiye ve yardımcı olacak kaynaklara aşağıdan ulaşabilirsiniz.

# Kurulum

Bir workspace oluşturun ve bu paketi klonlayıp derleyin.

```bash
mkdir -p ~/rover_ws/src
cd ~/rover_ws/src
git clone https://github.com/itu-rover/iturover_keyboard_control_assignment_ros2.git
cd ~/rover_ws
colcon build
source install/setup.bash
```

# Kullanım

Turtlebot simülasyonunu kullanmak için gerekli paketleri kurun:

```bash
sudo apt install ros-humble-turtlebot3 ros-humble-turtlebot3-simulations ros-humble-gazebo-ros-pkgs
```

Gazebo'yu çalıştırmak için aşağıdaki komutu terminal yardımıyla çalıştırın:

```bash
ros2 launch reactive_robot_sim reactive_robot.launch.py
```

Launch dosyası Gazebo simülasyonunu ve WASD klavye kontrol node'unu birlikte
başlatır. `w/s` ileri-geri, `a/d` yerinde dönüş komutları verir. Tuş bırakılınca
ilgili hız sıfırlanır; süre dolunca veya `Esc` basılınca node sıfır hız gönderip
kapanır. 60 saniyelik süre ilk hareket tuşuna basıldığında başlar. Klavye
dinleyicisi için Linux masaüstü oturumu gerekir.

Kontrol büyük/küçük harfi kabul eder. Aynı anda `w+a` ileri ve sola dönüş,
`w+s` sıfır ileri hız verir. Süre ilk sıfırdan farklı hız komutu yayınlandığında
başlar; tuş tekrarları süreyi uzatmaz. Her hız/yön değişimi ayrı loglanır.
Süre ROS saatinden bağımsız, monoton saatle ölçülür; simülasyon duraklatılsa
da 60 saniyelik sınır işler.

`Esc`, `Ctrl+C`, `SIGTERM`, süre bitişi veya klavye dinleyicisinin kapanması
kontrolü durdurur. Node kapanmadan önce 0.25 saniye boyunca sıfır hız yayınlar.
Başlangıç parametreleri `linear_speed=0.20`, `angular_speed=0.70`, `duration=60.0`.
`SIGKILL` veya ağ kesintisinde komut gönderilemez; gerçek araç kontrolcüsünde
ayrıca komut zaman aşımı bulunmalıdır. Simülasyonda denemeler için
`control_state.py` ROS ve masaüstünden bağımsız olarak sınanabilir.


## İsterler ve Kısıtlamalar
<br>
<br>




* Robot klavyenin tuşları ile aktif bir şekilde hareket ettirilebiliyor olmalıdır.
* Robot harekete geçtikten sonra 60 saniye hareket etmelidir.
* 60 saniyelik sürenin sonunda robot hareketini sonlandırmalı ve node kapanmalıdır.
* Robotun hareketindeki değişimler `self.get_logger().info(...)` yardımıyla terminalde gösterilmelidir. Örneğin: _Started rotating left._ Her değişim için yapmayı unutmayınız.
* Node ile ilgili bilgiler `self.get_logger().info(...)` yardımıyla terminalde gösterilmelidir. Örneğin: _Time limit reached. Stopping..._
* Script'iniz ve simülasyon ortamı aynı anda launch dosyası yardımıyla çalıştırılmalıdır.
* Launch dosyasının ismi `reactive_robot.launch.py` olmalıdır.
* Kodunuz yorum satırlarıyla açıklanmalıdır.


# Extra
<br>
<br>
Robotun üzerinde bir imu bulunmaktadır ve `/imu` topic'i üzerinden veri yayımlamaktadır. Arzu ettiğiniz takdirde bu veriyi kullanarak odometri yapıp odometri mesajı da yayımlayabilir ve bunu RViz2'de görüntüleyebilirsiniz.



https://github.com/user-attachments/assets/b80053f3-0768-4468-8743-4c6b3294c505




# Ayrıca bakınız

* https://docs.ros.org/en/humble/Tutorials.html
* https://docs.ros2.org/humble/api/geometry_msgs/msg/Twist.html
* https://docs.ros2.org/humble/api/nav_msgs/msg/Odometry.html

## Çözüm testleri

Bu depoyu bağımsız test etmek için [tests/README.md](tests/README.md) dosyasına bakın.
Ölçümler [tests/results.json](tests/results.json) içindedir.

## Bizim çözümümüzün görüntüsü

[Önizleme ve açıklama](media/solution/README.md) · [Çözüm videosu](media/solution/solution_demo.mp4)
