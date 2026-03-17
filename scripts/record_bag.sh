#!/usr/bin/env bash
# record_bag.sh
#
# Records joint states and TF topics for the bimanual UR10e setup.
# Data is written to the data/ directory with a timestamped folder name.
#
# Usage:
#   bash scripts/record_bag.sh [OUTPUT_DIR]
#
# If OUTPUT_DIR is not specified it defaults to data/bag_<timestamp>.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="${1:-${REPO_ROOT}/data/bag_${TIMESTAMP}}"

echo "[record_bag] Recording to: ${OUTPUT_DIR}"
echo "[record_bag] Press Ctrl+C to stop."

mkdir -p "${OUTPUT_DIR}"

ros2 bag record \
  --output "${OUTPUT_DIR}" \
  --storage sqlite3 \
  /robot1/joint_states \
  /robot2/joint_states \
  /joint_states \
  /tf \
  /tf_static
