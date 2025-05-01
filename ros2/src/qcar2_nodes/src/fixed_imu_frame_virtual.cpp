#include <chrono>
#include <functional>
#include <memory>

#include "geometry_msgs/msg/transform_stamped.hpp"
#include "rclcpp/rclcpp.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_ros/transform_broadcaster.h"

using namespace std::chrono_literals;

class IMUFrameBroadcaster : public rclcpp::Node
{
public:
  IMUFrameBroadcaster()
  : Node("imu_frame_broadcaster")
  {
    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
    timer_ = this->create_wall_timer(
      100ms, std::bind(&IMUFrameBroadcaster::broadcast_timer_callback, this));
  }

private:
  void broadcast_timer_callback()
  {
    geometry_msgs::msg::TransformStamped t;

    t.header.stamp = this->get_clock()->now();
    t.header.frame_id = "base_link";    // parent
    t.child_frame_id = "base_imu";      // child

    // Corrected transform offset
    t.transform.translation.x = 1.4;
    t.transform.translation.y = 0.0;
    t.transform.translation.z = 0.0;

    // No rotation
    tf2::Quaternion q;
    q.setRPY(0.0, 0.0, 0.0);
    t.transform.rotation.x = q.x();
    t.transform.rotation.y = q.y();
    t.transform.rotation.z = q.z();
    t.transform.rotation.w = q.w();

    tf_broadcaster_->sendTransform(t);
  }

  rclcpp::TimerBase::SharedPtr timer_;
  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<IMUFrameBroadcaster>());
  rclcpp::shutdown();
  return 0;
}
