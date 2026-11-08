cmake_minimum_required(VERSION 3.8)
project(iturover_odometry_assignment)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  src/odometry.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  rosbag
  DESTINATION share/${PROJECT_NAME}
)

install(FILES src/odometry_core.py DESTINATION lib/${PROJECT_NAME})

ament_package()
