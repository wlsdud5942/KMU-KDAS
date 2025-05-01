#include <chrono>
#include <memory>
#include "rclcpp/rclcpp.hpp"
#include "rosgraph_msgs/msg/clock.hpp"

using namespace std::chrono_literals;

class SimTimePublisher : public rclcpp::Node
{
public:
    SimTimePublisher() : Node("sim_time_publisher")
    {
        clock_pub_ = this->create_publisher<rosgraph_msgs::msg::Clock>("/clock", 10);
        timer_ = this->create_wall_timer(10ms, std::bind(&SimTimePublisher::publish_time, this));
        RCLCPP_INFO(this->get_logger(), "SimTimePublisher initialized");
    }

private:
    void publish_time()
    {
        current_time_ = current_time_ + rclcpp::Duration(0, 10 * 1000 * 1000);  // 10ms = 10,000,000ns

        rosgraph_msgs::msg::Clock msg;
        msg.clock = current_time_;
        clock_pub_->publish(msg);
    }

    rclcpp::Time current_time_;
    rclcpp::Publisher<rosgraph_msgs::msg::Clock>::SharedPtr clock_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SimTimePublisher>());
    rclcpp::shutdown();
    return 0;
}
