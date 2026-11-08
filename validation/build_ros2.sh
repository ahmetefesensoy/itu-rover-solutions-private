#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
set +u
source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash
set -u
colcon --log-base /tmp/itu-rover-validation/log build \
  --build-base /tmp/itu-rover-validation/build \
  --install-base /tmp/itu-rover-validation/install \
  --paths "$ROOT/iturover_processing_assignment_ros2" \
          "$ROOT/iturover_odometry_assignment_ros2" \
          "$ROOT/iturover_keyboard_control_assignment_ros2" \
          "$ROOT/iturover_compression_assignment_ros2"
