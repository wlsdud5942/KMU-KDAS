cmake_minimum_required(VERSION 3.8)
project(path_planning)

# Use C++17
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(qcar2_interfaces REQUIRED)

# Install Python scripts
install(PROGRAMS
  src/path_sender.py
  DESTINATION lib/${PROJECT_NAME}
)

# C++ executable for stopper
add_executable(stopper src/stopper.cpp)
ament_target_dependencies(stopper
  rclcpp
  std_msgs
  geometry_msgs
  qcar2_interfaces
)
install(TARGETS
  stopper
  DESTINATION lib/${PROJECT_NAME}
)

#waypoints
install(DIRECTORY config
  DESTINATION share/${PROJECT_NAME}
)

# Lint and test
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_cpplint_FOUND TRUE)
  set(ament_cmake_copyright_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

