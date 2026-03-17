#!/bin/bash
#
# Replay rosbag with simulated time for offline bimanual UR10e playback
#
# Usage:
#   ./scripts/replay_rosbag.sh path/to/rosbag
#   ./scripts/replay_rosbag.sh path/to/rosbag --rate 2.0
#
# Notes:
#   - The --clock flag publishes /clock to enable use_sim_time
#   - Specify playback rate with --rate (default: 1.0)
#   - Before running this, start the offline launch: ros2 launch bimanual_ur10e offline.launch.py
#

set -e

# Check if at least one argument (rosbag path) is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <rosbag_path> [--rate RATE]"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/my_recording.mcap"
    echo "  $0 /path/to/my_recording.mcap --rate 2.0"
    exit 1
fi

ROSBAG_PATH="$1"

# Check if rosbag file exists
if [ ! -e "$ROSBAG_PATH" ]; then
    echo "Error: Rosbag file not found: $ROSBAG_PATH"
    exit 1
fi

# Parse optional rate argument
RATE_ARG=""
if [ $# -gt 1 ] && [ "$2" = "--rate" ] && [ $# -gt 2 ]; then
    RATE_ARG="--rate $3"
fi

echo "=========================================="
echo "Bimanual UR10e - Rosbag Replay"
echo "=========================================="
echo "Rosbag: $ROSBAG_PATH"
echo "Playback rate: ${RATE_ARG:-default (1.0)}"
echo ""
echo "Make sure you have started the offline launch in another terminal:"
echo "  ros2 launch bimanual_ur10e offline.launch.py"
echo ""

# Play rosbag with --clock flag to publish /clock for use_sim_time
echo "Starting rosbag playback..."
ros2 bag play "$ROSBAG_PATH" --clock $RATE_ARG

