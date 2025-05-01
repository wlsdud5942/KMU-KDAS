#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from rosgraph_msgs.msg import Clock
from cv_bridge import CvBridge
import cv2
import os

class ImageSaver(Node):
    def __init__(self):
        super().__init__('frame_saver')
        self.bridge = CvBridge()

        # Initialize current time
        self.current_time = None

        # Create subscribers
        self.create_subscription(Image, '/camera/color_image', self.image_callback, 10)
        self.create_subscription(Clock, '/clock', self.clock_callback, 10)

        # Create save directory
        base_save_dir = os.path.join(os.getcwd(), 'save')
        self.save_dir = os.path.join(base_save_dir, 'frames')
        os.makedirs(self.save_dir, exist_ok=True)

        self.get_logger().info('Subscribed to /camera/color_image and /clock')

    def clock_callback(self, msg):
        # Save the latest clock time as a float: seconds.nanoseconds
        self.current_time = msg.clock.sec + msg.clock.nanosec * 1e-9

    def image_callback(self, msg):
        if self.current_time is None:
            self.get_logger().warn('Waiting for /clock message...')
            return

        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            # Save image using the current ROS2 time
            filename = f"{self.current_time:.9f}.png"
            filepath = os.path.join(self.save_dir, filename)
            cv2.imwrite(filepath, cv_image)
            self.get_logger().info(f'Saved frame: {filepath}')
        except Exception as e:
            self.get_logger().error(f'Error processing image: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = ImageSaver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
