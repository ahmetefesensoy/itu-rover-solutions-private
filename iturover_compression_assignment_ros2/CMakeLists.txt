cmake_minimum_required(VERSION 3.8)
project(iturover_compression_assignment)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/bz2_publisher.py
  scripts/bz2_solution.py
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES scripts/bz2_codec.py DESTINATION lib/${PROJECT_NAME})

ament_package()
