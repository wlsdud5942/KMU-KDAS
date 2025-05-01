#include "rclcpp/rclcpp.hpp"
#include "qcar2_interfaces/msg/motor_commands.hpp"
#include "qcar2_interfaces/msg/boolean_leds.hpp"

#include <termios.h>
#include <unistd.h>
#include <fcntl.h>
#include <iostream>

class KeyboardController : public rclcpp::Node
{
public:
    KeyboardController() : Node("keyboard_qcar_controller"), throttle(0.0), steering(0.0)
    {
        command_publisher_ = this->create_publisher<qcar2_interfaces::msg::MotorCommands>("qcar2_motor_speed_cmd", 10);
        led_publisher_ = this->create_publisher<qcar2_interfaces::msg::BooleanLeds>("qcar2_led_cmd", 10);

        set_nonblocking_input(); // non-blocking terminal input

        timer_ = this->create_wall_timer(std::chrono::milliseconds(100), std::bind(&KeyboardController::control_loop, this));
    }

    ~KeyboardController() {
        reset_terminal();
    }

private:
    void set_nonblocking_input()
    {
        tcgetattr(STDIN_FILENO, &original_termios);
        struct termios new_termios = original_termios;
        new_termios.c_lflag &= ~(ICANON | ECHO); // turn off canonical mode and echo
        tcsetattr(STDIN_FILENO, TCSANOW, &new_termios);

        // set stdin non-blocking
        fcntl(STDIN_FILENO, F_SETFL, O_NONBLOCK);
    }

    void reset_terminal()
    {
        tcsetattr(STDIN_FILENO, TCSANOW, &original_termios);
    }

    void control_loop()
    {
        char c;
        if (read(STDIN_FILENO, &c, 1) > 0) {
            switch (c)
            {
                case 'w': throttle += 0.1; break;
                case 's': throttle -= 0.1; break;
                case 'a': steering += 0.05; break;
                case 'd': steering -= 0.05; break;
                case ' ': throttle = 0.0; steering = 0.0; break; // space to reset
                case 'q': rclcpp::shutdown(); break;
                default: break;
            }

            throttle = std::clamp(throttle, -1.0, 1.0);
            steering = std::clamp(steering, -1.0, 1.0);
        }

        // Send motor command
        auto msg = qcar2_interfaces::msg::MotorCommands();
        msg.motor_names = {"steering_angle", "motor_throttle"};
        msg.values = {steering, throttle};
        command_publisher_->publish(msg);

        // (Optional) LED logic
        auto leds = qcar2_interfaces::msg::BooleanLeds();
        leds.led_names = {"left_outside_headlight", "right_outside_headlight"};
        leds.values = {false, false};
        led_publisher_->publish(leds);
    }

    rclcpp::Publisher<qcar2_interfaces::msg::MotorCommands>::SharedPtr command_publisher_;
    rclcpp::Publisher<qcar2_interfaces::msg::BooleanLeds>::SharedPtr led_publisher_;
    rclcpp::TimerBase::SharedPtr timer_;

    double throttle;
    double steering;
    struct termios original_termios;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<KeyboardController>());
    rclcpp::shutdown();
    return 0;
}