from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 1. SCNN Inference Node
        Node(
            package='lane_detection',
            executable='lane_detection_node',
            name='lane_detection_node',
            output='screen'
        ),

        # 2. Local to World Transform Node
        Node(
            package='lane_detection',
            executable='waypoint_transform_node',
            name='waypoint_transform_node',
            output='screen'
        ),
    ])
