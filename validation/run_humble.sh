#!/usr/bin/env bash
set -eo pipefail
cd /assignments
bash validation/build_ros2.sh > /results/build.log 2>&1
source /opt/ros/humble/setup.bash
source /tmp/itu-rover-validation/install/setup.bash
export ROS_DOMAIN_ID=83
export ITU_RESULTS=/results
python3 -m unittest discover -s validation -v > /results/unit_results.log 2>&1
python3 validation/ros2_integration.py
