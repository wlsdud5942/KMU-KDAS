#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/pose_with_covariance_stamped.hpp"
#include "tf2/LinearMath/Quaternion.h"  // Add this for quaternion support

using std::placeholders::_1;
using namespace std::chrono_literals;

class InitialPosePublisher : public rclcpp::Node
{
public:
    InitialPosePublisher()
    : Node("initial_pose_publisher"), published_(false)
    {
        publisher_ = this->create_publisher<geometry_msgs::msg::PoseWithCovarianceStamped>("/initialpose", 10);

        // Wait 2 seconds before publishing
        timer_ = this->create_wall_timer(2s, std::bind(&InitialPosePublisher::timer_callback, this));
    }

private:
    void timer_callback()
    {
        if (published_)
            return;

        auto msg = geometry_msgs::msg::PoseWithCovarianceStamped();
        msg.header.frame_id = "map";
        msg.header.stamp = this->get_clock()->now();

        // Set position
        msg.pose.pose.position.x = -1.5;
        msg.pose.pose.position.y = -0.7;
        msg.pose.pose.position.z = 0.0;

        // Convert yaw = 2.3 radians to quaternion
        double yaw = -0.8;
        tf2::Quaternion q;
        q.setRPY(0, 0, yaw);

        msg.pose.pose.orientation.x = q.x();
        msg.pose.pose.orientation.y = q.y();
        msg.pose.pose.orientation.z = q.z();
        msg.pose.pose.orientation.w = q.w();

        // Covariance (minimal example with diagonal values)
        for (int i = 0; i < 36; ++i)
            msg.pose.covariance[i] = 0.0;
        msg.pose.covariance[0] = 0.25;
        msg.pose.covariance[7] = 0.25;
        msg.pose.covariance[35] = 0.0685;

        publisher_->publish(msg);
        RCLCPP_INFO(this->get_logger(), "Published initial pose to /initialpose");
        published_ = true;
    }

    rclcpp::Publisher<geometry_msgs::msg::PoseWithCovarianceStamped>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    bool published_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<InitialPosePublisher>());
    rclcpp::shutdown();
    return 0;
}
