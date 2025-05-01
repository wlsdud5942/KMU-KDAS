import subprocess

from launch import LaunchDescription
from launch.actions import (ExecuteProcess, LogInfo, RegisterEventHandler, OpaqueFunction, TimerAction)
from launch.substitutions import PathJoinSubstitution
from launch.event_handlers import (OnProcessExit, OnProcessStart)

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare



def generate_launch_description():
        
    current_location = Node(
        package='util',
        executable='current_location',
        name='current_location',
        parameters=[],
        output='screen'
        )
    
    getSimTime = Node(
        package='util',
        executable='get_sim_time_node',
        name='get_sim_time_node',
        parameters=[{'use_sim_time':True}],
        output='screen'
        )
    
    simulinkConverter = Node(
        package='util',
        executable='simulink_converter_node',
        name='simulink_converter_node',
        parameters=[{'use_sim_time':True}],
        output='screen'
        )
    
    clock = Node(
        package='util',
        executable='sim_time_node',
        name='sim_time_node',
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
        current_location,
        getSimTime,
        simulinkConverter,
        clock,
        pathplanner,
    ])
