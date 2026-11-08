#!/usr/bin/env bash
set -eo pipefail
cd /assignments
bash validation/build_ros2.sh > /results/build_bag.log 2>&1
source /opt/ros/humble/setup.bash
source /tmp/itu-rover-validation/install/setup.bash
export ROS_DOMAIN_ID=89
export ITU_RESULTS=/results
python3 validation/odometry_live_bag.py
