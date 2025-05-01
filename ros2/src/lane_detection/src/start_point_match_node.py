#!/usr/bin/env python3
# start_point_match_node.py
# -----------------------------------------------------------------------------
# 역할:
# - SCNN이 추론한 중심점 (월드 좌표)을 수신
# - 각 segment의 시작점들과 거리 비교
# - 가장 가까운 시작점이 임계값(threshold) 이내이면:
#     → 해당 시작점 좌표 (x, y)를 /matched_start_point 토픽으로 퍼블리시
#     → 매칭 성공 상태로 /lane_state = 1 퍼블리시
# - 어떤 시작점과도 가까이 있지 않으면:
#     → 매칭 실패 상태로 /lane_state = 0 퍼블리시
# -----------------------------------------------------------------------------
import os
import numpy as np
import pandas as pd
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Int32
from ament_index_python.packages import get_package_share_directory

class StartPointMatchNode(Node):
    def __init__(self):
        super().__init__('start_point_match_node')

        # 매칭 허용 거리 (meters)
        self.threshold = 1

        # 구독: SCNN 추론 결과 (월드 좌표 중심점)
        self.create_subscription(Point, '/lane_detection/waypoints_world', self.scnn_callback, 20)

        # 퍼블리시: 매칭된 시작점 좌표
        self.match_pub = self.create_publisher(Point, '/matched_start_point', 20)

        # 퍼블리시: 매칭 성공 여부 (1: 매칭됨, 0: 실패)
        self.lane_state_pub = self.create_publisher(Int32, '/lane_state', 20)

        # 시작점 좌표 목록 로드 (segment_id, start_x, start_y)
        self.segment_start_points = self.load_segment_starts()

    def load_segment_starts(self):
        """
        waypoint_data/segment_start_points.csv 파일을 읽어
        segment 시작점 딕셔너리로 반환
        반환 형식: {segment_id: np.array([x, y])}
        """
        shared = get_package_share_directory('lane_detection')
        csv_path = os.path.join(shared, 'ref', 'start_end_point.csv')
        df = pd.read_csv(csv_path)
        return {
            int(row['segment_id']): np.array([row['start_x'], row['start_y']])
            for _, row in df.iterrows()
        }

    def scnn_callback(self, msg: Point):
        """
        SCNN 추론 중심점 수신 시:
        - 각 segment 시작점과의 거리 계산
        - 가장 가까운 시작점이 threshold 이내이면:
            → /matched_start_point 퍼블리시
            → /lane_state = 1
        - 아니면:
            → /lane_state = 0 (매칭 실패)
        """
        scnn_point = np.array([msg.x, msg.y])

        closest_seg = None
        min_dist = float('inf')

        # 각 시작점과 거리 비교
        for seg_id, start_pt in self.segment_start_points.items():
            dist = np.linalg.norm(scnn_point - start_pt)
            if dist < self.threshold and dist < min_dist:
                closest_seg = seg_id
                min_dist = dist

        if closest_seg is not None:
            # 매칭 성공: 시작점 좌표 퍼블리시
            matched = self.segment_start_points[closest_seg]
            self.match_pub.publish(Point(x=matched[0], y=matched[1], z=0.0))
            self.lane_state_pub.publish(Int32(data=1))
        else:
            # 매칭 실패: 상태만 퍼블리시
            self.lane_state_pub.publish(Int32(data=0))


def main(args=None):
    rclpy.init(args=args)
    node = StartPointMatchNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()