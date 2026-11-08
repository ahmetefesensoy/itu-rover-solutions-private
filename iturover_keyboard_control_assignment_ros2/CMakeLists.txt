cmake_minimum_required(VERSION 3.8)
project(reactive_robot_sim)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/keyboard_control.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  config
  launch
  scripts
  models
  urdf
  worlds
  DESTINATION share/${PROJECT_NAME}
)

install(FILES scripts/control_state.py DESTINATION lib/${PROJECT_NAME})

ament_package()
