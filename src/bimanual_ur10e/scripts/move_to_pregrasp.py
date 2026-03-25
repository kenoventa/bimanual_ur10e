#!/usr/bin/env python3
"""
move_to_pregrasp.py

Move bimanual UR10e robots to pre-grasp position before picking cable.
Performs smooth interpolated motion from current position to target pose.

Usage:
  python3 move_to_pregrasp.py [--robot ROBOT_NUM] [--duration SECONDS]

  --robot:      Which robot(s) to move: 1, 2, or both (default: both)
  --duration:   Motion duration in seconds (default: 5.0)

Example:
  python3 move_to_pregrasp.py --robot 1 --duration 3.0
"""

import argparse
import math
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


# Joint names for both robots
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

# Home/neutral position (all zeros)
HOME_POSE = [0.0, -math.pi / 2, 0.0, -math.pi / 2, 0.0, 0.0]

# Pre-grasp position: Ready to  approach cable from above
# Adjust these values based on your workspace and cable location
PREGRASP_POSE_LEFT = [
    -2.4184656778918665 * 180 / math.pi,
    -1.802105566064352 * 180 / math.pi,
    -2.574643135070801 * 180 / math.pi,
    0.9633027750202636 * 180 / math.pi,
    4.214846436177389 * 180 / math.pi,
    -1.7743828932391565 * 180 / math.pi,
    0.011764705882352941 * 180 / math.pi             
]
PREGRASP_POSE_RIGHT = [
    -0.915072266255514 * 180 / math.pi,
    -1.193003461962082 * 180 / math.pi,
    2.3953519503222864 * 180 / math.pi,
    -2.8518196545042933 * 180 / math.pi,
    1.996173620223999 * 180 / math.pi,
    0.22858597338199615 * 180 / math.pi,
    0.011764705882352941 * 180 / math.pi              # wrist_3_joint: neutral rotation
]


class MoveToPreGraspNode(Node):
    """ROS2 node to move robots to pre-grasp position."""

    def __init__(self, target_robot="both", motion_duration=5.0):
        super().__init__("move_to_pregrasp")
        
        self.target_robot = target_robot
        self.motion_duration = motion_duration
        self.rate_hz = 50  # Control loop frequency
        self.dt = 1.0 / self.rate_hz

        # Publishers for joint state commands
        self.pub1 = self.create_publisher(JointState, "/robot1/joint_states", 10)
        self.pub2 = self.create_publisher(JointState, "/robot2/joint_states", 10)

        # Store current positions (will be updated if subscribed)
        self.robot1_current = HOME_POSE[:]
        self.robot2_current = HOME_POSE[:]

        # Create subscribers to get current state
        self.sub1 = self.create_subscription(
            JointState, "/robot1/joint_states", self.robot1_callback, 10
        )
        self.sub2 = self.create_subscription(
            JointState, "/robot2/joint_states", self.robot2_callback, 10
        )

        self.get_logger().info(
            f"MoveToPreGrasp initialized - Robot: {target_robot}, Duration: {motion_duration}s"
        )

    def robot1_callback(self, msg):
        """Update robot1 current position."""
        if len(msg.position) == 6:
            self.robot1_current = list(msg.position)

    def robot2_callback(self, msg):
        """Update robot2 current position."""
        if len(msg.position) == 6:
            self.robot2_current = list(msg.position)

    def interpolate_pose(self, start, end, progress):
        """Linear interpolation between start and end pose.
        
        Args:
            start: Start position (list of 6 joint angles)
            end: End position (list of 6 joint angles)
            progress: Interpolation progress (0.0 to 1.0)
            
        Returns:
            Interpolated pose (list of 6 joint angles)
        """
        return [start[i] + (end[i] - start[i]) * progress for i in range(6)]

    def publish_joint_state(self, robot_num, positions):
        """Publish joint state message."""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        
        if robot_num == 1:
            msg.name = ROBOT1_JOINTS
        else:
            msg.name = ROBOT2_JOINTS
        
        msg.position = positions
        msg.velocity = [0.0] * 6
        msg.effort = [0.0] * 6
        
        if robot_num == 1:
            self.pub1.publish(msg)
        else:
            self.pub2.publish(msg)

    def move_to_pregrasp(self):
        """Execute smooth motion to pre-grasp position."""
        self.get_logger().info("Starting motion to pre-grasp position...")
        
        # Allow time to read current state
        time.sleep(0.5)
        
        start_time = time.time()
        
        while time.time() - start_time < self.motion_duration:
            elapsed = time.time() - start_time
            progress = elapsed / self.motion_duration
            
            # Clamp progress to [0, 1]
            progress = min(1.0, max(0.0, progress))
            
            # Calculate interpolated poses
            if self.target_robot in ["1", "both"]:
                pose1 = self.interpolate_pose(
                    self.robot1_current, PREGRASP_POSE_LEFT, progress
                )
                self.publish_joint_state(1, pose1)
            
            if self.target_robot in ["2", "both"]:
                pose2 = self.interpolate_pose(
                    self.robot2_current, PREGRASP_POSE_RIGHT, progress
                )
                self.publish_joint_state(2, pose2)
            
            # Log progress
            if elapsed % 1.0 < self.dt:  # Log every ~1 second
                self.get_logger().info(f"Motion progress: {progress*100:.1f}%")
            
            time.sleep(self.dt)
        
        # Publish final position to ensure it's reached
        if self.target_robot in ["1", "both"]:
            self.publish_joint_state(1, PREGRASP_POSE_LEFT)
        if self.target_robot in ["2", "both"]:
            self.publish_joint_state(2, PREGRASP_POSE_RIGHT)
        
        self.get_logger().info("Motion complete! Robots at pre-grasp position.")
        self.get_logger().info(f"Pre-grasp pose: {PREGRASP_POSE_LEFT if self.target_robot == '1' else PREGRASP_POSE_RIGHT}")


def main(args=None):
    parser = argparse.ArgumentParser(description="Move robots to pre-grasp position")
    parser.add_argument(
        "--robot",
        type=str,
        default="both",
        choices=["1", "2", "both"],
        help="Which robot to move (default: both)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Motion duration in seconds (default: 5.0)",
    )
    
    parsed_args = parser.parse_args()
    
    rclpy.init(args=args)
    node = MoveToPreGraspNode(
        target_robot=parsed_args.robot,
        motion_duration=parsed_args.duration,
    )
    
    try:
        node.move_to_pregrasp()
        rclpy.spin_once(node, timeout_sec=1.0)
    except KeyboardInterrupt:
        node.get_logger().info("Motion interrupted by user")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
