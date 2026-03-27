#!/usr/bin/env python3
"""
move_to_pregrasp_rtde.py

Move dual UR10e robots to pre-grasp position using RTDE (Real-Time Data Exchange).

Requirements:
  pip install ur-rtde

Usage:
  python3 move_to_pregrasp_rtde.py [--config CONFIG_FILE] [--robot ROBOT] [--duration SECONDS]

Example:
  python3 move_to_pregrasp_rtde.py --config ur_robots.yaml --robot both --duration 5.0
  python3 move_to_pregrasp_rtde.py --robot left --duration 3.0
  python3 move_to_pregrasp_rtde.py --robot right --duration 3.0
"""

import argparse
import math
import time
import yaml
from pathlib import Path

import rclpy
from rclpy.node import Node

try:
    from rtde_control import RTDEControlInterface
    from rtde_receive import RTDEReceiveInterface
except ImportError:
    print("ERROR: ur-rtde library not found!")
    print("Install with: pip install ur-rtde")
    exit(1)


# Home position (all zeros)
HOME_POSE = [0.0, -math.pi / 2, 0.0, -math.pi / 2, 0.0, 0.0]

# Pre-grasp position: Ready to approach cable from above
PREGRASP_POSE_LEFT = [
    0.0,                    # shoulder_pan_joint
    -math.pi / 2,          # shoulder_lift_joint
    0.0,                   # elbow_joint
    -math.pi / 2,          # wrist_1_joint
    0.0,                   # wrist_2_joint
    0.0,                   # wrist_3_joint
]

PREGRASP_POSE_RIGHT = [
    0.0,                    # shoulder_pan_joint
    -math.pi / 2,          # shoulder_lift_joint
    0.0,                   # elbow_joint
    -math.pi / 2,          # wrist_1_joint
    0.0,                   # wrist_2_joint
    0.0,                   # wrist_3_joint
]


class URRTDEController:
    """Controller for UR robot using RTDE protocol."""

    def __init__(self, robot_ip, frequency=500):
        """
        Initialize RTDE connection.
        
        Args:
            robot_ip: IP address robot (e.g., "192.168.1.100")
            frequency: RTDE frequency (default 500 Hz - UR default)
        """
        self.robot_ip = robot_ip
        self.frequency = frequency
        
        print(f"[RTDE] Connecting to UR robot at {robot_ip}...")
        
        try:
            self.rtde_c = RTDEControlInterface(robot_ip)
            self.rtde_r = RTDEReceiveInterface(robot_ip)
            print(f"[RTDE] Successfully connected to {robot_ip}")
        except Exception as e:
            print(f"[ERROR] Failed to connect to {robot_ip}: {e}")
            raise

    def get_current_pose(self):
        """Get current joint positions dari robot."""
        try:
            return list(self.rtde_r.getActualQ())
        except Exception as e:
            print(f"[ERROR] Failed to read joint positions: {e}")
            return None

    def move_to_pose(self, target_pose, speed=1.0, acceleration=1.2, duration_sec=5.0):
        """
        Args:
            target_pose: List of 6 joint angles (radians)
            speed: Speed (rad/s) - default 1.0
            acceleration: Acceleration (rad/s²) - default 1.2
            duration_sec: Approximate motion duration (seconds)
        """
        current = self.get_current_pose()
        if current is None:
            print("[ERROR] Could not get current pose")
            return False

        print(f"[MOTION] Moving to target pose...")
        print(f"  Current:  {[f'{x:.3f}' for x in current]}")
        print(f"  Target:   {[f'{x:.3f}' for x in target_pose]}")
        print(f"  Duration: {duration_sec}s")

        try:
            # moveJ = move with joint interpolation (smooth curve through joint space)
            self.rtde_c.moveJ(target_pose, speed, acceleration)
            
            # Monitor motion until finished or timeout
            start_time = time.time()
            while not self.rtde_c.isSteady() and (time.time() - start_time) < (duration_sec + 5):
                time.sleep(0.1)
            
            print("[MOTION] Motion complete!")
            return True

        except Exception as e:
            print(f"[ERROR] Motion failed: {e}")
            return False

    def move_to_home(self):
        """Move ke home position."""
        return self.move_to_pose(HOME_POSE, duration_sec=5.0)

    def move_to_pregrasp(self, robot_side="left", duration_sec=5.0):
        """Move ke pre-grasp position."""
        pose = PREGRASP_POSE_LEFT if robot_side == "left" else PREGRASP_POSE_RIGHT
        return self.move_to_pose(pose, duration_sec=duration_sec)

    def disconnect(self):
        """Gracefully disconnect dari robot."""
        try:
            self.rtde_c.disconnect()
            self.rtde_r.disconnect()
            print("[RTDE] Disconnected")
        except:
            pass


class MoveToPreGraspRTDENode(Node):

    def __init__(self, config_file=None):
        super().__init__("move_to_pregrasp_rtde")
        
        # Load configuration
        self.config = self.load_config(config_file)
        self.robot_left_controller = None
        self.robot_right_controller = None

    def load_config(self, config_file=None):
        """Load configuration dari YAML file."""
        if config_file is None:
            config_file = Path(__file__).parent.parent / "config" / "ur_robots.yaml"
        
        if not Path(config_file).exists():
            print(f"[WARNING] Config file not found: {config_file}")
            print("[WARNING] Using default IPs...")
            return {
                "left": {"ip": "192.168.1.10", "name": "left"},
                "right": {"ip": "192.168.1.20", "name": "right"},
            }
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            print(f"[CONFIG] Loaded from {config_file}")
            return config
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            return None

    def connect_robots(self, robot_list):
        """Connect ke specified robots."""
        if "left" in robot_list or "both" in robot_list:
            try:
                left_ip = self.config["left"]["ip"]
                self.robot_left_controller = URRTDEController(left_ip)
            except Exception as e:
                print(f"[ERROR] Failed to connect left robot: {e}")

        if "right" in robot_list or "both" in robot_list:
            try:
                right_ip = self.config["right"]["ip"]
                self.robot_right_controller = URRTDEController(right_ip)
            except Exception as e:
                print(f"[ERROR] Failed to connect right robot: {e}")

    def move_robots_to_pregrasp(self, robot_list="both", duration_sec=5.0):
        """Move specified robots ke pre-grasp position."""
        self.connect_robots([robot_list] if robot_list != "both" else ["left", "right"])
        
        results = {}
        
        if self.robot_left_controller and (robot_list == "left" or robot_list == "both"):
            print(f"\n[LEFT ROBOT] Starting motion...")
            results["left"] = self.robot_left_controller.move_to_pregrasp("left", duration_sec)
        
        if self.robot_right_controller and (robot_list == "right" or robot_list == "both"):
            print(f"\n[RIGHT ROBOT] Starting motion...")
            results["right"] = self.robot_right_controller.move_to_pregrasp("right", duration_sec)
        
        return results

    def disconnect_all(self):
        """Disconnect from all robots."""
        if self.robot_left_controller:
            self.robot_left_controller.disconnect()
        if self.robot_right_controller:
            self.robot_right_controller.disconnect()


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Move UR robots to pre-grasp position via RTDE"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (default: config/ur_robots.yaml)",
    )
    parser.add_argument(
        "--robot",
        type=str,
        default="both",
        choices=["left", "right", "both"],
        help="Which robot(s) to move (default: both)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Motion duration in seconds (default: 5.0)",
    )
    
    parsed_args = parser.parse_args(args)
    
    # Use ROS2 jika available, otherwise standalone
    try:
        rclpy.init()
        node = MoveToPreGraspRTDENode(config_file=parsed_args.config)
        results = node.move_robots_to_pregrasp(parsed_args.robot, parsed_args.duration)
        node.disconnect_all()
        node.destroy_node()
        rclpy.shutdown()
    except:
        # Standalone mode (tanpa ROS2)
        print("[ROS2] ROS2 not initialized, running in standalone mode...")
        node = MoveToPreGraspRTDENode(config_file=parsed_args.config)
        results = node.move_robots_to_pregrasp(parsed_args.robot, parsed_args.duration)
        node.disconnect_all()
    
    # Print results
    print("\n" + "="*50)
    print("MOTION RESULTS:")
    for robot, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"  {robot}: {status}")
    print("="*50)


if __name__ == "__main__":
    main()
