import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('iturover_odometry_assignment')
    bag_path = os.path.join(pkg_share, 'rosbag', 'scenario')

    odometry_node = Node(
        package='iturover_odometry_assignment',
        executable='odometry.py',
        name='rover_odometry',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    bag_player = ExecuteProcess(
        cmd=['ros2', 'bag', 'play', bag_path, '--start-offset', '8', '--clock'],
        output='screen',
    )

    return LaunchDescription([
        odometry_node,
        bag_player,
    ])
