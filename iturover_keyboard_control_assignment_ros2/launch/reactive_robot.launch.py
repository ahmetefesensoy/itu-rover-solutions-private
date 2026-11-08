import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory("reactive_robot_sim")
    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(package_share, "launch", "reactive_robot_sim.launch.py")
        )
    )
    controller = Node(
        package="reactive_robot_sim",
        executable="keyboard_control.py",
        name="keyboard_control",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )
    return LaunchDescription([simulation, controller])
