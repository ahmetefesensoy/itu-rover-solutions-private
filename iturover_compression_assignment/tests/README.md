# Çözüm testleri

8 Kasım 2026 son kontrolü: 14 test; 200 sabit tohumlu rastgele payload. Noetic üzerinde 5 geçerli ve 5 geçersiz girdi.

Depo kökünden:

```bash
python3 -m unittest discover -s tests -v
```

Testler çözüme ait algoritmayı gerçek girdiler ve beklenen sonuçlarla karşılaştırır. ROS/Gazebo çalışma ölçümleri [results.json](results.json) içindedir. Bunlar sınanan senaryoların sonuçlarıdır; bütün olası çalışma koşulları için garanti değildir.
