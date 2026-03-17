#!/usr/bin/env python3
"""
joint_state_publisher.py

Publishes fake joint states for both UR10e robots on:
  /robot1/joint_states
  /robot2/joint_states

This is useful for testing visualization without real robots or a controller.
The joints are held at their home positions by default; edit INITIAL_POSITIONS to
experiment with different configurations.

Usage:
  # Source your ROS2 workspace first, then:
  python3 joint_state_publisher.py
"""
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# Joint names must match the prefixed names in the URDF
ROBOT1_JOINTS = [
    "robot1_shoulder_pan_joint",
    "robot1_shoulder_lift_joint",
    "robot1_elbow_joint",
    "robot1_wrist_1_joint",
    "robot1_wrist_2_joint",
    "robot1_wrist_3_joint",
]

ROBOT2_JOINTS = [
    "robot2_shoulder_pan_joint",
    "robot2_shoulder_lift_joint",
    "robot2_elbow_joint",
    "robot2_wrist_1_joint",
    "robot2_wrist_2_joint",
    "robot2_wrist_3_joint",
]

# Home position (all values in radians)
HOME = [0.0, -math.pi / 2, 0.0, -math.pi / 2, 0.0, 0.0]


class BimanualJointStatePublisher(Node):
    def __init__(self):
        super().__init__("bimanual_joint_state_publisher")

        self.pub1 = self.create_publisher(JointState, "/robot1/joint_states", 10)
        self.pub2 = self.create_publisher(JointState, "/robot2/joint_states", 10)

        self.timer = self.create_timer(0.02, self.publish_states)  # 50 Hz

    def publish_states(self):
        stamp = self.get_clock().now().to_msg()

        msg1 = JointState()
        msg1.header.stamp = stamp
        msg1.name = ROBOT1_JOINTS
        msg1.position = HOME[:]
        msg1.velocity = [0.0] * 6
        msg1.effort = [0.0] * 6
        self.pub1.publish(msg1)

        msg2 = JointState()
        msg2.header.stamp = stamp
        msg2.name = ROBOT2_JOINTS
        msg2.position = HOME[:]
        msg2.velocity = [0.0] * 6
        msg2.effort = [0.0] * 6
        self.pub2.publish(msg2)


def main(args=None):
    rclpy.init(args=args)
    node = BimanualJointStatePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
