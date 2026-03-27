cmake_minimum_required(VERSION 3.8)
project(bimanual_ur10e)

find_package(ament_cmake REQUIRED)

# Install folders (launch, urdf, config)
install(
  DIRECTORY launch urdf config
  DESTINATION share/${PROJECT_NAME}
)

# Install Python scripts as executables
install(
  PROGRAMS
    scripts/joint_state_publisher.py
    scripts/joint_state_republisher.py
    scripts/move_to_pregrasp.py
    scripts/move_to_pregrasp_rtde.py
    scripts/robotiq_gripper_publisher.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()