#!/usr/bin/env python3
"""
Online mode launch file for bimanual UR10e with real robots.

Connects to two UR10e robots via drivers and displays them in RViz.
Requires physical UR10e robots to be accessible.

Starts:
  - robot_state_publisher with dual-robot URDF
  - RViz2 for visualization
  - Joint state aggregator
  - Optional: UR robot drivers (placeholder for actual driver connection)
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory("bimanual_ur10e")

    # ---------- arguments ----------
    use_gui_arg = DeclareLaunchArgument(
        "use_gui",
        default_value="true",
        description="Start the joint_state_publisher_gui instead of the headless one",
    )
    use_gui = LaunchConfiguration("use_gui")

    robot1_ip_arg = DeclareLaunchArgument(
        "robot1_ip",
        default_value="192.168.1.20",
        description="IP address of robot1 (UR10e left)",
    )
    robot1_ip = LaunchConfiguration("robot1_ip")

    robot2_ip_arg = DeclareLaunchArgument(
        "robot2_ip",
        default_value="192.168.1.10",
        description="IP address of robot2 (UR10e right)",
    )
    robot2_ip = LaunchConfiguration("robot2_ip")

    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=os.path.join(pkg_share, "config", "bimanual_ur10e.rviz"),
        description="Full path to the RViz config file",
    )
    rviz_config = LaunchConfiguration("rviz_config")

    # ---------- URDF via xacro ----------
    xacro_file = os.path.join(pkg_share, "urdf", "bimanual_ur10e.urdf.xacro")
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]),
        value_type=str
    )

    # ---------- robot_state_publisher ----------
    # Publishes TF transforms based on URDF and joint states
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": False,  # Online mode: real-time
            }
        ],
    )

    # ---------- joint_state_publisher (aggregator) ----------
    # Merges joint states from both robots into /joint_states
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        condition=UnlessCondition(use_gui),
        parameters=[
            {
                "source_list": [
                    "/robot1/joint_states",
                    "/robot2/joint_states",
                ],
                "rate": 50,
            }
        ],
    )

    joint_state_publisher_gui_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
        condition=IfCondition(use_gui),
        parameters=[
            {
                "source_list": [
                    "/robot1/joint_states",
                    "/robot2/joint_states",
                ],
                "rate": 50,
            }
        ],
    )

    # ---------- RViz ----------
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )

    # NOTE: Actual UR driver nodes would be launched here.
    # For example (if using ur_robot_driver):
    #   - ur_robot_driver for robot1 (connects to robot1_ip)
    #   - ur_robot_driver for robot2 (connects to robot2_ip)
    # Each driver would publish to its namespaced /robot{n}/joint_states topic.

    return LaunchDescription(
        [
            use_gui_arg,
            robot1_ip_arg,
            robot2_ip_arg,
            rviz_config_arg,
            robot_state_publisher_node,
            joint_state_publisher_node,
            joint_state_publisher_gui_node,
            rviz_node,
        ]
    )
