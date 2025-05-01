#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os

class ImageToVideoConverter(Node):
    def __init__(self):
        super().__init__('image_to_video_converter')
        self.bridge = CvBridge()
        self.subscription = self.create_subscription(
            Image,
            '/camera/color_image',
            self.image_callback,
            10
        )

        # Create save directory
        base_save_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(base_save_dir, exist_ok=True)
        self.output_path = os.path.join(base_save_dir, 'qcar_output_video.mp4')

        self.video_writer = None
        self.get_logger().info('Subscribed to /camera/color_image')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            if self.video_writer is None:
                self.init_video_writer(cv_image)
            self.video_writer.write(cv_image)
        except Exception as e:
            self.get_logger().error(f'Error processing image: {e}')

    def init_video_writer(self, image):
        height, width, _ = image.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30  # adjust as needed
        self.video_writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))
        self.get_logger().info(f'Video writer initialized at: {self.output_path}')

    def release_video(self):
        if self.video_writer is not None:
            self.video_writer.release()
            self.get_logger().info(f'Video file saved and writer released: {self.output_path}')

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