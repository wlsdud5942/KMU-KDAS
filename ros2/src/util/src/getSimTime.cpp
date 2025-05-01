#include <chrono> 
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/float64.hpp"

class SimTimePublisher : public rclcpp::Node
{
public:
    SimTimePublisher()
    : Node("sim_time_publisher")
    {
        // Publisher to /sim_time topic
        sim_time_pub_ = this->create_publisher<std_msgs::msg::Float64>("sim_time", 10);

        // Timer for periodic publishing
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&SimTimePublisher::publishSimTime, this)
        );
        RCLCPP_INFO(this->get_logger(), "SimTimePublisher node has been started (ms)");
    }

private:
    void publishSimTime()
    {
        // Get current simulation time (not wall time)
        rclcpp::Time now = this->get_clock()->now();

        auto msg = std_msgs::msg::Float64();
        msg.data = now.seconds();

        sim_time_pub_->publish(msg);
    }

    rclcpp::Publisher<std_msgs::msg::Float64>::SharedPtr sim_time_pub_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SimTimePublisher>());
    rclcpp::shutdown();
    return 0;
}
