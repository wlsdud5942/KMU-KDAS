#!/usr/bin/env python3
import sys
import os
import json
import math
import pandas as pd
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Float32MultiArray

# locate package resources
full_path = os.path.join(os.getcwd(), "ros2/src/path_planning")
sys.path.append(os.path.join(full_path, "src"))

from waypoint_interpolator import interpolate_path
from area_checker import check_area

class PathSenderNode(Node):
    def __init__(self):
        super().__init__('path_sender')
        self.i = 0
        # Publisher for planned path
        self.path_pub_x = self.create_publisher(Float32MultiArray, 'path_x', 10)
        self.path_pub_y = self.create_publisher(Float32MultiArray, 'path_y', 10)

        # Directory for per-area JSON waypoint files
        self.config_dir = os.path.join(full_path, 'config')

        self.get_logger().info("Path Sender up & running")
        
        # Set the desired publishing frequency (in Hz)
        self.timer = self.create_timer(0.5, self.loop)  # 0.5 seconds interval
        self.is_final_point_reached = True  # To track if the final waypoint has been reached

        try:
            file_path = os.path.join(self.config_dir, f"test1.csv")
            self.current_path = self.load_waypoints(file_path)
            self.finished = False
            self.get_logger().info("waypoints loaded")

        except Exception as e:
            self.get_logger().warn(f"Failed to load waypoint, path: {file_path}: {e}")
            return

    def load_waypoints(self, filepath):
        return np.loadtxt(filepath, delimiter=',')

    #sliding window
    def publish_path(self, i):
        x_pub = self.x_list[i:i+10]
        y_pub = self.y_list[i:i+10]        

        msgx = Float32MultiArray()
        msgy = Float32MultiArray()
        #msgLD = Float32()

        msgx.data = x_pub
        msgy.data = y_pub
        #msgLD.data = self.LD

        self.path_pub_x.publish(msgx)
        self.path_pub_y.publish(msgy)

    def loop(self):
        self.x_list = self.current_path[:, 0].tolist()
        self.y_list = self.current_path[:, 1].tolist()
        self.publish_path(self.i)
        self.i += 1;   

    

def main():
    rclpy.init()
    node = PathSenderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down PathSenderNode...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
