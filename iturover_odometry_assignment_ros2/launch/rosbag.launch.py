import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('iturover_odometry_assignment')
    bag_path = os.path.join(pkg_share, 'rosbag', 'scenario')

    odometry_node = Node(
        package='iturover_odometry_assignment',
        executable='odometry.py',
        name='rover_odometry',
        output='screen',
        # This known recording has Q14 quaternions and incorrect validity flags.
        # Keep the compatibility choice local to this launch, not live sensors.
        parameters=[{'use_sim_time': True, 'heading_source': 'imu',
                     'orientation_policy': 'assignment_q14'}],
    )

    bag_player = ExecuteProcess(
        cmd=['ros2', 'bag', 'play', bag_path, '--start-offset', LaunchConfiguration('start_offset'),
             '--clock', '100', '--rate', LaunchConfiguration('rate')],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('rate', default_value='1.0'),
        DeclareLaunchArgument('start_offset', default_value='0.0'),
        odometry_node,
        bag_player,
    ])
