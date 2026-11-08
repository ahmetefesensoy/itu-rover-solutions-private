#!/usr/bin/env bash
set -euo pipefail
g++ -shared -fPIC -O2 /tmp/robot_recording_camera.cc \
    -o /tmp/librobot_recording_camera.so $(pkg-config --cflags --libs gazebo OGRE OGRE-Terrain OGRE-Paging)
