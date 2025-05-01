cmake_minimum_required(VERSION 3.8)
project(util)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs)
find_package(rosgraph_msgs REQUIRED)
find_package(qcar2_interfaces REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)




# Simulink Bridge
add_executable(simulink_converter_node src/simulinkConverter.cpp)
ament_target_dependencies(simulink_converter_node rclcpp geometry_msgs qcar2_interfaces)
install(TARGETS 
  simulink_converter_node 
  DESTINATION lib/${PROJECT_NAME})

# Cartographer Location
add_executable(current_location src/current_location.cpp)
ament_target_dependencies(current_location rclcpp tf2 tf2_ros tf2_geometry_msgs geometry_msgs)
install(TARGETS
  current_location
  DESTINATION lib/${PROJECT_NAME})

# Sim Time
add_executable(get_sim_time_node src/getSimTime.cpp)
ament_target_dependencies(get_sim_time_node rclcpp std_msgs)
install (TARGETS
  get_sim_time_node
  DESTINATION lib/${PROJECT_NAME})

# clock publisher
add_executable(sim_time_node src/clock.cpp)
ament_target_dependencies(sim_time_node rclcpp rosgraph_msgs)
install(TARGETS
  sim_time_node
  DESTINATION lib/${PROJECT_NAME}
)

#recorder
install(PROGRAMS
  src/savevideo.py
  DESTINATION lib/${PROJECT_NAME}
)  

#recorder AI res
install(PROGRAMS
  src/save_res_video.py
  DESTINATION lib/${PROJECT_NAME}
)

#depth to CSV
install(PROGRAMS
  src/depth_csv.py
  DESTINATION lib/${PROJECT_NAME}
)

#image frame saver
install(PROGRAMS
  src/image_save.py
  DESTINATION lib/${PROJECT_NAME}
)

#depth at pixel
install(PROGRAMS
  src/get_pixel_depth.py
  DESTINATION lib/${PROJECT_NAME}
)

#depth to csv ksm
install(PROGRAMS
  src/depthCSVExport.py
  DESTINATION lib/${PROJECT_NAME}
)

#way point to CSV
install(PROGRAMS
  src/waypointSaver.py
  DESTINATION lib/${PROJECT_NAME}
)

#save each frame
install(PROGRAMS
  src/saveframe.py
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
