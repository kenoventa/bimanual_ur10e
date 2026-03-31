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
        description="IP address of robot1 (UR10e left)",
    )

    robot2_ip_arg = DeclareLaunchArgument(
        "robot2_ip",
        default_value="192.168.1.20",
        description="IP address of robot2 (UR10e right)",
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
    # Delay 5s agar robot driver sudah siap sebelum gripper publisher mencoba connect
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
#     robot1_ur_driver = TimerAction(
#         period=0.1,
#         actions=[
#             GroupAction([
#                 PushRosNamespace("robot1"),
#                 SetRemap(src="/tf", dst="/robot1/tf"),
#                 SetRemap(src="/tf_static", dst="/robot1/tf_static"),
#                 *cm_remaps("robot1"),
#                 *controller_type_params(),
#                 IncludeLaunchDescription(
#                     PythonLaunchDescriptionSource(
#                         PathJoinSubstitution([FindPackageShare("ur_robot_driver"), "launch", "ur10e.launch.py"])
#                     ),
#                     launch_arguments={
#                         "robot_ip": robot1_ip,
#                         "use_fake_hardware": "false",
#                         "initial_joint_controller": "scaled_joint_trajectory_controller",
#                         "activate_joint_controller": "false",
#                         "headless_mode": "false",
#                         "launch_rviz": "false",
#                         "tf_prefix": "robot1_",
#                         "namespace": "robot1",
#                         "reverse_port": "50001",
#                         "script_command_port": "50002",
#                         "trajectory_port": "50003",
#                         "script_sender_port": "50004",
#                         "controllers_config_file": os.path.join(pkg_share, "config", "robot1_controllers.yaml"),
#                     }.items(),
#                 ),
#             ])
#         ]
#     )

#     # ── UR Robot Driver Robot 2 ──
#     robot2_ur_driver = TimerAction(
#         period=2.0,
#         actions=[
#             GroupAction([
#                 PushRosNamespace("robot2"),
#                 SetRemap(src="/tf", dst="/robot2/tf"),
#                 SetRemap(src="/tf_static", dst="/robot2/tf_static"),
#                 *cm_remaps("robot2"),
#                 *controller_type_params(),
#                 IncludeLaunchDescription(
#                     PythonLaunchDescriptionSource(
#                         PathJoinSubstitution([FindPackageShare("ur_robot_driver"), "launch", "ur10e.launch.py"])
#                     ),
#                     launch_arguments={
#                         "robot_ip": robot2_ip,
#                         "use_fake_hardware": "false",
#                         "initial_joint_controller": "scaled_joint_trajectory_controller",
#                         "activate_joint_controller": "false",
#                         "headless_mode": "false",
#                         "launch_rviz": "false",
#                         "tf_prefix": "robot2_",
#                         "namespace": "robot2",
#                         "reverse_port": "50011",
#                         "script_command_port": "50012",
#                         "trajectory_port": "50013",
#                         "script_sender_port": "50014",
#                         "controllers_config_file": os.path.join(pkg_share, "config", "robot2_controllers.yaml"),
#                     }.items(),
#                 ),
#             ])
#         ]
#     )

#     # ── Gripper Publisher (BIMANUAL) ── ✅ NEW
#     gripper_publisher_node = Node(
#         package="bimanual_ur10e",
#         executable="robotiq_gripper_publisher.py",
#         name="robotiq_gripper_publisher",
#         output="screen",
#         parameters=[{
#             "robot1_ip": robot1_ip,
#             "robot2_ip": robot2_ip,
#         }],
#     )

#     # ── RViz ──
#     rviz_node = Node(
#         package="rviz2",
#         executable="rviz2",
#         name="rviz2",
#         output="screen",
#         arguments=["-d", rviz_config],
#     )

#     return [
#         robot_state_publisher_node,
#         robot1_ur_driver,
#         robot2_ur_driver,
#         gripper_publisher_node,  # ← Gripper publisher
#         joint_state_publisher_node,
#         rviz_node,
#     ]


# def generate_launch_description():
#     """Generate launch description."""
#     pkg_share = get_package_share_directory("bimanual_ur10e")

#     return LaunchDescription([
#         DeclareLaunchArgument("robot1_ip", default_value="192.168.1.10"),
#         DeclareLaunchArgument("robot2_ip", default_value="192.168.1.20"),
#         DeclareLaunchArgument(
#             "rviz_config",
#             default_value=os.path.join(pkg_share, "config", "rviz.rviz"),
#         ),
#         OpaqueFunction(function=launch_setup),
#     ])
