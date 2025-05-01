import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription


from launch_ros.actions import Node
e

def generate_launch_description():

    csvsaver = Node(
        package='util',
        executable='waypointSaver.py',
        name='waypointSaver',
        parameters=[],
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
        csvsaver,
        pathplanner,
    ])
