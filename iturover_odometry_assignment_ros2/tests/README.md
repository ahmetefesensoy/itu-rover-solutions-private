# Çözüm testleri

9 Kasım 2026 son kontrolü: 27 test; 23.483 bag mesajı. Teker hızı + normalize IMU yönü; gerçek ROS2 çıktısı dörtgen rota üretir. assignment_q14 kayıt varsayımı açıktır; fiziksel doğruluk ölçülmemiştir.

Depo kökünden:

```bash
python3 -m unittest discover -s tests -v
```

Testler çözüme ait algoritmayı gerçek girdiler ve beklenen sonuçlarla karşılaştırır. ROS/Gazebo çalışma ölçümleri [results.json](results.json) içindedir. Bunlar sınanan senaryoların sonuçlarıdır; bütün olası çalışma koşulları için garanti değildir.
