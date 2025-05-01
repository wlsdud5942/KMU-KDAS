import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (IncludeLaunchDescription, DeclareLaunchArgument, TimerAction)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (PathJoinSubstitution, LaunchConfiguration)

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # Launch arguments
    use_sim = LaunchConfiguration('use_sim')
    configuration_basename = LaunchConfiguration('configuration_basename')
    resolution = LaunchConfiguration('resolution')
    publish_period_sec = LaunchConfiguration('publish_period_sec')

    # Directories
    cartographer_config_dir = PathJoinSubstitution([
        FindPackageShare('qcar2_nodes'),
        'config',
    ])

    # Include the base QCar2 nodes + TF for your en./ros2/src/qcar2_nodes/maps/my_map2.pbstream'vironment or sim
    qcar2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('qcar2_nodes'),
                'launch',
                'qcar2_virtual_launch.py'
            )
        )
    )

    qcar2_to_lidar_tf_node = Node(
        package='qcar2_nodes',
        executable='fixed_lidar_frame_virtual',
        name='fixed_lidar_frame'
    )
    
    configuration_basename_la = DeclareLaunchArgument(
        'configuration_basename',
        default_value='qcar2_2d.lua',
        description='Name of the LUA file for Cartographer'
    )

    use_sim_la = DeclareLaunchArgument(
        'use_sim',
        default_value='false',
        description='Use simulation clock'
    )

    resolution_la = DeclareLaunchArgument(
        'resolution',
        default_value='0.05',
        description='Resolution of the occupancy grid (in meters per cell)'
    )

    publish_period_sec_la = DeclareLaunchArgument(
        'publish_period_sec',
        default_value='1.0',
        description='OccupancyGrid publishing period in seconds'
    )

    # The main Cartographer node in pure localization mode
    # carto_original_map.pbstream unmodified 
    # my_map.pbstream modified
    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim}],
        arguments=[
            '-configuration_directory', cartographer_config_dir,
            '-configuration_basename', configuration_basename,
            '-load_state_filename', os.path.join(
                                        get_package_share_directory('qcar2_nodes'),
                                        'maps', 'long_range.pbstream'),
            '-load_frozen_state',
            '-loaded_state_trimmer'
        ]
  
    )

    # The occupancy grid generation node
    cartographer_occupancy_grid_node = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim}],
        arguments=[
            '-resolution', resolution,
            '-publish_period_sec', publish_period_sec
        ]
    )

    initial_pose = TimerAction(
        period=2.0,
        actions=[Node(
            package='qcar2_nodes',
            executable='initial_pose',
            output='screen'
        )]
    )
    
    return LaunchDescription([
        qcar2_launch,
        configuration_basename_la,
        use_sim_la,
        resolution_la,
        publish_period_sec_la,
        cartographer_node,
        cartographer_occupancy_grid_node,
        qcar2_to_lidar_tf_node,
        initial_pose,
    ])
