#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import numpy as np
import csv
import os

class DepthCSVExporter(Node):
    def __init__(self):
        super().__init__('depth_csv_exporter')
        self.bridge = CvBridge()

        # depth/raw 토픽 (정렬 안 된 상태)
        self.create_subscription(
            Image, '/camera/depth_image',
            self.depth_callback, 10
        )

        # ★ ROI 설정 
        ##1m
        #Point 1: (u=81, v=293)
        #Point 2: (u=589, v=317)

        # RGB 기준 ROI 
        #1m벽 영역
        self.u0, self.u1 = 81, 589
        self.v0, self.v1 = 293, 317

        #2m벽 영역
        #self.u0, self.u1 = 204, 255
        #self.v0, self.v1 = 450, 276

        # GT 거리 (m) 및 CSV 파일 경로
        self.gt_distance = 1.0  # 실제 거리 (m)
        #self.gt_distance = 2.0 

        # Create save directory
        save_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(save_dir, exist_ok=True)

        self.csv_path = os.path.join(save_dir, f"depth_calib_{self.gt_distance:.1f}m.csv")

        # — 카메라 파라미터 —  
        # RGB intrinsics
        self.rgb_intr = {'fx':455.2, 'fy':459.43, 'cx':308.53, 'cy':213.56}
        # Depth intrinsics
        self.dep_intr = {'fx':385.6, 'fy':385.6, 'cx':321.9, 'cy':237.3}
        # RGB->Depth extrinsics
        self.R = np.array([
            [ 1.      ,  0.004008 ,  0.0001655],
            [-0.004007,  1.       , -0.003435 ],
            [-0.0001792, 0.003434 ,  1.       ]
        ])
        self.t = np.array([-0.01474, -0.0004152, -0.0002451])

        self.done = False
        self.get_logger().info(
            f"[2.0] ROI(u={self.u0}-{self.u1},v={self.v0}-{self.v1}), "
            f"GT={self.gt_distance}m → {self.csv_path}"
        )

    def map_rgb_to_depth(self, u, v):
        """RGB(u,v) → aligned Depth 픽셀 (u_d, v_d) 및 ray depth scale"""
        x_r = (u - self.rgb_intr['cx']) / self.rgb_intr['fx']
        y_r = (v - self.rgb_intr['cy']) / self.rgb_intr['fy']
        ray = np.array([x_r, y_r, 1.0])
        P = self.R.dot(ray) + self.t
        u_d = (P[0] * self.dep_intr['fx'] / P[2]) + self.dep_intr['cx']
        v_d = (P[1] * self.dep_intr['fy'] / P[2]) + self.dep_intr['cy']
        return int(round(u_d)), int(round(v_d)), P[2]

    def depth_callback(self, msg: Image):
        if self.done:
            return

        # raw depth (un-aligned) 읽기
        raw = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        depth = raw.astype(np.float32)  # QLabs: 픽셀 기반(스케일값)

        h, w = depth.shape
        vals = []

        # RGB ROI 내 모든 픽셀 → Depth 프레임 픽셀로 변환 → 값 추출
        for v in range(self.v0, self.v1):
            for u in range(self.u0, self.u1):
                u_d, v_d, _ = self.map_rgb_to_depth(u, v)
                if 0 <= u_d < w and 0 <= v_d < h:
                    d = depth[v_d, u_d]
                    vals.append(d)

        if not vals:
            self.get_logger().warn("No valid aligned depth in ROI.")
            return

        # CSV 저장
        with open(self.csv_path, 'w', newline='') as f:
            wtr = csv.writer(f)
            wtr.writerow(['depth_pixel','ground_truth_m'])
            for d in vals:
                wtr.writerow([int(d), self.gt_distance])

        med = float(np.median(vals))
        self.get_logger().info(
            f"[2.0] Saved {len(vals)} samples to {self.csv_path}. "
            f"Median depth_pixel = {med:.1f}"
        )
        self.done = True

def main():
    rclpy.init()
    node = DepthCSVExporter()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
