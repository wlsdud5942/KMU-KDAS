#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray, Bool, String
from cv_bridge import CvBridge
import cv2
import os

class ImageToVideoConverter(Node):
    def __init__(self):
        super().__init__('image_to_video_converter')
        self.bridge = CvBridge()

        # Create save directory
        base_save_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(base_save_dir, exist_ok=True)
        self.output_video_path = os.path.join(base_save_dir, 'qcar_output_video.mp4')

        # Camera frame subscription
        self.create_subscription(
            Image,
            '/camera/color_image',
            self.image_callback,
            10
        )

        # Lane center subscriptions
        self.create_subscription(
            Float32MultiArray,
            '/lane_detection/waypoints_x',
            self.center_x_callback,
            10
        )
        self.create_subscription(
            Float32MultiArray,
            '/lane_detection/waypoints_y',
            self.center_y_callback,
            10
        )

        # Object detection subscriptions
        self.create_subscription(
            Bool,
            '/stop',
            self.object_detected_callback,
            10
        )
        self.create_subscription(
            String,
            '/detection_label',
            self.detection_label_callback,
            10
        )

        # video writer
        self.video_writer = None

        # lane data
        self.center_x = []
        self.center_y = []
        self.points = []

        # detection data + timestamps
        self.object_detected = False
        self.detection_label = ""
        now = self.get_clock().now()
        self.last_object_time = now
        self.last_label_time = now

        # how long to consider data "fresh"
        self.text_timeout = Duration(seconds=0.1)

        self.get_logger().info('Subscribed to image, lane, and detection topics')

    def center_x_callback(self, msg: Float32MultiArray):
        self.center_x = list(msg.data)
        self._update_points()

    def center_y_callback(self, msg: Float32MultiArray):
        self.center_y = list(msg.data)
        self._update_points()

    def _update_points(self):
        if len(self.center_x) == len(self.center_y):
            self.points = list(zip(self.center_x, self.center_y))
        else:
            self.points = []

    def object_detected_callback(self, msg: Bool):
        self.object_detected = msg.data
        self.last_object_time = self.get_clock().now()

    def detection_label_callback(self, msg: String):
        self.detection_label = msg.data
        self.last_label_time = self.get_clock().now()

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            if self.video_writer is None:
                self.init_video_writer(frame)

            now = self.get_clock().now()

            # draw Stop sign status only if fresh
            if (now - self.last_object_time) < self.text_timeout:
                cv2.putText(
                    frame,
                    f"Stop sign: {self.object_detected}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            # draw Label only if fresh
            if (now - self.last_label_time) < self.text_timeout:
                cv2.putText(
                    frame,
                    f"Label: {self.detection_label}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            # draw lane-center points in red
            for x, y in self.points:
                xi, yi = int(x), int(y)
                cv2.circle(
                    frame,
                    (xi, yi),
                    radius=4,
                    color=(0, 0, 255),
                    thickness=-1
                )

            self.video_writer.write(frame)

        except Exception as e:
            self.get_logger().error(f'Error processing image: {e}')

    def init_video_writer(self, image):
        h, w, _ = image.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            self.output_video_path, fourcc, 30.0, (w, h)
        )
        self.get_logger().info(f'Video writer initialized: {self.output_video_path}')

    def release_video(self):
        if self.video_writer:
            self.video_writer.release()
            self.get_logger().info(f'Video file saved and writer released: {self.output_video_path}')

def main(args=None):
    rclpy.init(args=args)
    node = ImageToVideoConverter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.release_video()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()