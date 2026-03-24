# bimanual_ur10e

A ROS 2 Humble package for **bimanual UR10e robot operation** with two flexible modes:
- **Offline Mode:** Replay recorded trajectories from rosbag files (no hardware needed)
- **Online Mode:** Connect to real UR10e robots via drivers (live operation)

Both modes use the **same URDF** and provide consistent coordinate frames and joint naming.

---

## Quick Start

### Offline Mode (Testing/Demos - No Robots Required)
```bash
# Terminal 1: Start the offline launcher
ros2 launch bimanual_ur10e offline.launch.py

# Terminal 2: Play a rosbag file
./scripts/replay_rosbag.sh /path/to/rosbag.mcap
```

### Online Mode (Real Robots)
```bash
# Launch with robot IP addresses
ros2 launch bimanual_ur10e online.launch.py \
  robot1_ip:=192.168.1.10 \
  robot2_ip:=192.168.1.20
```

---

## Repository Structure

```
bimanual_ur10e/
├── README.md                                  # This file
│
├── src/bimanual_ur10e/
│   ├── CMakeLists.txt
│   ├── package.xml
│   │
│   ├── launch/
│   │   ├── offline.launch.py                # Rosbag playback launcher
│   │   ├── online.launch.py                 # Real robot launcher (with grippers)
│   │   ├── bimanual_ur10e.launch.py         # Mode selection guide
│   │   └── replay.launch.py                 # Legacy replay launcher
│   │
│   ├── scripts/
│   │   ├── replay_rosbag.sh                 # Rosbag playback helper
│   │   ├── record_bag.sh                    # Rosbag recording helper
│   │   ├── joint_state_publisher.py         # Test joint publisher
│   │   └── replay_bag.sh                    # Legacy replay script
│   │
│   ├── urdf/
│   │   └── bimanual_ur10e.urdf.xacro        # Dual-robot URDF (includes Robotiq grippers)
│   │
│   ├── config/
│   │   └── bimanual_ur10e.rviz              # RViz2 configuration
│   │
│   └── data/                                 # Reserved for rosbags
│
├── build/                                    # Build artifacts
├── install/                                  # Installed packages
└── log/                                      # Build logs
```

---

## Prerequisites

| Dependency | Installation |
|---|---|
| ROS 2 Humble | Ubuntu 22.04 or higher |
| ur_description | `sudo apt install ros-humble-ur-description` |
| robot_state_publisher | `sudo apt install ros-humble-robot-state-publisher` |
| joint_state_publisher | `sudo apt install ros-humble-joint-state-publisher ros-humble-joint-state-publisher-gui` |
| rviz2 | `sudo apt install ros-humble-rviz2` |
| xacro | `sudo apt install ros-humble-xacro` |
| rosbag2 | `sudo apt install ros-humble-rosbag2 ros-humble-rosbag2-storage-default-plugins` |

**Install all dependencies at once:**
```bash
sudo apt update
sudo apt install -y \
  ros-humble-ur-description \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-rviz2 \
  ros-humble-xacro \
  ros-humble-rosbag2 \
  ros-humble-rosbag2-storage-default-plugins
```

### Gripper Support (Robotiq 2F140)

This package includes **Robotiq 2F140 grippers** on both robot end effectors.

**Additional dependencies for gripper hardware control:**
```bash
sudo apt install -y \
  libserial-dev
```

**Gripper Configuration:**
- Robot 1 Gripper: `/dev/ttyUSB0` (update if different)
- Robot 2 Gripper: `/dev/ttyUSB1` (update if different)
- Baud Rate: 115200

**Gripper Joint Names:**
- `gripper1_finger_left_joint` / `gripper1_finger_right_joint`
- `gripper2_finger_left_joint` / `gripper2_finger_right_joint`

**To update serial ports if different:**
Edit `src/bimanual_ur10e/urdf/bimanual_ur10e.urdf.xacro` and change `com_port` parameters for each gripper macro.

---

## Build

```bash
cd ~/bimanual_ur10e
colcon build
source install/setup.bash
```

---

## Usage

### Offline Mode - Rosbag Playback

**Use Case:** Testing, demonstrations, development (no hardware required)

**Launch the offline stack:**
```bash
ros2 launch bimanual_ur10e offline.launch.py
```

**In another terminal, play a rosbag:**
```bash
./scripts/replay_rosbag.sh /path/to/rosbag.mcap
```

**Adjust playback speed (optional):**
```bash
./scripts/replay_rosbag.sh /path/to/rosbag.mcap --rate 2.0
```

**Parameters:**
- `use_gui` - Show joint_state_publisher GUI (default: true)
- `rviz_config` - Custom RViz config file

**Features:**
- Uses simulated time from rosbag (`use_sim_time=true`)
- No UR drivers or hardware needed
- Perfect for testing and demonstrations

---

### Online Mode - Real Robots

**Use Case:** Live robot operation with UR10e hardware

**Launch the online stack:**
```bash
ros2 launch bimanual_ur10e online.launch.py \
  robot1_ip:=192.168.1.100 \
  robot2_ip:=192.168.1.101
```

**Parameters:**
- `robot1_ip` - IP address of first UR10e (default: 192.168.1.100)
- `robot2_ip` - IP address of second UR10e (default: 192.168.1.101)
- `use_gui` - Show joint_state_publisher GUI (default: true)
- `rviz_config` - Custom RViz config file

**Features:**
- Real-time robot operation (`use_sim_time=false`)
- Connects to physical UR10e robots via drivers
- Live joint state updates
- TF transforms synchronized with hardware
- Gripper meshes and joint states visualized in RViz

**Prerequisites for Online Mode:**
- Both UR10e robots must be accessible on the network
- UR ROS 2 drivers must be installed and configured
- Network connectivity to both robot IP addresses
- For gripper control: USB serial ports must be accessible (permissions may be needed: `sudo chmod 666 /dev/ttyUSB*`)

---

### Gripper Usage

**Offline playback with grippers:**
Grippers are automatically included in the URDF. When replaying a rosbag with gripper states, they will animate in RViz.

```bash
# Terminal 1: Launch offline
ros2 launch bimanual_ur10e offline.launch.py use_gui:=false

# Terminal 2: Play rosbag (including gripper states if recorded)
ros2 bag play recorded_motion.mcap --clock
```

**Online control with grippers:**
When launching online mode, gripper messages come from the gripper hardware via USB serial ports.

```bash
# Verify gripper connectivity
ls /dev/ttyUSB*

# Check gripper status
ros2 topic echo /robot1_gripper_state  # If gripper driver publishes states
```

**Recording gripper motion:**
Record gripper states along with arm states for offline playback.

```bash
ros2 bag record \
  /joint_states \
  /robot1/gripper/joint_states \
  /robot2/gripper/joint_states \
  -o bimanual_motion_with_grippers.mcap
```

---

## Workflow Examples

### Record a Trajectory

```bash
# Start offline or online launcher
ros2 launch bimanual_ur10e offline.launch.py  # or online.launch.py

# In another terminal, record the rosbag
ros2 bag record -a -o my_demo.mcap

# Move the robots (manually via GUI or through your control program)

# Stop recording (Ctrl+C)
```

### Replay Downloaded Trajectory

```bash
# Terminal 1: Start offline launcher
ros2 launch bimanual_ur10e offline.launch.py

# Terminal 2: Play the rosbag
./scripts/replay_rosbag.sh my_demo.mcap
```

### Real Robot Demo

```bash
# Terminal 1: Start online launcher with your robots
ros2 launch bimanual_ur10e online.launch.py \
  robot1_ip:=192.168.1.100 \
  robot2_ip:=192.168.1.101

# Terminal 2: Run your control program
# (robots will animate in RViz based on real joint states)
```

---

## Coordinate Frame Convention

The dual-UR10e URDF defines two robots with integrated Robotiq 2F140 grippers:

| Robot | Base Offset | Orientation | TF Prefix | Gripper |
|---|---|---|---|---|
| robot1 | (-0.5, 0, 0) m | Facing +X | `robot1_` | gripper1 @ robot1_tool0 |
| robot2 | (+0.5, 0, 0) m | Rotated 180° around Z | `robot2_` | gripper2 @ robot2_tool0 |

Both robots share the `world` reference frame.

**Transform tree:**
```
world
├── robot1_base
│   └── [robot1 arm chain]
│       └── robot1_tool0
│           └── gripper1_base_link
│               └── [gripper finger links]
└── robot2_base
    └── [robot2 arm chain]
        └── robot2_tool0
            └── gripper2_base_link
                └── [gripper finger links]
```

**Joint state topics:**
- `/robot1/joint_states` - Arm joints (input from driver or rosbag)
- `/robot2/joint_states` - Arm joints (input from driver or rosbag)
- `/robot1/gripper/joint_states` - Gripper joints (input from hardware or rosbag)
- `/robot2/gripper/joint_states` - Gripper joints (input from hardware or rosbag)
- `/joint_states` - Aggregated arm + gripper output

---

## Troubleshooting

### Issue: RViz doesn't show robots
- **Offline:** Make sure rosbag playback is started in another terminal
- **Online:** Verify robot IP addresses are correct and robots are online
- **Both:** Check that robot_state_publisher is running: `ros2 node list | grep state_publisher`

### Issue: "Cannot connect to robot"
- Verify network connectivity: `ping 192.168.1.100` (adjust IP)
- Check that UR drivers are installed and configured
- Confirm firewall allows ROS 2 communication

### Issue: Joint states not updating
- **Offline:** Check rosbag contains required topics:
  ```bash
  ros2 bag info /path/to/rosbag.mcap | grep joint_states
  ```
- **Online:** Verify topics are publishing:
  ```bash
  ros2 topic echo /robot1/joint_states
  ros2 topic echo /robot2/joint_states
  ```

### Issue: TF frames not available
```bash
# View available TF frames
ros2 run tf2_tools view_frames
# Opens frames.pdf showing the TF tree
```

### Gripper Issues

**Gripper meshes not visible in RViz:**
- Verify URDF was updated with gripper macros: `xacro src/bimanual_ur10e/urdf/bimanual_ur10e.urdf.xacro | grep -i gripper`
- Check robot_state_publisher is running and loaded the full URDF
- In RViz, ensure "Robot Model" display is enabled

**Gripper not responding to commands (Online mode):**
- Check serial ports are detected: `ls /dev/ttyUSB*`
- Verify USB permissions: `sudo chmod 666 /dev/ttyUSB0 /dev/ttyUSB1`
- Check gripper serial port configuration in URDF matches actual ports
- Verify gripper hardware is powered and connected

**Gripper states not updating in rosbag playback (Offline mode):**
- Verify rosbag contains gripper state topics:
  ```bash
  ros2 bag info your_rosbag.mcap | grep gripper
  ```
- If rosbag lacks gripper states, they will be simulated (gripper stays static)
- For full gripper animation, record gripper states during online motion

---

## Useful ROS 2 Commands

```bash
# List all active nodes
ros2 node list

# List all topics
ros2 topic list

# View topic content
ros2 topic echo /robot1/joint_states

# View ROS 2 parameters
ros2 param list

# View TF tree
ros2 run tf2_tools view_frames

# Record all topics to rosbag
ros2 bag record -a -o output.mcap

# Play rosbag with simulated time
ros2 bag play output.mcap --clock

# Get help for a launch file
ros2 launch bimanual_ur10e offline.launch.py --show-args
```

---

## Support & Documentation

- [ROS 2 Humble Documentation](https://docs.ros.org/en/humble/)
- [UR Description Package](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description)
- [ROS 2 Launch Files](https://docs.ros.org/en/humble/How-To-Guides/launch-file-different-formats.html)
- [ROS 2 TF2 Documentation](https://docs.ros.org/en/humble/Concepts/Intermediate/Tf2/Main.html)

---

## License

Apache-2.0
