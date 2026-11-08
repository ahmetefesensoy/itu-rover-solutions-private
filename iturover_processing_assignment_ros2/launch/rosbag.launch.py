import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description():
    pkg_share = get_package_share_directory('iturover_processing_assignment')
    bag_path = os.path.join(pkg_share, 'rosbag', 'assignment')

    return LaunchDescription([
        ExecuteProcess(
            cmd=['ros2', 'bag', 'play', bag_path, '--loop'],
            output='screen',
        ),
    ])
