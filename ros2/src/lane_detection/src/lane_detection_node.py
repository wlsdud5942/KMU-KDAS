#!/usr/bin/env python3

# --- 기본 패키지 및 ROS2, Torch 등 import ---
import os
import sys
import numpy as np
import torch
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray, MultiArrayDimension, Int32
from ament_index_python.packages import get_package_share_directory

# --- SCNN 모델 import (패키지 경로 등록 포함) ---
shared = get_package_share_directory('lane_detection')
sys.path.append(os.path.join(shared, 'src'))

from model import SCNN_LaneDetection
from postprocess_modify import postprocess_mask

# === ROS2 노드 정의 ===
class LaneDetectionNode(Node):
    """
    역할:
    - RGB 이미지를 받아 SCNN으로 차선 중심을 추론
    - ROI 범위 내 중심점 하나를 local 좌표 (x_local, z_local)로 추출
    - 이를 ROS2 토픽으로 퍼블리시
    
    퍼블리시 토픽:
      /lane_detection/waypoints_local (Float32MultiArray [x_local, z_local])
      /lane_detection/lane_state      (Int32, 0 = 없음, 1 = 있음)
    """
    def __init__(self):
        super().__init__('lane_detection_node')

        # OpenCV와 ROS 이미지 메시지를 변환하는 bridge
        self.bridge = CvBridge()

        # CUDA 사용 가능 시 GPU, 아니면 CPU 사용
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # --- SCNN 모델 로드 및 가중치 불러오기 ---
        self.model = SCNN_LaneDetection().to(self.device)
        ckpt = os.path.join(shared, 'models', 'scnn_lane_detection_0427.pth')
        try:
            self.model.load_state_dict(torch.load(ckpt, map_location=self.device))
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {e}")
            rclpy.shutdown()
            return
        self.model.eval()  # 추론 모드 설정

        # --- 카메라 파라미터 및 ROI 설정 ---
        self.fx, self.cx = 455.2, 308.53  # focal length, 중심점
        self.V_MIN = 365  # ROI 시작 (y축 하한)
        self.V_MAX = 390  # ROI 끝 (y축 상한)
        self.Z_FIXED = 0.5  # 고정된 깊이값 (m)

        # --- ROS2 토픽 구독 및 퍼블리시 ---
        self.create_subscription(Image, '/camera/color_image', self.image_callback, 20)
        self.local_pub = self.create_publisher(Float32MultiArray, '/lane_detection/waypoints_local', 20)
        self.lane_state_pub = self.create_publisher(Int32, '/lane_detection/lane_state', 10)


    def image_callback(self, msg: Image):
        """
        카메라 이미지가 들어왔을 때 실행되는 콜백 함수
        - 이미지를 SCNN에 넣고 중심점을 추론
        - ROI 내에서 가장 적합한 중심점 선택
        - 실세계 좌표 변환 후 퍼블리시
        """
        try:
            # ROS → OpenCV 이미지 변환
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            if cv_img is None:
                self.get_logger().warning("Empty image received. Skipping frame.")
                return

        except Exception as e:
            self.get_logger().error(f"cv_bridge error: {e}")
            return
        
        # 이미지 → Tensor 변환 및 정규화 [0,1]
        t = torch.from_numpy(cv_img).permute(2, 0, 1).unsqueeze(0).float() / 255.0
        t = t.to(self.device)

        # --- SCNN 추론 ---
        with torch.no_grad():
            seg = self.model(t)  # 차선 segmentation 결과 얻음

        # --- 후처리 ---
        state, us, vs, _ = postprocess_mask(seg, samples=300)

        # 차선이 없거나 픽셀 좌표가 없을 경우 → lane_state = 0
        if state == 0 or len(us) == 0:
            self.lane_state_pub.publish(Int32(data=0))
            return


        # ROI 영역 내에 있는 중심점들 필터링
        center_pix = list(zip(us, vs))
        candidates = [(u, v) for (u, v) in center_pix if self.V_MIN <= v <= self.V_MAX]

        if not candidates:
            return

        # 이미지 중심(cx)과 가장 가까운 점 하나 선택
        u_sel, v_sel = min(candidates, key=lambda p: abs(p[0] - self.cx))

        # --- 픽셀 → local 실세계 좌표 변환 ---
        x_local = (u_sel - self.cx) / self.fx * self.Z_FIXED
        z_local = self.Z_FIXED

        # --- 결과 퍼블리시 ---
        self.lane_state_pub.publish(Int32(data=1))
        self.publish_local_waypoint(x_local, z_local)

    def publish_local_waypoint(self, x_local, z_local):
        """
        추론된 (x_local, z_local) 좌표를 Float32MultiArray로 퍼블리시
        """
        msg = Float32MultiArray()
        msg.layout.dim.append(
            MultiArrayDimension(label='dim', size=2, stride=2)
        )
        msg.layout.data_offset = 0
        msg.data = [x_local, z_local]
        self.local_pub.publish(msg)
    

    
def main(args=None):
    rclpy.init(args=args)
    node = LaneDetectionNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
