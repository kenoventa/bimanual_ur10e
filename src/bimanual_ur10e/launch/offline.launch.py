#!/usr/bin/env python3
"""
Offline mode launch file for bimanual UR10e with rosbag playback.

Plays back recorded joint states from a rosbag file and displays them in RViz.
No robot drivers or physical hardware required.

Starts:
  - robot_state_publisher with dual-robot URDF
  - RViz2 for visualization
  - Joint state aggregator
  - Optional: rosbag player (launched manually or via replay_rosbag.sh script)

To use:
  1. Start this launch file: ros2 launch bimanual_ur10e offline.launch.py
  2. In another terminal, play the rosbag: ./scripts/replay_rosbag.sh path/to/rosbag
  3. Watch the robots animate in RViz based on recorded data
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
    # Publishes TF transforms based on URDF and joint states from rosbag
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": True,  # Offline mode: use rosbag timestamps
            }
        ],
    )

    # ---------- joint_state_publisher (aggregator) ----------
    # Merges joint states from both robots into /joint_states
    # In offline mode, these come from rosbag playback
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

    # NOTE: Rosbag playback is intentionally NOT launched here.
    # Use the replay_rosbag.sh helper script or 'ros2 bag play' manually:
    #
    #   ./scripts/replay_rosbag.sh path/to/rosbag.mcap
    #
    # The --clock flag in the helper script enables simulated time (use_sim_time=true).

    return LaunchDescription(
        [
            use_gui_arg,
            rviz_config_arg,
            robot_state_publisher_node,
            joint_state_publisher_node,
            joint_state_publisher_gui_node,
            rviz_node,
        ]
    )
