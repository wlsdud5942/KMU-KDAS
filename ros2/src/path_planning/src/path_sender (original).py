#!/usr/bin/env python3
import sys, os, json, time, csv
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import String, Int32, Float32MultiArray, Float32
from ament_index_python.packages import get_package_share_directory


shared = get_package_share_directory('path_planning')

class PathSenderNode(Node):
    def __init__(self):
        super().__init__('path_sender')
        
        # ── 퍼블리셔 & 구독자 설정 ───────────────────────────────────────────
        
        self.pub_x = self.create_publisher(Float32, 'path_x', 100)
        self.pub_y = self.create_publisher(Float32, 'path_y', 100)
        self.pub_path_mode = self.create_publisher(Int32, 'path_mode', 100)
        self.create_subscription(Point,               'location',                   self.cb_location, 20)
        self.create_subscription(Float32MultiArray,  '/lane_detection/waypoints_x', self.cb_scnn_x,   20)
        self.create_subscription(Float32MultiArray,  '/lane_detection/waypoints_y', self.cb_scnn_y,   20)
        self.create_subscription(Int32,               '/lane_detection/lane_state', self.cb_state,    200)
        self.create_subscription(String,              '/detection_label',           self.cb_label,    10)
        self.create_subscription(Int32,                '/stop',                     self.cb_stop,     10)

        # ── 파라미터 ─────────────────────────────────────────────────────────
        self.WINDOW         = 4      # 4점씩 퍼블리시
        self.COOLDOWN_SEC   = 1.0    # 전환 후 1초간 잠금
        self.SCNN_DEBOUNCE  = 3      # SCNN ROI 연속 감지 프레임 수
        self.config_dir     = os.path.join(shared, "config")

        # 예선 시나리오: 순서대로 진행
        self.scenario = [
            '1','2','3','4','5','6-1','6-2','7','8',
            '9','10-1','10-2','10a','11','12','5a','6a','7a','13','14'
            ]
        
        self.path_state= [ 2, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 2] #0: straight, 1: curve, 2: start and finish

        # SCNN 트리거용 ROI (다음 구간 진입 영역: xmin,xmax,ymin,ymax)
        self.scnn_bbox = {
            '1':   (-1.6, -1.0, -1.2, -0.6),
            '2':   (-0.6,  0.0, -1.3, -0.7),
            '3':   ( 1.0,  1.6, -1.6, -1.0),
            '4':   ( 1.7,  2.3, -0.4,  0.2),
            '5':   ( 2.2,  2.8,  3.1,  3.7),
            '6-1': ( 1.6,  2.0,  3.8,  4.4),
            '6-2': ( 0.6,  1.2,  4.0,  4.6),
            '7':   (-0.9, -0.3,  4.0,  4.6),
            '8':   (-1.8, -1.2,  3.3,  3.9),
            '9':   (-2.1, -1.5,  1.6,  2.2),
            '10-1':(-1.2, -0.8,  0.8,  1.2), 
            '10-2':(-0.9, -0.5,  0.7,  1.1),
            '10a': (-0.6, -0.2,  0.7,  1.1),
            '11':  ( 1.2,  1.8,  0.3,  0.9),
            '12':  ( 1.9,  2.5,  1.1,  1.7),
            '5a':  ( 2.2,  2.8,  3.1,  3.7),
            '6a':  ( 1.6,  2.0,  3.8,  4.4),
            '7a':  (-0.9, -0.3,  4.0,  4.6),
            '13':  (-1.8, -1.2,  3.3,  3.9),
            '14':  (-2.3, -1.7,  0.1,  0.7),     

         }

        # ── 상태 변수 ─────────────────────────────────────────────────────────
        self.pos              = (0.0, 0.0)    # Cartographer 위치
        self.center_x, self.center_y = [], [] # SCNN 중심점 리스트
        self.lane_state       = 0             # SCNN 활성 여부
        self.detection_label  = ''            # YOLO 라벨
        self.stop_flag        = False         # STOP 플래그

        self.segment_idx       = 0           # 현재 시나리오 인덱스
        self.buffer_path       = []
        self.next_buffer       = []
        self.current_index     = 0
        self.next_index        = 0
        self.last_trigger_time = 0.0         # 마지막 전환 시각
        self.scnn_counter      = 0           # Debounce 카운터

        # loop frequency
        self.create_timer(0.01, self.loop)
        self.create_timer(0.5, self.path_loop)
        self.get_logger().info("PathSenderNode initialized.")

        self.preload_buffer(self.segment_idx)  # 0+1 준비

    # ── 콜백들 ────────────────────────────────────────────────────────────────
    def cb_location(self, msg: Point):
        self.pos = (msg.x, msg.y)

    def cb_scnn_x(self, msg: Float32MultiArray):
        self.center_x = list(msg.data)

    def cb_scnn_y(self, msg: Float32MultiArray):
        self.center_y = list(msg.data)

    def cb_state(self, msg: Int32):
        self.lane_state = msg.data

    def cb_label(self, msg: String):
        self.detection_label = msg.data

    def cb_stop(self, msg: Int32):
        self.stop_flag = msg.data

    # ── 파일 로드 유틸 ────────────────────────────────────────────────────────
    def load_csv(self, key: str):
        """key.csv → [[x,y], ...]"""
        coords = []
        path = os.path.join(self.config_dir, f"{key}.csv")
        try:
            with open(path, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    coords.append([float(row['x']), float(row['y'])])
        except Exception as e:
            self.get_logger().error(f"load_csv({key}) failed: {e}")
        return coords

    def load_json(self, key: str):
        """key.json → [[x,y], ...]"""
        try:
            with open(os.path.join(self.config_dir, f"{key}.json")) as f:
                return json.load(f)[key]
        except Exception as e:
            self.get_logger().error(f"load_json({key}) failed: {e}")
            return []

    def preload_buffer(self, idx: int):
        """현재 segment + 다음 segment 미리 로드"""
        key1 = self.scenario[idx]
        key2 = self.scenario[idx+1] if idx+1 < len(self.scenario) else None

        self.buffer_path = self.load_csv(key1) or self.load_json(key1)
        self.next_buffer = self.load_csv(key2) or self.load_json(key2) if key2 else []

        self.next_index = 0
        self.get_logger().info(f"Loaded [{key1}] ({len(self.buffer_path)} pts)")
        if key2:
            self.get_logger().info(f"Preloaded [{key2}] ({len(self.next_buffer)} pts)")


    # ── SCNN 트리거 판정 ─────────────────────────────────────────────────────
    def scnn_trigger(self) -> bool:
        # 1) SCNN 활성 & 중심점 수신
        if self.lane_state != 1 or not self.center_x:
            self.scnn_counter = 0
            return False

        # 2) ROI bbox 검사
        next_key = self.scenario[self.segment_idx+1] if self.segment_idx+1 < len(self.scenario) else None
        if next_key and next_key in self.scnn_bbox:
            xmin,xmax,ymin,ymax = self.scnn_bbox[next_key]
            cx, cy = self.center_x[0], self.center_y[0]
            if xmin <= cx <= xmax and ymin <= cy <= ymax:
                self.scnn_counter += 1
            else:
                self.scnn_counter = 0

        # 3) 연속 N 프레임 감지 시 트리거
        if self.scnn_counter >= self.SCNN_DEBOUNCE:
            self.scnn_counter = 0
            return True

        return False

    # ── Cartographer 트리거 (백업) ───────────────────────────────────────────
    def carto_trigger(self) -> bool:
        next_idx = self.segment_idx + 1
        if next_idx >= len(self.scenario):
            return False
        xmin,xmax,ymin,ymax = self.scnn_bbox.get(self.scenario[next_idx], (0,0,0,0))
        x,y = self.pos
        return (xmin <= x <= xmax and ymin <= y <= ymax)

    # ── 슬라이딩 윈도우 퍼블리시 ─────────────────────────────────────────────
    def publish_window(self):
        if not self.buffer_path:
            self.get_logger().warn("buffer is empty")
            return

        if self.current_index < len(self.buffer_path):
            pt = self.buffer_path[self.current_index]
            self.pub_x.publish(Float32(data=pt[0]))
            self.pub_y.publish(Float32(data=pt[1]))
            self.current_index += 1
            self.get_logger().info(f"path published, index: {self.current_index}")
        elif self.next_index < len(self.next_buffer):
            pt = self.next_buffer[self.next_index]
            self.pub_x.publish(Float32(data=pt[0]))
            self.pub_y.publish(Float32(data=pt[1]))
            self.next_index += 1
            self.get_logger().info(f"preloaded path published, index: {self.next_index}")

    def publish_path_mode(self):
        if 0 <= self.segment_idx < len(self.path_state):
            mode = self.path_state[self.segment_idx]
            self.pub_path_mode.publish(Int32(data=mode))



    # ── 메인 루프 ─────────────────────────────────────────────────────────────
    def loop(self):
        now = time.monotonic()
        
        if now - self.last_trigger_time < self.COOLDOWN_SEC:
            return 
        
        # 트리거 체크
        if (self.current_index >= len(self.buffer_path)) and (
        self.scnn_trigger() or self.carto_trigger()
        ):
            self.segment_idx += 1
            self.get_logger().info(f"changed to segment {self.segment_idx+1}")
            self.buffer_path = self.next_buffer
            self.current_index = self.next_index
            self.preload_buffer(self.segment_idx)
            self.last_trigger_time = now

            return

        if self.stop_flag == 1:
            self.get_logger().info("stop detected")
            time.sleep(4)
            return
        
        self.publish_path_mode()

    def path_loop(self):
        self.publish_window()   

def main():
    rclpy.init()
    node = PathSenderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
