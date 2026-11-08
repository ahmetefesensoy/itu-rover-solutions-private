#!/usr/bin/env bash
set -eo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash
source /tmp/itu-rover-validation/install/setup.bash
export ROS_DOMAIN_ID=83
python3 validation/ros2_integration.py
