#!/usr/bin/env python3
"""
Launch file for bimanual Robotiq gripper joint state publisher.

This launch file starts the gripper publisher node that reads gripper positions
from both UR controllers via socket interface (port 63352) and publishes them to
the /gripper1/joint_states and /gripper2/joint_states topics (for aggregation).

Usage:
  ros2 launch bimanual_ur10e gripper_publisher.launch.py \\
    robot1_ip:=192.168.1.10 \\
    robot2_ip:=192.168.1.20
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Generate launch description for bimanual gripper publisher."""
    
    # Declare launch arguments
    robot1_ip_arg = DeclareLaunchArgument(
        "robot1_ip",
        default_value="192.168.1.10",
        description="IP address of Robot 1 UR controller",
    )

    robot2_ip_arg = DeclareLaunchArgument(
        "robot2_ip",
        default_value="192.168.1.20",
        description="IP address of Robot 2 UR controller",
    )

    # Bimanual gripper publisher node
    gripper_publisher_node = Node(
        package="bimanual_ur10e",
        executable="robotiq_gripper_publisher.py",
        name="robotiq_gripper_publisher",
        output="screen",
        parameters=[
            {
                "robot1_ip": LaunchConfiguration("robot1_ip"),
                "robot2_ip": LaunchConfiguration("robot2_ip"),
            }
        ],
    )

    return LaunchDescription([
        robot1_ip_arg,
        robot2_ip_arg,
        gripper_publisher_node,
    ])
