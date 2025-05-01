#include <chrono>
#include <memory>
#include <cmath>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/int32.hpp"
#include "geometry_msgs/msg/point.hpp"

using std::placeholders::_1;

class StopCommandNode : public rclcpp::Node, public std::enable_shared_from_this<StopCommandNode>
{
public:
  StopCommandNode()
  : Node("stop_command_node")
  {
    target_coords_ = {
      {0.3, 4.3}, {-0.7, 0.9}, {-1.30, -0.90}
    };

    position_subscriber_ = this->create_subscription<geometry_msgs::msg::Point>(
      "location", 10, std::bind(&StopCommandNode::position_callback, this, _1));

    stop_publisher_ = this->create_publisher<std_msgs::msg::Int32>("stop", 10);
    index_publisher_ = this->create_publisher<std_msgs::msg::Int32>("index",10);

    RCLCPP_INFO(this->get_logger(), "StopCommandNode initialized with %zu target waypoints", target_coords_.size());
  }

private:
  void position_callback(const geometry_msgs::msg::Point::SharedPtr msg)
  {
    float x = msg->x;
    float y = msg->y;

    int stop = 0;

    if (current_index_ < target_coords_.size())
    {
      auto [tx, ty] = target_coords_[current_index_];

      double dx = tx - x;
      double dy = ty - y;
      double distance = std::sqrt(dx * dx + dy * dy);

      if (distance < 0.3)
      { 
        stop = 1;
        RCLCPP_INFO(this->get_logger(), "Reached target #%zu: (%.2f, %.2f) with distance %.2f", current_index_, tx, ty, distance);
        current_index_++;
      }
    }
    else
    {
      RCLCPP_INFO(this->get_logger(), "All waypoints reached. Holding final position.");
      stop = 1;
    }
    std_msgs::msg::Int32 index_msg;
    std_msgs::msg::Int32 stop_msg;
    index_msg.data = current_index_;
    stop_msg.data = stop;
    stop_publisher_->publish(stop_msg);
    index_publisher_ -> publish(index_msg);
  }

  rclcpp::Subscription<geometry_msgs::msg::Point>::SharedPtr position_subscriber_;
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr stop_publisher_;
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr index_publisher_;
  std::vector<std::pair<float, float>> target_coords_;
  size_t current_index_ = 0;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<StopCommandNode>());
  rclcpp::shutdown();
  return 0;
}
