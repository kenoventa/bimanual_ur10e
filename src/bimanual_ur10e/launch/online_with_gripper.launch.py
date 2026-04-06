#!/usr/bin/env python3
"""
Online mode launch file for bimanual UR10e with GRIPPER INTEGRATION.

Combines:
1. online.launch.py - UR10e robot drivers + RViz
2. gripper_publisher.launch.py - Robotiq gripper publisher

USAGE:
  ros2 launch bimanual_ur10e online_with_gripper.launch.py \\
    robot1_ip:=192.168.1.10 \\
    robot2_ip:=192.168.1.20

All arm and gripper data aggregated to /joint_states.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Generate combined online + gripper launch."""
    
    # ──────── Launch Arguments ────────
    robot1_ip_arg = DeclareLaunchArgument(
        "robot1_ip",
        default_value="192.168.1.10",
        description="IP address of robot1 (UR10e right)",
    )

    robot2_ip_arg = DeclareLaunchArgument(
        "robot2_ip",
        default_value="192.168.1.20",
        description="IP address of robot2 (UR10e left)",
    )

    # ──────── Get package share directory ────────
    pkg_share = FindPackageShare("bimanual_ur10e")

    # ──────── Include online.launch.py (UR drivers + RViz) ────────
    online_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([pkg_share, "launch", "online.launch.py"])
        ),
        launch_arguments={
            "robot1_ip": LaunchConfiguration("robot1_ip"),
            "robot2_ip": LaunchConfiguration("robot2_ip"),
        }.items(),
    )

    # ──────── Include gripper_publisher.launch.py (delayed 5s) ────────
    gripper_launch = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([pkg_share, "launch", "gripper_publisher.launch.py"])
                ),
                launch_arguments={
                    "robot1_ip": LaunchConfiguration("robot1_ip"),
                    "robot2_ip": LaunchConfiguration("robot2_ip"),
                }.items(),
            )
        ]
    )

    # ──────── Return combined launch description ────────
    return LaunchDescription([
        robot1_ip_arg,
        robot2_ip_arg,
        online_launch,
        gripper_launch,
    ])
