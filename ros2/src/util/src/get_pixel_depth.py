#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
import numpy as np
import threading
import os
import csv

class PixelDepthQueryNode(Node):
    def __init__(self):
        super().__init__('pixel_depth_query_node')
        self.subscription = self.create_subscription(
            Image,
            '/camera/depth_image',  # Change if needed
            self.depth_callback,
            10
        )
        self.latest_frame = None
        self.frame_shape = None

        # Create save directory
        save_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(save_dir, exist_ok=True)

        # CSV setup
        self.csv_path = os.path.join(save_dir, 'pixel_depth_query.csv')
        self.csv_file = open(self.csv_path, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['u', 'v', 'depth_mm'])

        self.get_logger().info('Pixel depth getter up & running')
        # Start pixel query listener
        threading.Thread(target=self.wait_for_coordinate_input, daemon=True).start()

    def depth_callback(self, msg: Image):
        try:
            depth_array = np.frombuffer(msg.data, dtype=np.uint16).reshape((msg.height, msg.width))
            self.latest_frame = depth_array
            self.frame_shape = (msg.height, msg.width)
        except Exception as e:
            self.get_logger().error(f'Failed to process depth frame: {e}')

    def wait_for_coordinate_input(self):
        while True:
            try:
                user_input = input('Enter pixel ("u v"): ').strip()
                if self.latest_frame is None or not self.latest_frame.any():
                    print("No frame received yet.")
                    continue

                u_str, v_str = user_input.split()
                u, v = int(u_str) - 1, int(v_str) - 1

                if 0 <= v < self.frame_shape[0] and 0 <= u < self.frame_shape[1]:
                    depth_mm = int(self.latest_frame[v, u])  # Note: OpenCV image order is (row, col) -> (v, u)
                    print(depth_mm)

                    # Save to CSV
                    self.csv_writer.writerow([u + 1, v + 1, depth_mm])
                    self.csv_file.flush()
                else:
                    print(f"Pixel ({u+1}, {v+1}) out of bounds (max: {self.frame_shape[1]}, {self.frame_shape[0]})")
            except ValueError:
                print("Invalid input. Please enter pixel coordinates as: u v")
            except Exception as e:
                print(f"Error reading pixel input: {e}")

    def destroy_node(self):
        self.csv_file.close()
        self.get_logger().info(f"Saved queried pixels to {self.csv_path}")
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = PixelDepthQueryNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
