#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/noetic/setup.bash
mkdir -p /tmp/itu-noetic/src
ln -sfn /assignments/iturover_compression_assignment /tmp/itu-noetic/src/iturover_compression_assignment
cd /tmp/itu-noetic
catkin_make install -DCMAKE_INSTALL_PREFIX=/tmp/itu-noetic/install > /results/ros1_build.log 2>&1
source install/setup.bash
roscore > /results/roscore.log 2>&1 &
MASTER_PID=$!
trap 'kill "$MASTER_PID" 2>/dev/null || true' EXIT
python3 /assignments/validation/ros1_integration.py
