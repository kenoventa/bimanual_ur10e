#!/usr/bin/env python3
"""
Online mode launch file for bimanual UR10e with GRIPPER INTEGRATION.

This is the same as online.launch.py but with gripper publisher included.
Connects to both UR10e robots + both Robotiq grippers via socket interface.

USAGE:
  ros2 launch bimanual_ur10e online_with_gripper.launch.py \\
    robot1_ip:=192.168.1.10 \\
    robot2_ip:=192.168.1.20

All gripper and arm data will be aggregated to /joint_states.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace, SetRemap
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def controller_type_params():
    """Inject controller type params to all nodes."""
    return [
        SetRemap(src=f"/controller_manager/{svc}", dst=f"/controller_manager/{svc}")
        for svc in [
            "list_controllers", "load_controller", "unload_controller",
            "configure_controller", "switch_controller",
            "set_hardware_component_state", "list_hardware_interfaces",
            "list_controller_types", "reload_controller_libraries",
        ]
    ]


def cm_remaps(ns: str):
    """Return list of SetRemap for controller_manager services."""
    services = [
        "list_controllers", "load_controller", "unload_controller",
        "configure_controller", "switch_controller",
        "set_hardware_component_state", "list_hardware_interfaces",
        "list_controller_types", "reload_controller_libraries",
    ]
    return [
        SetRemap(src=f"/controller_manager/{svc}", dst=f"/{ns}/controller_manager/{svc}")
        for svc in services
    ]


def launch_setup(context, *args, **kwargs):
    """Setup function for bimanual + gripper launch."""
    pkg_share = get_package_share_directory("bimanual_ur10e")
    robot1_ip = LaunchConfiguration("robot1_ip")
    robot2_ip = LaunchConfiguration("robot2_ip")
    rviz_config = LaunchConfiguration("rviz_config")

    # ── URDF via xacro ──
    xacro_file = os.path.join(pkg_share, "urdf", "bimanual_ur10e.urdf.xacro")
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]),
        value_type=str,
    )

    # ── robot_state_publisher ──
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description, "use_sim_time": False}],
    )

    # ── joint_state_publisher aggregator (UPDATED TO INCLUDE GRIPPER) ──
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        parameters=[{
            "source_list": [
                "/robot1/joint_states",
                "/robot2/joint_states",
                "/gripper1/joint_state_broadcaster/joint_states",
                "/gripper2/joint_state_broadcaster/joint_states",
            ],
            "rate": 50,
        }],
    )

    # ── UR Robot Driver Robot 1 ──
    robot1_ur_driver = TimerAction(
        period=0.1,
        actions=[
            GroupAction([
                PushRosNamespace("robot1"),
                SetRemap(src="/tf", dst="/robot1/tf"),
                SetRemap(src="/tf_static", dst="/robot1/tf_static"),
                *cm_remaps("robot1"),
                *controller_type_params(),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([FindPackageShare("ur_robot_driver"), "launch", "ur10e.launch.py"])
                    ),
                    launch_arguments={
                        "robot_ip": robot1_ip,
                        "use_fake_hardware": "false",
                        "initial_joint_controller": "scaled_joint_trajectory_controller",
                        "activate_joint_controller": "false",
                        "headless_mode": "false",
                        "launch_rviz": "false",
                        "tf_prefix": "robot1_",
                        "namespace": "robot1",
                        "reverse_port": "50001",
                        "script_command_port": "50002",
                        "trajectory_port": "50003",
                        "script_sender_port": "50004",
                        "controllers_config_file": os.path.join(pkg_share, "config", "robot1_controllers.yaml"),
                    }.items(),
                ),
            ])
        ]
    )

    # ── UR Robot Driver Robot 2 ──
    robot2_ur_driver = TimerAction(
        period=2.0,
        actions=[
            GroupAction([
                PushRosNamespace("robot2"),
                SetRemap(src="/tf", dst="/robot2/tf"),
                SetRemap(src="/tf_static", dst="/robot2/tf_static"),
                *cm_remaps("robot2"),
                *controller_type_params(),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([FindPackageShare("ur_robot_driver"), "launch", "ur10e.launch.py"])
                    ),
                    launch_arguments={
                        "robot_ip": robot2_ip,
                        "use_fake_hardware": "false",
                        "initial_joint_controller": "scaled_joint_trajectory_controller",
                        "activate_joint_controller": "false",
                        "headless_mode": "false",
                        "launch_rviz": "false",
                        "tf_prefix": "robot2_",
                        "namespace": "robot2",
                        "reverse_port": "50011",
                        "script_command_port": "50012",
                        "trajectory_port": "50013",
                        "script_sender_port": "50014",
                        "controllers_config_file": os.path.join(pkg_share, "config", "robot2_controllers.yaml"),
                    }.items(),
                ),
            ])
        ]
    )

    # ── Gripper Publisher (BIMANUAL) ── ✅ NEW
    gripper_publisher_node = Node(
        package="bimanual_ur10e",
        executable="robotiq_gripper_publisher.py",
        name="robotiq_gripper_publisher",
        output="screen",
        parameters=[{
            "robot1_ip": robot1_ip,
            "robot2_ip": robot2_ip,
        }],
    )

    # ── RViz ──
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )

    return [
        robot_state_publisher_node,
        robot1_ur_driver,
        robot2_ur_driver,
        gripper_publisher_node,  # ← Gripper publisher
        joint_state_publisher_node,
        rviz_node,
    ]


def generate_launch_description():
    """Generate launch description."""
    pkg_share = get_package_share_directory("bimanual_ur10e")

    return LaunchDescription([
        DeclareLaunchArgument("robot1_ip", default_value="192.168.1.10"),
        DeclareLaunchArgument("robot2_ip", default_value="192.168.1.20"),
        DeclareLaunchArgument(
            "rviz_config",
            default_value=os.path.join(pkg_share, "config", "rviz.rviz"),
        ),
        OpaqueFunction(function=launch_setup),
    ])
