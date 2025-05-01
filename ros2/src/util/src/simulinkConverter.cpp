#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/point.hpp"
#include "qcar2_interfaces/msg/motor_commands.hpp"  // Include the header for MotorCommands

class SimulinkOutSubscriber : public rclcpp::Node
{
public:
  SimulinkOutSubscriber()
  : Node("simulink_out_subscriber"),
    throttle(0.0),
    steering_angle(0.0)
  {
    // Subscribe to /simulinkOut topic expecting Point messages
    subscription_ = this->create_subscription<geometry_msgs::msg::Point>(
      "/simulinkOut",
      100,
      std::bind(&SimulinkOutSubscriber::topic_callback, this, std::placeholders::_1)
    );

    // Create a publisher for MotorCommands messages on the "motor_commands" topic
    command_publisher_ = this->create_publisher<qcar2_interfaces::msg::MotorCommands>(
      "/qcar2_motor_speed_cmd", 100
    );
  }

private:
  double throttle;
  double steering_angle;

  void topic_callback(const geometry_msgs::msg::Point::SharedPtr msg)
  { 

    // Update member variables with incoming message values.
    throttle = msg->x;
    steering_angle = msg->y;
    //RCLCPP_INFO(this->get_logger(), "Received: throttle = %f, steering = %f", throttle, steering_angle);

    // Create and fill a MotorCommands message.
    auto msgOut = qcar2_interfaces::msg::MotorCommands();
    msgOut.motor_names = {"steering_angle", "motor_throttle"};
    msgOut.values = {steering_angle, throttle};
    
    // Publish the motor commands message.
    command_publisher_->publish(msgOut);
  }

  // Subscription to /simulinkOut
  rclcpp::Subscription<geometry_msgs::msg::Point>::SharedPtr subscription_;
  // Publisher for qcar2_interfaces MotorCommands
  rclcpp::Publisher<qcar2_interfaces::msg::MotorCommands>::SharedPtr command_publisher_;

  // Member variables updated from the Point message.

};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<SimulinkOutSubscriber>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
