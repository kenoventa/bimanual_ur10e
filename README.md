# bimanual_ur10e

A clean, minimal ROS 2 Humble package for a bimanual UR10e setup.

## Features

- Visualize **two UR10e robots** simultaneously in RViz2
- Publish joint states for both robots (`/robot1/joint_states`, `/robot2/joint_states`)
- **Record** trajectories to a rosbag with a single script
- **Replay** trajectories offline (no real hardware needed)

---

## Repository structure

```
bimanual_ur10e/
├── src/
│   └── bimanual_ur10e/           # ROS2 package
│       ├── CMakeLists.txt
│       ├── package.xml
│       ├── launch/
│       │   ├── bimanual_ur10e.launch.py   # Live visualization
│       │   └── replay.launch.py           # Offline bag replay
│       ├── urdf/
│       │   └── bimanual_ur10e.urdf.xacro  # Dual-robot URDF
│       ├── config/
│       │   └── bimanual_ur10e.rviz        # Pre-configured RViz layout
│       └── scripts/
│           └── joint_state_publisher.py   # Fake joint state publisher
│
├── scripts/
│   ├── record_bag.sh   # Record joint states + TF to a bag file
│   └── replay_bag.sh   # Replay a bag file with /clock
│
├── data/               # Recorded bag files go here (git-ignored)
└── README.md
```

---

## Prerequisites

| Dependency | Notes |
|---|---|
| [ROS 2 Humble](https://docs.ros.org/en/humble/Installation.html) | Ubuntu 22.04 recommended |
| `ur_description` | `sudo apt install ros-humble-ur-description` |
| `robot_state_publisher` | `sudo apt install ros-humble-robot-state-publisher` |
| `joint_state_publisher` | `sudo apt install ros-humble-joint-state-publisher ros-humble-joint-state-publisher-gui` |
| `rviz2` | `sudo apt install ros-humble-rviz2` |
| `xacro` | `sudo apt install ros-humble-xacro` |
| `rosbag2` | `sudo apt install ros-humble-rosbag2` |

Install everything at once:

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

---

## Build

```bash
cd ~/ros2_ws          # or wherever your workspace is
# Copy or symlink the package
cp -r /path/to/bimanual_ur10e/src/bimanual_ur10e src/

colcon build --packages-select bimanual_ur10e
source install/setup.bash
```

---

## Usage

### 1. Visualize both robots in RViz2

```bash
# Terminal 1 – launch everything
ros2 launch bimanual_ur10e bimanual_ur10e.launch.py

# Optional: publish fake joint states from a separate terminal
python3 src/bimanual_ur10e/scripts/joint_state_publisher.py
```

The `joint_state_publisher_gui` window lets you manually move each joint.
Pass `use_gui:=false` to use the headless version instead:

```bash
ros2 launch bimanual_ur10e bimanual_ur10e.launch.py use_gui:=false
```

### 2. Record a trajectory

```bash
# Make sure the live stack (step 1) is running, then:
bash scripts/record_bag.sh
# Bag files are saved to data/bag_<timestamp>/
```

Recorded topics:
- `/robot1/joint_states`
- `/robot2/joint_states`
- `/joint_states`
- `/tf`
- `/tf_static`

### 3. Replay a trajectory offline

```bash
# Terminal 1 – start visualization with sim time
ros2 launch bimanual_ur10e replay.launch.py

# Terminal 2 – play back the bag
bash scripts/replay_bag.sh data/bag_<timestamp>
```

The replay script passes `--clock` to `ros2 bag play` so that
`robot_state_publisher` and RViz2 use the bag's recorded time.

---

## URDF overview

`urdf/bimanual_ur10e.urdf.xacro` includes the upstream `ur_macro.xacro`
macro twice, once per robot arm:

| Robot | TF prefix | Base offset |
|---|---|---|
| robot1 | `robot1_` | `xyz="-0.5 0.0 0.0"` (left) |
| robot2 | `robot2_` | `xyz="0.5 0.0 0.0"` (right, rotated 180°) |

Both robots are attached to the `world` link.

---

## Topic layout

```
/robot1/joint_states   → joint_state_publisher merges →  /joint_states
/robot2/joint_states   →                                  (consumed by robot_state_publisher)
/tf
/tf_static
/robot_description     (latched, published by robot_state_publisher)
```

---

## License

Apache-2.0
