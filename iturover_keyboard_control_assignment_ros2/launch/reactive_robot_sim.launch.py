import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('reactive_robot_sim')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')

    gui = LaunchConfiguration('gui').perform(context)
    rviz = LaunchConfiguration('rviz')
    model = LaunchConfiguration('model').perform(context)
    ground_truth = LaunchConfiguration('ground_truth').perform(context)
    world = LaunchConfiguration('world').perform(context)
    use_sim_time = LaunchConfiguration('use_sim_time')

    world_path = os.path.join(pkg_share, 'worlds', f'{world}.world')
    xacro_path = os.path.join(pkg_share, 'urdf', f'turtlebot3_{model}.urdf.xacro')
    rviz_config_path = os.path.join(pkg_share, 'config', 'reactive_robot.rviz')

    robot_description_doc = xacro.process_file(
        xacro_path,
        mappings={'ground_truth': ground_truth},
    )
    robot_description = robot_description_doc.toxml()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_path,
            'gui': gui,
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description,
        }],
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_urdf',
        output='screen',
        arguments=[
            '-entity', f'turtlebot3_{model}',
            '-topic', 'robot_description',
            '-x', '-0.0',
            '-y', '9.5',
            '-z', '0.0',
            '-R', '-0.0',
            '-P', '-0.0',
            '-Y', '-1.57',
        ],
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(rviz),
    )

    return [
        gazebo,
        robot_state_publisher,
        spawn_entity,
        rviz_node,
    ]


def generate_launch_description():
    pkg_share = get_package_share_directory('reactive_robot_sim')
    models_path = os.path.join(pkg_share, 'models')

    return LaunchDescription([
        AppendEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=models_path,
        ),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument(
            'model',
            default_value='burger_rgbd',
            description='{burger_rgbd, burger, waffle}',
        ),
        DeclareLaunchArgument('ground_truth', default_value='false'),
        DeclareLaunchArgument('world', default_value='obs_corridor_world'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        OpaqueFunction(function=launch_setup),
    ])
