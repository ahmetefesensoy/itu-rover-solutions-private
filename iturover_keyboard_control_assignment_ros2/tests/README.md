# Çözüm testleri

8 Kasım 2026 son kontrolü: 10 test; 16 tuş birleşimi ve duruş/kapanış senaryoları. Gazebo Classic ile hareket ve duruş ölçümü.

Depo kökünden:

```bash
python3 -m unittest discover -s tests -v
```

Testler çözüme ait algoritmayı gerçek girdiler ve beklenen sonuçlarla karşılaştırır. ROS/Gazebo çalışma ölçümleri [results.json](results.json) içindedir. Bunlar sınanan senaryoların sonuçlarıdır; bütün olası çalışma koşulları için garanti değildir.
