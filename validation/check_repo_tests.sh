#!/usr/bin/env bash
set -eo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source /opt/ros/jazzy/setup.bash
for repo in iturover_processing_assignment_ros2 iturover_odometry_assignment_ros2 iturover_keyboard_control_assignment_ros2 iturover_compression_assignment_ros2 iturover_compression_assignment; do
  python3 -m unittest discover -s "$repo/tests" -v > "validation/${repo}_tests.log" 2>&1
  tail -n 4 "validation/${repo}_tests.log"
done
