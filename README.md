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

### Online Mode Dependencies (RTDE Robot Control)

For direct UR robot control via RTDE (Real-Time Data Exchange):

```bash
pip install ur-rtde pyyaml
```

This enables scripts to move robots to specific joint angles without ROS 2 drivers.

### Gripper Support (Robotiq 2F140)

This package includes **Robotiq 2F140 grippers** on both robot end effectors. They are controlled via the UR10e robots (integrated via Modbus/Ethernet) and teleoperated through GELLO.

**No additional dependencies required** - gripper support is fully included in the URDF and automatically published by the UR driver.

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

**Use Case:** Testing, demonstrations, trajectory playback (no hardware required)

**Option 1: Record trajectory manually via GUI**

Terminal 1 - Start offline launcher:
```bash
ros2 launch bimanual_ur10e offline.launch.py use_gui:=true
```

Terminal 2 - Record joint states using **either method**:

**Method A: Using helper script (recommended)**
```bash
bash scripts/record_bag.sh
```
This creates a timestamped folder like `data/bag_20260325_143025/` and starts recording automatically.

**Method B: Direct ROS 2 command**
```bash
ros2 bag record /joint_states -o data/my_motion.mcap
```

Now drag the joint sliders in the GUI to create a trajectory. Stop recording (Ctrl+C) when done.

**Option 2: Playback recorded rosbag**

Terminal 1 - Launch offline (disable aggregator to avoid conflicts):
```bash
ros2 launch bimanual_ur10e offline.launch.py use_gui:=false enable_aggregator:=false
```

Terminal 2 - Play rosbag using **either method**:

**Method A: Using helper script (recommended)**
```bash
bash scripts/replay_rosbag.sh data/my_motion.mcap
bash scripts/replay_rosbag.sh data/my_motion.mcap --rate 2.0  # Optional: custom playback speed
```

**Method B: Direct ROS 2 command**
```bash
ros2 bag play data/my_motion.mcap --clock
ros2 bag play data/my_motion.mcap --clock --rate 2.0  # Optional: custom playback speed
```

Robot will animate in RViz based on recorded trajectory.

**Parameters:**
- `use_gui` - Show joint_state_publisher GUI (default: true)
- `enable_aggregator` - Enable joint state aggregator, disable for rosbag playback (default: true)
- `rviz_config` - Custom RViz config file

**Notes:**
- Initial RViz errors (missing TF/robot model) are normal—they resolve once rosbag starts publishing
- To replay rosbag multiple times, restart the launcher between plays
- The `--clock` flag is **required** for RViz to properly synchronize with rosbag timestamps

---

### Online Mode - Real Robots

**Use Case:** Live robot operation with UR10e hardware

**Launch the online stack:**
```bash
ros2 launch bimanual_ur10e online.launch.py \
  robot1_ip:=192.168.1.10 \
  robot2_ip:=192.168.1.20
```

**Parameters:**
- `robot1_ip` - IP address of first UR10e (default: 192.168.1.10)
- `robot2_ip` - IP address of second UR10e (default: 192.168.1.20)
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

**Offline playback with gripper states:**

If you have recorded a rosbag with gripper control:

```bash
# Terminal 1: Launch offline
ros2 launch bimanual_ur10e offline.launch.py

# Terminal 2: Play rosbag with gripper states
ros2 bag play recorded_gello_motion.mcap --clock
```


**Verify gripper states are being published:**

```bash
# Check if gripper joint states are in the aggregated /joint_states topic
ros2 topic echo /joint_states | grep gripper

# Or view the full joint state for robot 1
ros2 topic echo /robot1/joint_states
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

## Direct Robot Control (RTDE)

For moving robots to specific joint angles via RTDE protocol:

**Setup:**
1. Edit `config/ur_robots.yaml` with your robot IP addresses:
   ```yaml
   robots:
     robot1:
       ip: "192.168.1.10"
     robot2:
       ip: "192.168.1.20"
   ```

2. Run the move script:
   ```bash
   python3 src/bimanual_ur10e/scripts/move_to_pregrasp_rtde.py --robot both --duration 5.0
   ```

**Options:**
- `--robot` - Which robot(s): `1`, `2`, or `both` (default: both)
- `--duration` - Motion time in seconds (default: 5.0)
- `--config` - Custom config file path


---
