#!/usr/bin/env python3
"""
Replay launch file for the bimanual UR10e setup.

This launch file is intended for offline replay of recorded rosbag data.
It starts:
  - robot_state_publisher (with use_sim_time=true)
  - RViz2 with the pre-configured bimanual display

Run the rosbag replay in a separate terminal using:
  ros2 bag play <bag_directory> --clock

Or use the convenience script at scripts/replay_bag.sh.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("bimanual_ur10e")

    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=os.path.join(pkg_share, "config", "bimanual_ur10e.rviz"),
        description="Full path to the RViz config file",
    )
    rviz_config = LaunchConfiguration("rviz_config")

    xacro_file = os.path.join(pkg_share, "urdf", "bimanual_ur10e.urdf.xacro")
    robot_description = Command([FindExecutable(name="xacro"), " ", xacro_file])

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                # Use simulation time so the replayed /clock drives the TF tree.
                "use_sim_time": True,
            }
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription(
        [
            rviz_config_arg,
            robot_state_publisher_node,
            rviz_node,
        ]
    )
