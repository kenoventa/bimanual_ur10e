#!/usr/bin/env bash
# replay_bag.sh
#
# Replays a recorded rosbag for offline visualization of the bimanual UR10e.
#
# Usage:
#   bash scripts/replay_bag.sh <BAG_DIRECTORY> [RATE]
#
# Arguments:
#   BAG_DIRECTORY  Path to the rosbag directory (contains metadata.yaml)
#   RATE           Playback rate multiplier (default: 1.0)
#
# Before running this script, start the replay launch file in another terminal:
#   ros2 launch bimanual_ur10e replay.launch.py

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <BAG_DIRECTORY> [RATE]"
  exit 1
fi

BAG_DIR="$1"
RATE="${2:-1.0}"

if [[ ! -d "${BAG_DIR}" ]]; then
  echo "[replay_bag] ERROR: Directory not found: ${BAG_DIR}"
  exit 1
fi

echo "[replay_bag] Replaying bag: ${BAG_DIR}  (rate=${RATE})"
echo "[replay_bag] Make sure 'ros2 launch bimanual_ur10e replay.launch.py' is running."

ros2 bag play \
  "${BAG_DIR}" \
  --rate "${RATE}" \
  --clock \
  --storage sqlite3
