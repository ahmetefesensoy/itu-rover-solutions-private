cmake_minimum_required(VERSION 3.8)
project(iturover_processing_assignment)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
install(PROGRAMS
  src/filter_publisher.py
  src/image_processor.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  rosbag
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
