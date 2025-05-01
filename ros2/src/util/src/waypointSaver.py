#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from rosgraph_msgs.msg import Clock
import csv
import os

class LocationLoggerNode(Node):
    def __init__(self):
        super().__init__('location_logger_node')

        # Define save directory as 'save/locations/'
        self.save_dir = os.path.join(os.getcwd(), 'save')
        os.makedirs(self.save_dir, exist_ok=True)

        # Define CSV file path
        self.csv_path = os.path.join(self.save_dir, 'location_data.csv')

        # Open CSV file
        self.csv_file = open(self.csv_path, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)

        # Write header
        self.csv_writer.writerow(['time', 'x', 'y', 'heading'])

        # Initialize latest clock time
        self.current_time = None

        # Subscribers
        self.create_subscription(Point, 'location', self.location_callback, 10)
        self.create_subscription(Clock, '/clock', self.clock_callback, 10)

        self.get_logger().info(f"Saving location data to {self.csv_path}")

    def clock_callback(self, msg):
        # Update the current time from /clock
        self.current_time = msg.clock.sec + msg.clock.nanosec * 1e-9

    def location_callback(self, msg: Point):
        if self.current_time is None:
            self.get_logger().warn('Waiting for /clock message...')
            return

        # Write (time, x, y) to CSV
        self.csv_writer.writerow([f"{self.current_time:.9f}", f"{msg.x:.6f}", f"{msg.y:.6f}",f"{msg.z}"])
        self.get_logger().info(f"Saved: time={self.current_time:.9f}, x={msg.x:.6f}, y={msg.y:.6f}, yaw={msg.z:6f}")

    def destroy_node(self):
        # Close the file properly
        self.csv_file.close()
        self.get_logger().info("CSV file closed and data saved.")
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)

    location_logger_node = LocationLoggerNode()

    try:
        rclpy.spin(location_logger_node)
    except KeyboardInterrupt:
        pass
    finally:
        location_logger_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
