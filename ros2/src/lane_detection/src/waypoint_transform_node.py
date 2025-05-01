#!/usr/bin/env python3
import os
import sys
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, MultiArrayDimension
from geometry_msgs.msg import Point


class WaypointTransformNode(Node):
    """
    Local 좌표 (x_local, z_local)를 현재 차량 pose를 기준으로 World 좌표 (x_world, y_world)로 변환하는 노드
    - Pose 수신 (/location)
    - Local Waypoint 수신 (/lane_detection/waypoints_local)
    - 변환된 World Waypoint 발행 (/lane_detection/waypoints_world)
    - Pose와 Local 수신 간 시간 차이를 검사하여 0.5초 초과시 변환 스킵
    """

    def __init__(self):
        super().__init__('waypoint_transform_node')

        # Pose 저장용 변수 (x, y, yaw 방향각, pose 수신 시간)
        self.x0 = None
        self.y0 = None
        self.yaw = None
        self.pose_time = None

        # Waypoint 저장용 변수 (local 좌표와 수신 시간)
        self.latest_local = None  # (x_local, z_local)
        self.local_time = None    # 수신된 local 좌표의 수신 시간

        # --- ROS 통신 설정 ---
        # 현재 차량 Pose (Cartographer) 구독
        self.create_subscription(Point,
                                 '/location', self.pose_callback, 20)
        # SCNN 결과 Local Waypoint 구독
        self.create_subscription(Float32MultiArray,
                                 '/lane_detection/waypoints_local', self.local_callback, 20)
        # 변환 완료된 World 좌표 퍼블리시
        self.world_pub = self.create_publisher(Point,
                                               '/lane_detection/waypoints_world', 20)

    def pose_callback(self, msg: Point):
        """
        /location callback
        - recive x, y location & yaw angle 
        - pose 수신 시각 저장
        """
        self.yaw = msg.z
        self.x0 = msg.x
        self.y0 = msg.y
        self.pose_time = self.get_clock().now()  # 현재 시각 저장
        self.try_publish()  # local waypoint가 준비되었으면 변환 시도

    def local_callback(self, msg: Float32MultiArray):
        """
        /lane_detection/waypoints_local 수신 시 호출
        - (x_local, z_local) 추출
        - local 수신 시각 저장
        """
        if len(msg.data) >= 2:
            self.latest_local = (msg.data[0], msg.data[1])  # (x_local, z_local)
            self.local_time = self.get_clock().now()
            self.try_publish()
        else:
            self.get_logger().warn('Invalid local waypoint message')

    def try_publish(self):
        """
        pose와 local waypoint 모두 준비되었을 때 변환을 시도
        - pose와 local 수신 시각 간 차이를 계산
        - Δt > 0.5초이면 변환하지 않고 스킵
        """
        if self.latest_local is None:
            self.get_logger().warn("latest_local is None, skipping publish.")
            return
        
        x_local, z_local = self.latest_local

        # --- Local → World 변환 ---
        cos_yaw = np.cos(self.yaw)
        sin_yaw = np.sin(self.yaw)

        x_world = self.x0 + cos_yaw * z_local - sin_yaw * x_local
        y_world = self.y0 + sin_yaw * z_local + cos_yaw * x_local

        # --- World Waypoint 퍼블리시 ---
        msg_out = Point()
        msg_out.x = float(x_world)
        msg_out.y = float(y_world)
        self.world_pub.publish(msg_out)
        self.get_logger().info("published world coordinate")
        # --- 수신된 local waypoint 버퍼 클리어 (한 번만 변환하도록) ---
        self.latest_local = None
        self.local_time = None

def main(args=None):
    rclpy.init(args=args)
    node = WaypointTransformNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
