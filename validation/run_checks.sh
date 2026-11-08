#!/usr/bin/env bash
set -eo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
bash validation/build_ros2.sh
source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash
source /tmp/itu-rover-validation/install/setup.bash
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-83}
python3 -m unittest discover -s validation -v 2>&1 | tee validation/unit_results.log
python3 validation/ros2_integration.py 2>&1 | tee validation/ros2_integration.log
python3 validation/bag_evaluation.py
python3 validation/regression_probe.py
