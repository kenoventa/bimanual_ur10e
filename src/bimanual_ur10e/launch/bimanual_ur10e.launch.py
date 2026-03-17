#!/usr/bin/env python3
"""
Master launch file for bimanual UR10e.

This file documents the available launch modes. Choose the appropriate mode for your use case:

OFFLINE MODE (recommended for testing without robots):
========================================================
Launch the offline mode with rosbag playback:
  ros2 launch bimanual_ur10e offline.launch.py

Then in another terminal, replay a rosbag:
  ./scripts/replay_rosbag.sh /path/to/rosbag.mcap

Features:
  - No robot hardware required
  - Displays both UR10e robots with rosbag data
  - Uses simulated time from rosbag (use_sim_time=true)
  - Includes joint_state_publisher_gui for visualization


ONLINE MODE (for real robot operation):
=======================================
Launch the online mode when robots are connected:
  ros2 launch bimanual_ur10e online.launch.py \\
    robot1_ip:=192.168.1.100 \\
    robot2_ip:=192.168.1.101

Optional arguments:
  robot1_ip     : IP address of first UR10e (default: 192.168.1.100)
  robot2_ip     : IP address of second UR10e (default: 192.168.1.101)
  use_gui       : Show joint_state_publisher_gui (default: true)
  rviz_config   : Path to RViz config file

Features:
  - Connects to real UR10e robots via drivers
  - Subscribes to real-time joint states
  - Displays both robots synchronized with hardware
  - Uses real time (use_sim_time=false)


URDF AND COORDINATE FRAMES:
==========================
Both modes use the same dual-UR10e URDF:
  - World frame: "world" (common reference)
  - Robot 1: Offset -0.5 m along X, namespace "robot1_"
  - Robot 2: Offset +0.5 m along X, mirrored 180° around Z, namespace "robot2_"

All links and joints are namespaced per robot:
  - robot1_base, robot1_shoulder_link, robot1_wrist_3_link, etc.
  - robot2_base, robot2_shoulder_link, robot2_wrist_3_link, etc.

Joint state topics:
  - /robot1/joint_states (subscribed by aggregator)
  - /robot2/joint_states (subscribed by aggregator)
  - /joint_states (published by aggregator for robot_state_publisher)
"""

from launch import LaunchDescription


def generate_launch_description():
    # This is a documentation file. Users should launch offline.launch.py or online.launch.py directly.
    # Returning empty LaunchDescription to show usage info.
    return LaunchDescription([])

