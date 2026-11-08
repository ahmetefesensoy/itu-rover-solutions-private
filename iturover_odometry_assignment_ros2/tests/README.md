# Çözüm testleri

8 Kasım 2026 son kontrolü: 19 test; 23.483 bag mesajı. Bağımsız hesapla son konum farkı 3,65 cm; gerçek konum doğruluğu ölçülmemiştir.

Depo kökünden:

```bash
python3 -m unittest discover -s tests -v
```

Testler çözüme ait algoritmayı gerçek girdiler ve beklenen sonuçlarla karşılaştırır. ROS/Gazebo çalışma ölçümleri [results.json](results.json) içindedir. Bunlar sınanan senaryoların sonuçlarıdır; bütün olası çalışma koşulları için garanti değildir.
