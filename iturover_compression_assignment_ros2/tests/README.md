# Çözüm testleri

9 Kasım 2026 son kontrolü: 14 test; 200 sabit tohumlu rastgele payload ve bozuk/kesik/büyük veri kontrolleri.

Depo kökünden:

```bash
python3 -m unittest discover -s tests -v
```

Testler çözüme ait algoritmayı gerçek girdiler ve beklenen sonuçlarla karşılaştırır. ROS/Gazebo çalışma ölçümleri [results.json](results.json) içindedir. Bunlar sınanan senaryoların sonuçlarıdır; bütün olası çalışma koşulları için garanti değildir.
