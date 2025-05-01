#!/usr/bin/env python3
import os
import cv2
import rclpy

from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Int32

from cv_bridge import CvBridge
from ultralytics import YOLO
from ament_index_python.packages import get_package_share_directory


class QCarDetectionNode(Node):
    def __init__(self):
        super().__init__('qcar_detection_node')

        # QCar2 RGBD 카메라 컬러 토픽 구독
        self.subscription = self.create_subscription(
            Image,
            '/camera/color_image',  # QCar2 RGBD 컬러 스트림
            self.image_callback,
            10)

        # 정지 감지 관련 변수
        self.stop_detected_count = 0
        self.suppression_count = 0
        self.THRESHOLD = 30         # 연속 감지 프레임 수 기준
        self.SUPPRESSION_FRAMES = 200  # 정지 출력 이후 무시할 프레임 수

        # stop 검지 여부 퍼블리시 (1/0)
        self.int_publisher = self.create_publisher(Int32, '/stop', 10)

        # YOLO 모델 로드
        shared = get_package_share_directory('yolo_detection')
        filename = "0426yolo.pt"
        full_path = os.path.join(shared, "models", filename)
        self.model = YOLO(full_path)

        # 이미지 변환용 bridge
        self.bridge = CvBridge()

        # 타이머: 10 FPS로 주기적 실행
        self.timer = self.create_timer(1 / 10, self.process_frame)

        # 이미지 버퍼 초기화
        self.latest_frame = None

        self.get_logger().info("YOLO 객체 감지 노드 시작 (출력: /stop Int32)")

    def image_callback(self, msg):
        try:
            self.latest_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            self.latest_frame = None

    def process_frame(self):
        if self.latest_frame is None:
            self.get_logger().warn("No frame received")
            return

        msg_int = Int32()

        # suppression 중이면 무조건 0 출력
        if self.suppression_count > 0:
            self.suppression_count -= 1
            msg_int.data = 0
        else:
            # YOLO 감지 수행
            results = self.model(self.latest_frame, imgsz=(480, 640), conf=0.6)

            # 감지된 클래스 번호 집합 수집
            detected_cls = set()
            for r in results:
                for cls_idx in r.boxes.cls:
                    detected_cls.add(int(cls_idx))

            # 클래스 0 또는 1 감지 여부
            detected = any(cls in detected_cls for cls in [0, 1])

            # 연속 감지 프레임 수 업데이트
            if detected:
                self.stop_detected_count += 1
            else:
                self.stop_detected_count = 0

            # 기준 초과 시 1 출력 + suppression 시작
            if self.stop_detected_count >= self.THRESHOLD:
                msg_int.data = 1
                self.suppression_count = self.SUPPRESSION_FRAMES
                self.stop_detected_count = 0  # 초기화
            else:
                msg_int.data = 0

        self.int_publisher.publish(msg_int)
        self.get_logger().info(f"[Stop FrameCount={self.stop_detected_count}, Suppress={self.suppression_count}] Signal: {msg_int.data}")

def main(args=None):
    rclpy.init(args=args)
    node = QCarDetectionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
