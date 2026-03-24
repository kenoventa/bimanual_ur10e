#!/usr/bin/env python3
"""
Joint State Republisher for Multi-Robot UR10e Setup
...
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from rclpy.qos import QoSProfile, ReliabilityPolicy


class JointStateRepublisher(Node):
    def __init__(self):
        super().__init__("joint_state_republisher")

        self.robot_id   = self.declare_parameter("robot_id",    "robot1").value
        self.tf_prefix  = self.declare_parameter("tf_prefix",  "robot1_").value
        self.input_topic = self.declare_parameter(
            "input_topic", "/joint_state_broadcaster/state"
        ).value

        self.output_topic = f"/{self.robot_id}/joint_states"

        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, depth=10)

        self.sub = self.create_subscription(
            JointState,
            self.input_topic,
            self.callback,
            qos_profile=qos,
        )
        self.pub = self.create_publisher(JointState, self.output_topic, 10)

        self.get_logger().info(f"JointStateRepublisher '{self.robot_id}' initialized")
        self.get_logger().info(f"  Subscribe : {self.input_topic}")
        self.get_logger().info(f"  Publish   : {self.output_topic}")
        self.get_logger().info(f"  Prefix    : {self.tf_prefix}")

    def callback(self, msg: JointState):
        indices_to_keep = []
        filtered_names  = []

        for i, name in enumerate(msg.name):
            if name.startswith(self.tf_prefix):
                indices_to_keep.append(i)
                filtered_names.append(name)

        if not indices_to_keep:
            self.get_logger().warn(
                f"No joints with prefix '{self.tf_prefix}' found in: {msg.name}",
                throttle_duration_sec=5.0,
            )
            return

        out = JointState()
        out.header = msg.header
        out.name   = filtered_names

        if len(msg.position) == len(msg.name):
            out.position = [msg.position[i] for i in indices_to_keep]
        if len(msg.velocity) == len(msg.name):
            out.velocity = [msg.velocity[i] for i in indices_to_keep]
        if len(msg.effort) == len(msg.name):
            out.effort   = [msg.effort[i] for i in indices_to_keep]

        self.pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = JointStateRepublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()