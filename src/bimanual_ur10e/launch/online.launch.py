#!/usr/bin/env python3
"""
Online mode launch file for bimanual UR10e with real robots - SINGLE LAUNCH.

Connects to both UR10e robots via drivers and displays them in RViz simultaneously.
All components start from a single command.

USAGE:
  ros2 launch bimanual_ur10e online.launch.py \\
    robot1_ip:=192.168.1.10 \\
    robot2_ip:=192.168.1.20

The robots publish to /robot1/joint_states and /robot2/joint_states which are
aggregated for visualization. TF frames are prefixed with robot1_ and robot2_.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, OpaqueFunction, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node, PushRosNamespace, SetRemap, SetParameter

def controller_type_params():
    """
    Inject controller type params to all nodes in GroupAction.
    Only controller_manager is using this param
    Type strings is taken from ur_controllers.yaml.
    """
    return [
        SetParameter(name="update_rate", value=500),
        SetParameter(name="joint_state_broadcaster.type",
                     value="joint_state_broadcaster/JointStateBroadcaster"),
        SetParameter(name="io_and_status_controller.type",
                     value="ur_controllers/GPIOController"),
        SetParameter(name="speed_scaling_state_broadcaster.type",
                     value="ur_controllers/SpeedScalingStateBroadcaster"),
        SetParameter(name="force_torque_sensor_broadcaster.type",
                     value="force_torque_sensor_broadcaster/ForceTorqueSensorBroadcaster"),
        SetParameter(name="joint_trajectory_controller.type",
                     value="joint_trajectory_controller/JointTrajectoryController"),
        SetParameter(name="scaled_joint_trajectory_controller.type",
                     value="ur_controllers/ScaledJointTrajectoryController"),
        SetParameter(name="forward_velocity_controller.type",
                     value="velocity_controllers/JointGroupVelocityController"),
        SetParameter(name="forward_effort_controller.type",
                     value="effort_controllers/JointGroupEffortController"),
        SetParameter(name="forward_position_controller.type",
                     value="position_controllers/JointGroupPositionController"),
        SetParameter(name="force_mode_controller.type",
                     value="ur_controllers/ForceModeController"),
        SetParameter(name="freedrive_mode_controller.type",
                     value="ur_controllers/FreedriveModeController"),
        SetParameter(name="passthrough_trajectory_controller.type",
                     value="ur_controllers/PassthroughTrajectoryController"),
        SetParameter(name="tcp_pose_broadcaster.type",
                     value="pose_broadcaster/PoseBroadcaster"),
        SetParameter(name="ur_configuration_controller.type",
                     value="ur_controllers/URConfigurationController"),
        SetParameter(name="tool_contact_controller.type",
                     value="ur_controllers/ToolContactController"),
    ]

def launch_setup(context, *args, **kwargs):
    """Setup function to avoid port binding issues by using different ports for each robot."""
    pkg_share = get_package_share_directory("bimanual_ur10e")
    robot1_ip = LaunchConfiguration("robot1_ip")
    robot2_ip = LaunchConfiguration("robot2_ip")
    rviz_config = LaunchConfiguration("rviz_config")

    # ---------- URDF via xacro ----------
    xacro_file = os.path.join(pkg_share, "urdf", "bimanual_ur10e.urdf.xacro")
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]),
        value_type=str
    )

    # ---------- robot_state_publisher (SINGLE INSTANCE ONLY) ----------
    # Publishes TF frames based on URDF and aggregated joint states
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": False,
            }
        ],
    )

    # ---------- joint_state_publisher (HEADLESS AGGREGATOR ONLY) ----------
    # Subscribes to /robot1/joint_states and /robot2/joint_states
    # Publishes aggregated /joint_states for robot_state_publisher and RViz
    # NO GUI variant - GUI causes conflicts and flickering
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
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

    # ---------- UR Robot Drivers with Namespace Isolation ----------
    # Robot1: Each driver in its own namespace to isolate controller managers
    robot1_ur_driver = GroupAction([
        PushRosNamespace("robot1"),
        SetRemap(src="/tf",        dst="/robot1/tf"),
        SetRemap(src="/tf_static", dst="/robot1/tf_static"),
        *cm_remaps("robot1"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution(
                    [FindPackageShare("ur_robot_driver"), "launch", "ur10e.launch.py"]
                )
            ),
            launch_arguments={
                "robot_ip":                  robot1_ip,
                "use_fake_hardware":         "false",
                "initial_joint_controller":  "scaled_joint_trajectory_controller",
                "activate_joint_controller": "false",
                "headless_mode":             "false",
                "launch_rviz":               "false",
                "tf_prefix":                 "robot1_",
                "namespace":                 "robot1",
                "reverse_port":              "50001",
                "script_command_port":       "50002",
                "trajectory_port":           "50003",
                "script_sender_port":        "50004",
            }.items(),
        ),
    ])

    
#!/usr/bin/env python3
"""
Online mode launch file for bimanual UR10e with real robots - SINGLE LAUNCH.
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


# ─── Helper: list SetRemap for controller_manager services ────────────
def cm_remaps(ns: str):
    """
    Return list of SetRemap actions yang redirect semua /controller_manager/*
    service calls ke /{ns}/controller_manager/*.

    Diperlukan karena spawner di ur_control.launch.py pakai path ABSOLUTE
    '/controller_manager' (bukan relative 'controller_manager').
    """
    services = [
        "list_controllers",
        "load_controller",
        "unload_controller",
        "configure_controller",
        "switch_controller",
        "set_hardware_component_state",
        "list_hardware_interfaces",
        "list_controller_types",
        "reload_controller_libraries",
    ]
    return [
        SetRemap(
            src=f"/controller_manager/{svc}",
            dst=f"/{ns}/controller_manager/{svc}",
        )
        for svc in services
    ]


def launch_setup(context, *args, **kwargs):
    pkg_share  = get_package_share_directory("bimanual_ur10e")
    robot1_ip  = LaunchConfiguration("robot1_ip")
    robot2_ip  = LaunchConfiguration("robot2_ip")
    rviz_config = LaunchConfiguration("rviz_config")

    # ── URDF via xacro ──────────────────────────────────────────────────────
    xacro_file = os.path.join(pkg_share, "urdf", "bimanual_ur10e.urdf.xacro")
    robot_description = ParameterValue(
        Command([FindExecutable(name="xacro"), " ", xacro_file]),
        value_type=str,
    )

    # ── Combined robot_state_publisher  ──────
    # Usw bimanual URDF → publish semua frame robot1_ dan robot2_ ke /tf
    # UR driver RSPs will be redirect to /robot1/tf dan /robot2/tf via SetRemap
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description, "use_sim_time": False}],
    )

    # ── joint_state_publisher aggregator ────────────────────────────────────
    joint_state_publisher_node = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        parameters=[{
            "source_list": [
                "/robot1/joint_states",
                "/robot2/joint_states",
                # joint_state_publisher akan auto-compute SEMUA mimic joints
                # (knuckle, inner finger, outer finger, pad) dari finger_joint position
                "/gripper1/joint_state_broadcaster/joint_states",
                "/gripper2/joint_state_broadcaster/joint_states",
            ],
            "rate": 50,
        }],
    )
    

    # ── joint_state_republisher ─────────────────────────────
    joint_state_republisher_robot1 = Node(
        package="bimanual_ur10e",
        executable="joint_state_republisher.py",
        name="joint_state_republisher_robot1",
        output="screen",
        parameters=[
            {"robot_id": "robot1"},
            {"tf_prefix": "robot1_"},
            {"input_topic": "/robot1/joint_state_broadcaster/state"},
        ],
    )

    joint_state_republisher_robot2 = Node(
        package="bimanual_ur10e",
        executable="joint_state_republisher.py",
        name="joint_state_republisher_robot2",
        output="screen",
        parameters=[
            {"robot_id": "robot2"},
            {"tf_prefix": "robot2_"},
            {"input_topic": "/robot2/joint_state_broadcaster/state"},
        ],
    )

    # ── UR Robot Driver Robot 1 ──────────────────────────────────────────────
    robot1_ur_driver = TimerAction(
        period=0.1,
        actions=[
            GroupAction([
                PushRosNamespace("robot1"),
                SetRemap(src="/tf",        dst="/robot1/tf"),
                SetRemap(src="/tf_static", dst="/robot1/tf_static"),
                *cm_remaps("robot1"),
                *controller_type_params(),    
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution(
                            [FindPackageShare("ur_robot_driver"), "launch", "ur10e.launch.py"]
                        )
                    ),
                    launch_arguments={
                        "robot_ip":                  robot1_ip,
                        "use_fake_hardware":         "false",
                        "initial_joint_controller":  "scaled_joint_trajectory_controller",
                        "activate_joint_controller": "false",
                        "headless_mode":             "false",
                        "launch_rviz":               "false",
                        "tf_prefix":                 "robot1_",
                        "namespace":                 "robot1",
                        "reverse_port":              "50001",
                        "script_command_port":       "50002",
                        "trajectory_port":           "50003",
                        "script_sender_port":        "50004",
                        "controllers_config_file":   os.path.join(pkg_share, "config", "robot1_controllers.yaml"),
                    }.items(),
                ),
            ])
        ]
    )

    # ── UR Robot Driver Robot 2 (delayed 2s) ─────────────────────────────────
    robot2_ur_driver = TimerAction(
        period=2.0,
        actions=[
            GroupAction([
                PushRosNamespace("robot2"),
                SetRemap(src="/tf",        dst="/robot2/tf"),
                SetRemap(src="/tf_static", dst="/robot2/tf_static"),
                *cm_remaps("robot2"),
                *controller_type_params(),     
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution(
                            [FindPackageShare("ur_robot_driver"), "launch", "ur10e.launch.py"]
                        )
                    ),
                    launch_arguments={
                        "robot_ip":                  robot2_ip,
                        "use_fake_hardware":         "false",
                        "initial_joint_controller":  "scaled_joint_trajectory_controller",
                        "activate_joint_controller": "false",
                        "headless_mode":             "false",
                        "launch_rviz":               "false",
                        "tf_prefix":                 "robot2_",
                        "namespace":                 "robot2",
                        "reverse_port":              "50011",
                        "script_command_port":       "50012",
                        "trajectory_port":           "50013",
                        "script_sender_port":        "50014",
                        "controllers_config_file":   os.path.join(pkg_share, "config", "robot2_controllers.yaml"),
                    }.items(),
                ),
            ])
        ]
    )

    # ── RViz ────────────────────────────────────────────────────────────────
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )

    # ─── Gripper descriptions (dari standalone xacro) ────────────────────────────
    gripper1_description = ParameterValue(
        Command([
            FindExecutable(name="xacro"), " ",
            PathJoinSubstitution([
                FindPackageShare("bimanual_ur10e"), "config", "gripper1_standalone.urdf.xacro"
            ])
        ]),
        value_type=str,
    )

    gripper2_description = ParameterValue(
        Command([
            FindExecutable(name="xacro"), " ",
            PathJoinSubstitution([
                FindPackageShare("bimanual_ur10e"), "config", "gripper2_standalone.urdf.xacro"
            ])
        ]),
        value_type=str,
    )

    # ─── Gripper 1 controller_manager ─────────────────────────────────────────────
    # Dedicated CM untuk gripper1 (terpisah dari robot1 CM)
    # Tidak pakai PushRosNamespace karena kita bisa set namespace langsung di Node
    gripper1_cm = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace="gripper1",
        parameters=[{"robot_description": gripper1_description}],
        output="screen",
    )

    # Spawner: joint_state_broadcaster untuk gripper1
    # Absolute path ke /gripper1/controller_manager agar tidak perlu remap
    gripper1_jsb_spawner = TimerAction(
        period=3.0,   # beri waktu CM start + USB init
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "joint_state_broadcaster",
                    "--controller-manager", "/gripper1/controller_manager",
                    "--controller-manager-timeout", "30",
                ],
                output="screen",
            )
        ]
    )

    # ─── Gripper 2 controller_manager ─────────────────────────────────────────────
    gripper2_cm = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace="gripper2",
        parameters=[{"robot_description": gripper2_description}],
        output="screen",
    )

    gripper2_jsb_spawner = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=[
                    "joint_state_broadcaster",
                    "--controller-manager", "/gripper2/controller_manager",
                    "--controller-manager-timeout", "30",
                ],
                output="screen",
            )
        ]
    )
    
    
    return [
        robot_state_publisher_node,       # combined RSP → to /tf
        robot1_ur_driver,                 # robot1 group (TF + CM isolated)
        robot2_ur_driver,                 # robot2 group (TF + CM isolated, delay 2s)
        joint_state_republisher_robot1,   # /robot1/joint_state_broadcaster/state → /robot1/joint_states
        joint_state_republisher_robot2,   # /robot2/joint_state_broadcaster/state → /robot2/joint_states
        joint_state_publisher_node,       # /robot1/joint_states + /robot2/joint_states → /joint_states
        rviz_node,
        gripper1_cm,              # ← gripper1 controller_manager
        gripper1_jsb_spawner,     # ← spawn joint_state_broadcaster setelah 3s
        gripper2_cm,              # ← gripper2 controller_manager
        gripper2_jsb_spawner,     # ← spawn joint_state_broadcaster setelah 3s
    ]


def generate_launch_description():
    pkg_share = get_package_share_directory("bimanual_ur10e")

    # ---------- arguments ----------
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

    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=os.path.join(pkg_share, "config", "bimanual_ur10e.rviz"),
        description="Full path to the RViz config file",
    )

    return LaunchDescription(
        [
            robot1_ip_arg,
            robot2_ip_arg,
            rviz_config_arg,
            OpaqueFunction(function=launch_setup),
        ]
    )


