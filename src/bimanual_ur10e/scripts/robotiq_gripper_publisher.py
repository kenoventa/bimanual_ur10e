#!/usr/bin/env python3
"""
robotiq_gripper_publisher.py

Publishes Robotiq gripper finger positions from dual UR robot controllers via socket communication.

This node:
1. Connects to both UR controllers' gripper pass-through ports (63352)
2. Queries current gripper positions using "GET POS" command
3. Publishes normalized positions (0.0 = open, 1.0 = closed) to /gripper*/joint_states topics
4. Uses the same logic as gello_software for compatibility
5. Supports bimanual setup with 2 robots and 2 grippers

Joint names: 'gripper1_finger_joint' and 'gripper2_finger_joint' to match URDF definitions.
Topics: /gripper1/joint_states and /gripper2/joint_states (for aggregation with arm joints)

Usage:
  ros2 launch bimanual_ur10e gripper_publisher.launch.py robot1_ip:=192.168.1.10 robot2_ip:=192.168.1.20
"""

import socket
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class RobotiqGripperPublisher(Node):
    """
    ROS 2 node that publishes Robotiq gripper positions for bimanual setup via ur_rtde socket interface.
    Supports 2 independent grippers (one per robot).
    """

    def __init__(self):
        super().__init__("robotiq_gripper_publisher")

        # Declare parameters for both robots
        self.declare_parameter("robot1_ip", "192.168.1.10")
        self.declare_parameter("robot2_ip", "192.168.1.20")

        # Calibration parameters for raw position range
        # Adjust these based on your gripper's actual min/max raw values
        # Default assumes 0=fully open, 255=fully closed
        self.declare_parameter("raw_position_min", 0.0)     # Raw value when fully open
        self.declare_parameter("raw_position_max", 255.0)   # Raw value when fully closed

        self.robot1_ip = (
            self.get_parameter("robot1_ip").get_parameter_value().string_value
        )
        self.robot2_ip = (
            self.get_parameter("robot2_ip").get_parameter_value().string_value
        )
        self.raw_position_min = (
            self.get_parameter("raw_position_min").get_parameter_value().double_value
        )
        self.raw_position_max = (
            self.get_parameter("raw_position_max").get_parameter_value().double_value
        )

        # UR Controller port for Robotiq gripper pass-through communication
        self.port = 63352

        # Initialize sockets for both robots
        self.socket1 = None
        self.socket2 = None

        # Attempt to connect to both grippers
        self.connect_to_gripper(1, self.robot1_ip)
        self.connect_to_gripper(2, self.robot2_ip)

        # Publishers for both robots
        self.publisher1 = self.create_publisher(JointState, "/gripper1/joint_states", 10)
        self.publisher2 = self.create_publisher(JointState, "/gripper2/joint_states", 10)

        # Timer to publish at ~10Hz (100ms)
        self.timer = self.create_timer(0.1, self.timer_callback)

        self.get_logger().info(
            f"Started bimanual Robotiq gripper publisher. "
            f"Robot1: {self.robot1_ip}:{self.port}, "
            f"Robot2: {self.robot2_ip}:{self.port} | "
            f"Calibration: raw_min={self.raw_position_min}, raw_max={self.raw_position_max}"
        )

    def connect_to_gripper(self, robot_id, robot_ip):
        """Establish socket connection to UR controller gripper port."""
        try:
            socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_obj.settimeout(2.0)
            socket_obj.connect((robot_ip, self.port))
            self.get_logger().info(
                f"Successfully connected to robot{robot_id} gripper at {robot_ip}:{self.port}"
            )
            
            # Store socket reference
            if robot_id == 1:
                self.socket1 = socket_obj
            else:
                self.socket2 = socket_obj
                
        except Exception as e:
            self.get_logger().error(
                f"Failed to connect to robot{robot_id} gripper socket at {robot_ip}: {e}"
            )

    def get_gripper_position(self, robot_id):
        """
        Query current gripper finger position from UR controller.
        
        Args:
            robot_id (int): Robot ID (1 or 2)
        
        Returns:
            float: Normalized position (0.0 = open, 1.0 = closed)
        """
        # Select the appropriate socket
        socket_obj = self.socket1 if robot_id == 1 else self.socket2
        
        if not socket_obj:
            # Try to reconnect if connection lost
            try:
                robot_ip = self.robot1_ip if robot_id == 1 else self.robot2_ip
                self.connect_to_gripper(robot_id, robot_ip)
            except Exception:
                return 0.0

        socket_obj = self.socket1 if robot_id == 1 else self.socket2
        if not socket_obj:
            return 0.0

        try:
            # Send command following gello_software protocol
            cmd = b"GET POS\n"
            socket_obj.sendall(cmd)
            data = socket_obj.recv(1024).decode("utf-8").strip()

            # Parse response: expected format is "POS <value>"
            # where <value> is 0-255 (0=open, 255=closed)
            parts = data.split()
            if len(parts) >= 2 and parts[0] == "POS":
                raw_pos = float(parts[1])

                # Normalize using calibrated min/max range
                # Formula: (raw - min) / (max - min) → results in 0.0 to 1.0
                range_span = self.raw_position_max - self.raw_position_min
                if range_span > 0:
                    normalized_pos = (raw_pos - self.raw_position_min) / range_span
                    # Clamp to [0, 1] range in case of overshoot
                    normalized_pos = max(0.0, min(1.0, normalized_pos))
                else:
                    normalized_pos = 0.0
                    self.get_logger().warning(
                        f"Robot{robot_id}: Invalid calibration - raw_position_min >= raw_position_max"
                    )
                return normalized_pos
            else:
                self.get_logger().warning(
                    f"Robot{robot_id}: Unexpected response format: {data}"
                )
                return 0.0

        except socket.timeout:
            self.get_logger().warning(
                f"Robot{robot_id}: Socket timeout while reading gripper position"
            )
            return 0.0
        except Exception as e:
            self.get_logger().warning(
                f"Robot{robot_id}: Error reading gripper position: {e}"
            )
            return 0.0

    def timer_callback(self):
        """Timer callback to read and publish gripper positions for both robots."""
        # Read positions
        pos1 = self.get_gripper_position(1)
        pos2 = self.get_gripper_position(2)

        # Create and publish JointState message for Gripper 1
        msg1 = JointState()
        msg1.header.stamp = self.get_clock().now().to_msg()
        msg1.header.frame_id = ""
        msg1.name = ["gripper1_finger_joint"]
        msg1.position = [pos1]
        msg1.velocity = []
        msg1.effort = []
        self.publisher1.publish(msg1)

        # Create and publish JointState message for Gripper 2
        msg2 = JointState()
        msg2.header.stamp = self.get_clock().now().to_msg()
        msg2.header.frame_id = ""
        msg2.name = ["gripper2_finger_joint"]
        msg2.position = [pos2]
        msg2.velocity = []
        msg2.effort = []
        self.publisher2.publish(msg2)


def main(args=None):
    """Main entry point for the node."""
    rclpy.init(args=args)
    node = RobotiqGripperPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down bimanual gripper publisher...")
    finally:
        # Close socket connections
        if node.socket1:
            try:
                node.socket1.close()
            except Exception:
                pass
        if node.socket2:
            try:
                node.socket2.close()
            except Exception:
                pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
