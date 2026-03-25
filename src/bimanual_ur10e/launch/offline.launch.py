#!/usr/bin/env python3
"""
Offline mode launch file for bimanual UR10e with rosbag playback - WITH GRIPPERS.

Plays back recorded joint states from a rosbag file and displays them in RViz.
No robot drivers or physical hardware required.

Includes dual Robotiq 2F140 grippers attached to both end effectors.
Gripper visualization and states are aggregated from rosbag or simulated.

Starts:
  - robot_state_publisher with dual-robot URDF (includes grippers)
  - RViz2 for visualization (shows arms + grippers)
  - Joint state aggregator (arm joints from /robot{1,2}/joint_states)
  - Gripper state aggregator (gripper joints from rosbag or simulator)
  - Gripper state publisher (simulated gripper states for testing)
  - Optional: rosbag player (launched manually or via replay_rosbag.sh script)

To use:
  1. Start this launch file: ros2 launch bimanual_ur10e offline.launch.py
  2. In another terminal, play the rosbag: ./scripts/replay_rosbag.sh path/to/rosbag
  3. Watch the robots AND grippers animate in RViz based on recorded data

Gripper Configuration:
  - Gripper 1: Attached to robot1_tool0 (left arm end effector)
  - Gripper 2: Attached to robot2_tool0 (right arm end effector)
  - Joint names: gripper{1,2}_finger_{left,right}_joint
  - Visualized via RViz with gripper meshes
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

    enable_aggregator_arg = DeclareLaunchArgument(
        "enable_aggregator",
        default_value="true",
        description="Enable joint state aggregator (disable for rosbag playback)",
    )
    enable_aggregator = LaunchConfiguration("enable_aggregator")

    # ---------- URDF via xacro ----------
    xacro_file = os.path.join(pkg_share, "urdf", "bimanual_ur10e.urdf.xacro")
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]),
        value_type=str
    )

    # ---------- robot_state_publisher ----------
    # Publishes TF transforms based on URDF and joint states from rosbag
    # URDF includes: both UR10e arms + Robotiq 2F140 grippers
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
    # Merges arm joint states from both robots into /joint_states
    # Sources: /robot1/joint_states and /robot2/joint_states (from rosbag)

    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        condition=IfCondition(enable_aggregator),
        parameters=[
            {
                "source_list": [
                    "/robot1/joint_states",
                    "/robot2/joint_states",
                ],
                "rate": 50,
                "use_sim_time": True,  # Sync with rosbag timestamps
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
                "use_mimic_joints": True,
                "zeros": { #starting pose
                    "robot1_shoulder_pan_joint": 0.0,
                    "robot1_shoulder_lift_joint": -1.57,  # -90 degrees
                    "robot1_elbow_joint": 1.57,           # 90 degrees
                    "robot1_wrist_1_joint": 0.0,
                    "robot1_wrist_2_joint": 0.0,
                    "robot1_wrist_3_joint": 0.0,
                    "gripper1_finger_joint": 0.0,
                    "robot2_shoulder_pan_joint": 0.0,
                    "robot2_shoulder_lift_joint": -1.57,  # -90
                    "robot2_elbow_joint": 1.57,           # 90 degrees
                    "robot2_wrist_1_joint": 0.0,
                    "robot2_wrist_2_joint": 0.0,
                    "robot2_wrist_3_joint": 0.0,
                    "gripper2_finger_joint": 0.0,
                }
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
            enable_aggregator_arg,
            robot_state_publisher_node,
            joint_state_publisher_node,
            joint_state_publisher_gui_node,
            rviz_node,
        ]
    )
