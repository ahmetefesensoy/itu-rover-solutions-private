"""Decode demo videos, extract previews and collect file-level playback checks."""
import json
from pathlib import Path
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
results = {}
previews = []
for repo in sorted(ROOT.glob("iturover*")):
    if not repo.is_dir():
        continue
    video = repo / "media/solution/solution_demo.mp4"
    assert video.is_file(), video
    capture = cv2.VideoCapture(str(video))
    assert capture.isOpened(), video
    fps = capture.get(cv2.CAP_PROP_FPS)
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    assert fps > 0 and count > 0
    images = []
    for fraction in (.2, .5, .8):
        capture.set(cv2.CAP_PROP_POS_FRAMES, round(count*fraction))
        ok, image = capture.read()
        assert ok and image.std() > 5, video
        images.append(image)
    capture.release()
    difference = float(np.mean(cv2.absdiff(images[0], images[-1])))
    if "keyboard" in repo.name:
        cv2.imwrite(str(ROOT/"validation/gazebo_video_frame.jpg"), images[1])
    assert difference > .05, (repo.name, "video contains no visible change")
    if "keyboard" in repo.name:
        cv2.imwrite(str(video.parent / "preview.jpg"), images[1])
    preview = cv2.resize(images[1], (640,360))
    cv2.rectangle(preview,(0,0),(640,28),(15,15,15),-1)
    cv2.putText(preview,repo.name,(8,20),cv2.FONT_HERSHEY_SIMPLEX,.43,(255,255,255),1,cv2.LINE_AA)
    previews.append(preview)
    results[repo.name] = {"file":str(video.relative_to(ROOT)),"duration_seconds":count/fps,"fps":fps,"frame_count":count,"width":images[0].shape[1],"height":images[0].shape[0],"sampled_frames_decode":True,"visible_change_mean":difference,"bytes":video.stat().st_size}
(ROOT/"validation/media_results.json").write_text(json.dumps(results,indent=2)+"\n")
previews.append(np.full((360,640,3),245,np.uint8))
collage=np.vstack([np.hstack(previews[i:i+2]) for i in (0,2,4)])
cv2.imwrite(str(ROOT/"validation/media_contact_sheet.jpg"),collage)
print(json.dumps(results,indent=2))
