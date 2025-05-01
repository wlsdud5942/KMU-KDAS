import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node

def generate_launch_description():

    carto_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('qcar2_nodes'),
                'launch',
                'Cartographer_localization.py'
            )
        )
    )

    util_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('util'),
                'launch',
                'util_launch.py'
            )
        )
    )

    lane_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('lane_detection'),
                'launch',
                'lane_detection_launch.py'
            )
        )
    )

    yoloNode = Node(
        package='yolo_detection',  
        executable='yolo_node.py',
        name='yolo_node',
        output='screen'
    )

    stopper = Node(
        package='path_planning',
        executable='stopper',
        name='stopper',
        parameters=[{'use_sim_time':True}],
        output='screen'
    )

    pathplanner = Node(
        package='path_planning',
        executable='path_sender.py',
        name='path_planner',
        parameters=[{'use_sim_time':True}],
        output='screen'
    )

    return LaunchDescription([
        carto_launch,
        util_launch,
        lane_launch,
        yoloNode,
        stopper,
        pathplanner,
    ])
