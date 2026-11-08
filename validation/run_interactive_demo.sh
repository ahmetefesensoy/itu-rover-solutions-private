#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /usr/share/gazebo/setup.sh
source /workspace/install/setup.bash
export DISPLAY=:0
export ROS_DOMAIN_ID=90
export GAZEBO_MASTER_URI=http://127.0.0.1:11375
export GAZEBO_MODEL_DATABASE_URI=
export GAZEBO_MODEL_PATH=/opt/ros/humble/share:/workspace/install/reactive_robot_sim/share/reactive_robot_sim/models
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1

# Both the simulation and the real pynput controller start in the assignment
# launch. The GUI is started separately to avoid the deprecated EOL GUI plugin.
ros2 launch reactive_robot_sim reactive_robot.launch.py model:=burger gui:=false > /tmp/interactive_launch.log 2>&1 &
LAUNCH_PID=$!
GUI_PID=
cleanup() {
  kill -INT "$LAUNCH_PID" 2>/dev/null || true
  if [ -n "$GUI_PID" ]; then kill -TERM "$GUI_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT TERM INT
for attempt in $(seq 1 50); do
  if grep -q 'Successfully spawned entity' /tmp/interactive_launch.log; then break; fi
  if ! kill -0 "$LAUNCH_PID" 2>/dev/null; then cat /tmp/interactive_launch.log; exit 1; fi
  sleep .4
done
gzclient -g /tmp/librobot_recording_camera.so > /tmp/interactive_gui.log 2>&1 &
GUI_PID=$!
wait "$LAUNCH_PID"
