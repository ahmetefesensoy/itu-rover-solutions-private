cmake_minimum_required(VERSION 3.0.2)
project(iturover_compression_assignment)

find_package(catkin REQUIRED COMPONENTS rospy std_msgs)

catkin_package(CATKIN_DEPENDS rospy std_msgs)

catkin_install_python(PROGRAMS
  scripts/bz2_publisher.py
  scripts/bz2_solution.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# A Python helper must be beside both catkin's devel wrapper and installed node.
file(MAKE_DIRECTORY ${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_BIN_DESTINATION})
configure_file(scripts/bz2_codec.py ${CATKIN_DEVEL_PREFIX}/${CATKIN_PACKAGE_BIN_DESTINATION}/bz2_codec.py COPYONLY)
install(FILES scripts/bz2_codec.py DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
