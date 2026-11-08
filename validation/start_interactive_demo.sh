#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
docker run --detach --name itu-rover-interactive --shm-size=512m \
  --volume /mnt/wslg/.X11-unix:/tmp/.X11-unix:ro \
  --volume "$ROOT:/task:ro" \
  --env DISPLAY=:0 --env QT_X11_NO_MITSHM=1 --env LIBGL_ALWAYS_SOFTWARE=1 \
  itu-rover-humble-ready:local bash /task/validation/run_interactive_demo.sh
