"""Collect five standalone solutions without nested Git history or build output."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "private_bundle"
DEST.mkdir(exist_ok=True)
SKIP = {".git", "__pycache__", "build", "install", "devel", "log", "private_bundle", "gazebo_video_frame.jpg"}
def ignore(directory, names):
    return [n for n in names if n in SKIP or (Path(directory)/n).is_symlink() or n.endswith((".pyc", ".pyo"))]

repos = [p for p in ROOT.glob("iturover*") if p.is_dir()]
for repo in repos:
    shutil.copytree(repo, DEST/repo.name, ignore=ignore, dirs_exist_ok=True)
shutil.copytree(ROOT/"validation", DEST/"validation", ignore=ignore, dirs_exist_ok=True)
for name in ("SHOWCASE.html", "PLAN.md"):
    shutil.copy2(ROOT/name, DEST/name)
(DEST/".gitignore").write_text("__pycache__/\n*.py[cod]\n/build/\n/install/\n/devel/\n/log/\n")
(DEST/".gitattributes").write_text("*.py text eol=lf\n*.sh text eol=lf\n*.mp4 binary\n*.db3 binary\n")
rows = [
    ("Görüntü işleme", "iturover_processing_assignment_ros2", "preview.jpg", "4 filtre; 48 gerçek bag çıktısı kontrolü; 8/8 birim testi"),
    ("Odometry", "iturover_odometry_assignment_ros2", "preview.png", "23.483 mesaj; sayısal referansla 3,65 cm fark; 19/19 test"),
    ("Klavye / Gazebo", "iturover_keyboard_control_assignment_ros2", "preview.jpg", "Gazebo hareketi; gerçek X11 testinde 60,05 s duruş; 10/10 test"),
    ("Compression ROS 2", "iturover_compression_assignment_ros2", "preview.jpg", "14/14 test; gerçek DDS'de geçerli/geçersiz girdiler"),
    ("Compression ROS 1", "iturover_compression_assignment", "preview.jpg", "14/14 test; kurulu Noetic paketinde 10 mesaj senaryosu"),
]
readme = """# İTÜ Rover çözümleri ve kendi çıktı videolarımız

Beş ödev ayrı klasörlerdedir. Her klasörde çözüm kodu, çalıştırma yönergesi,
bağımsız testler ve `media/solution` altında kendi sonuçlarımız bulunur.
Obstacle avoidance bu pakete dahil değildir.

**Videoları topluca izlemek için:** depoyu ZIP olarak indirip çıkarın ve
`SHOWCASE.html` dosyasını tarayıcıda açın. GitHub'dan da aşağıdaki video
bağlantılarıyla tek tek görüntüleyebilir veya indirebilirsiniz.

65 birim testi Jazzy ve Humble'da geçti. Bu bir test başarı oranıdır;
gerçek araç konumu için yüzde doğruluk ölçümü değildir. Odometry'nin 3,65 cm
farkı aynı girdilerle hesaplanan bağımsız sayısal referansa göredir.

"""
for title, repo, preview, metric in rows:
    readme += f"## {title}\n\n{metric}.\n\n[![{title}]({repo}/media/solution/{preview})]({repo}/media/solution/solution_demo.mp4)\n\n[Bizim videomuz]({repo}/media/solution/solution_demo.mp4) · [Kod ve kullanım]({repo}/README.md) · [Ölçümler]({repo}/tests/results.json)\n\n"
readme += """## Çalıştırma ve doğrulama

[Ayrıntılı test raporu](validation/RESULTS.md) sınanan durumları, ölçümleri ve
tekrar çalıştırma komutlarını açıklar. Görüntü ve odometry videoları gerçek
bag verilerinden; compression videoları kendi Python çözüm fonksiyonlarının
sonuçlarından üretilmiştir. Klavye videosu Gazebo kaydıdır; tuş olayları
kontrol node'una programla verilmiştir.

## Erişim

Bu depo private'dır. WhatsApp'tan link göndermek erişim vermez; alıcının
GitHub hesabını Settings → Collaborators bölümünden davet etmek gerekir.
GitHub'da yalnız linki bilenlerin erişebildiği bir repo görünürlüğü yoktur.

## Kaynaklar

Ödev iskeletleri ve bag verileri [İTÜ Rover](https://github.com/itu-rover)
depolarından alınmıştır. Her alt klasörde orijinal README ve kaynak dosyaları
korunur. Önceki çözüm dalları İTÜ Rover depolarından kaldırılmıştır.
"""
(DEST/"README.md").write_text(readme, encoding="utf-8")
print(DEST)
