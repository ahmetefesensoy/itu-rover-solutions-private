# Çözüm testleri

8 Kasım 2026 son kontrolü: 8 test; 12 bag karesinde 48 filtre çıktısı kontrolü. JPEG kayıplıdır.

Depo kökünden:

```bash
source /opt/ros/humble/setup.bash
python3 -m unittest discover -s tests -v
```

Testler çözüme ait algoritmayı gerçek girdiler ve beklenen sonuçlarla karşılaştırır. ROS/Gazebo çalışma ölçümleri [results.json](results.json) içindedir. Bunlar sınanan senaryoların sonuçlarıdır; bütün olası çalışma koşulları için garanti değildir.
