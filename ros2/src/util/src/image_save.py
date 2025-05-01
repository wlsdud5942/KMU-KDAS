#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import threading

class RGBImageSaverNode(Node):
    def __init__(self):
        super().__init__('rgb_image_saver_node')
        self.bridge = CvBridge()
        self.frame_count = 0
        self.latest_frame = None

        # Create 'save/saved_rgb_images' directory
        base_save_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(base_save_dir, exist_ok=True)

        self.output_dir = os.path.join(base_save_dir, 'saved_rgb_images')
        os.makedirs(self.output_dir, exist_ok=True)

        self.image_format = 'jpg'  # or 'png'

        self.subscription = self.create_subscription(
            Image,
            '/camera/color_image',  # Adjust to your actual topic
            self.image_callback,
            10
        )

        # Start a thread to listen for keypress
        threading.Thread(target=self.wait_for_keypress, daemon=True).start()

        self.get_logger().info(f'Initialized. Press c and Enter to save an image to {self.output_dir}/')

    def image_callback(self, msg: Image):
        try:
            self.latest_frame = msg
        except Exception as e:
            self.get_logger().error(f'Error storing latest frame: {e}')

    def wait_for_keypress(self):
        while True:
            key = input().strip().lower()
            if key == 'c' and self.latest_frame is not None:
                try:
                    cv_image = self.bridge.imgmsg_to_cv2(self.latest_frame, desired_encoding='bgr8')
                    filename = os.path.join(
                        self.output_dir,
                        f'rgb_{self.frame_count:04d}.{self.image_format}'
                    )
                    cv2.imwrite(filename, cv_image)
                    self.get_logger().info(f'Saved: {filename}')
                    self.frame_count += 1
                except Exception as e:
                    self.get_logger().error(f'Failed to save image: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = RGBImageSaverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()