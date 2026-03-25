#!/usr/bin/env python3
"""
move_to_pregrasp.launch.py

Launch file for moving robots to pre-grasp position before cable picking.

Usage:
  ros2 launch bimanual_ur10e move_to_pregrasp.launch.py robot:=1 duration:=3.0
  
Arguments:
  - robot:   Which robot to move [1, 2, both] (default: both)
  - duration: Motion duration in seconds (default: 5.0)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_share = get_package_share_directory("bimanual_ur10e")
    scripts_dir = os.path.join(pkg_share, "scripts")

    # Arguments
    robot_arg = DeclareLaunchArgument(
        "robot",
        default_value="both",
        description="Which robot(s) to move: 1, 2, or both",
    )
    robot = LaunchConfiguration("robot")

    duration_arg = DeclareLaunchArgument(
        "duration",
        default_value="5.0",
        description="Motion duration in seconds",
    )
    duration = LaunchConfiguration("duration")

    # Move to pregrasp using ExecuteProcess (for non-ROS2 scripts)
    # ExecuteProcess doesn't add ROS-specific arguments, unlike Node()
    move_to_pregrasp_cmd = ExecuteProcess(
        cmd=[
            "python3",
            os.path.join(scripts_dir, "move_to_pregrasp.py"),
            "--robot", robot,
            "--duration", duration,
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            robot_arg,
            duration_arg,
            move_to_pregrasp_cmd,
        ]
    )
