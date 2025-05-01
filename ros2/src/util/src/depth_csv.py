#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import os
import csv
import threading

class KeyTriggeredDepthSaver(Node):
    def __init__(self):
        super().__init__('key_triggered_depth_saver')
        self.subscription = self.create_subscription(
            Image,
            '/camera/depth_image',  # Replace with your actual topic
            self.depth_callback,
            10
        )
        self.latest_frame = None
        self.frame_count = 0
        self.output_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(self.output_dir, exist_ok=True)

        # Start key listener in a separate thread
        threading.Thread(target=self.wait_for_keypress, daemon=True).start()
        self.get_logger().info('Press "c" and Enter to save a depth frame.')

    def depth_callback(self, msg: Image):
        try:
            self.latest_frame = np.frombuffer(msg.data, dtype=np.uint16).reshape((msg.height, msg.width))
        except Exception as e:
            self.get_logger().error(f"Error processing depth frame: {e}")

    def wait_for_keypress(self):
        while True:
            key = input()
            if key.strip().lower() == 'c' and self.latest_frame is not None:
                self.save_to_csv(self.latest_frame)

    def save_to_csv(self, depth_array):
        self.frame_count += 1
        filename = os.path.join(self.output_dir, f'depth_{self.frame_count:04d}.csv')
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                for row in depth_array:
                    writer.writerow(row)
            self.get_logger().info(f'Saved frame to {filename}')
        except Exception as e:
            self.get_logger().error(f"Failed to save CSV: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = KeyTriggeredDepthSaver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
