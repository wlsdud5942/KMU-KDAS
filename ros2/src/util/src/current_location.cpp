#include <chrono>
#include <memory>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include "geometry_msgs/msg/point.hpp"
#include "tf2/exceptions.h"
#include "tf2/utils.h"

using namespace std::chrono_literals;

class LocationNode : public rclcpp::Node
{
public:
  LocationNode()
  : Node("location_node")
  {
    // Create a TF buffer to store transform data using the node's clock.
    tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
    // Create a TF listener to subscribe to /tf and /tf_static topics.
    tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

    // Create a publisher
    publisher_ = this->create_publisher<geometry_msgs::msg::Point>("location", 20);

    // Set up a timer to periodically call the on_timer() function every 500 milliseconds.
    timer_ = this->create_wall_timer(50ms, std::bind(&LocationNode::on_timer, this));
  }

private:
void on_timer()
{
    try {
        auto transform_stamped = tf_buffer_->lookupTransform("map", "base_link", rclcpp::Time(0), 100ms);

        // Extract yaw (heading) from quaternion
        double yaw = tf2::getYaw(transform_stamped.transform.rotation) ; //rad 

        // + (M_PI / 2)
        
        double x_raw = transform_stamped.transform.translation.x;
        double y_raw = transform_stamped.transform.translation.y;
        /*
        double cos_theta = std::cos(theta_rad); 
        double sin_theta = std::sin(theta_rad);
        double x_corrected = x_raw * cos_theta - y_raw * sin_theta;
        double y_corrected = x_raw * sin_theta + y_raw * cos_theta;
        */
        double x = x_raw;
        double y = y_raw;
        
        // Publish translation
        // based on front axle
    
        geometry_msgs::msg::Point point_msg;
        // front axle
        point_msg.x = drop(x + wheelBase * std::cos(yaw));
        point_msg.y = drop(y + wheelBase * std::sin(yaw));
        // rear axle
        //point_msg.x = drop(x);
        //point_msg.y = drop(y);
        
        point_msg.z = drop(yaw);  

        publisher_->publish(point_msg);
        
        //RCLCPP_INFO(this->get_logger(),"location: [%.2f, %.2f], heading: %.2f rad",point_msg.x, point_msg.y, point_msg.z);
    } catch (const tf2::TransformException &ex) {
        RCLCPP_WARN(this->get_logger(), "Failed to get transform: %s", ex.what());
    }
}
  double drop(double num){
    return floor(num * 10) / 10;
  }
  


  // Member variables
  rclcpp::TimerBase::SharedPtr timer_;
  std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
  std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
  rclcpp::Publisher<geometry_msgs::msg::Point>::SharedPtr publisher_;
  double wheelBase = 0.26;
  double theta_rad = 0.121;
};

int main(int argc, char **argv)
{
  // Initialize ROS2.
  rclcpp::init(argc, argv);
  auto node = std::make_shared<LocationNode>();

  // Spin the node so that callbacks are processed.
  rclcpp::spin(node);

  // Shutdown ROS2.
  rclcpp::shutdown();
  return 0;
}
