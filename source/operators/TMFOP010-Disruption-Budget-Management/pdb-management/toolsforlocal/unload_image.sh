#!/usr/bin/env bash
set -e

DEFAULT_OPERATOR_VERSION="v0.1.3"
CLUSTER_NAME="oda-canvas"

usage() {
  cat <<EOF
Usage: $0 [OPTIONS] [OPERATOR_VERSION]

Removes specified images from all cluster nodes.

OPTIONS:
  -h, --help       Show this help message

ARGUMENTS:
  OPERATOR_VERSION   The operator image version to remove (default: ${DEFAULT_OPERATOR_VERSION})

Examples:

  # Use default version
  $0

  # Specify a version
  $0 v0.2.0
EOF
}

# Check for --help or -h
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

# Set operator version from argument or use default
OPERATOR_VERSION="${1:-$DEFAULT_OPERATOR_VERSION}"

# Images to remove
IMAGES=(
  "pdb-management:${OPERATOR_VERSION}"
)

# Find all node container names
NODES=$(docker ps --filter "name=${CLUSTER_NAME}" --format "{{.Names}}")

for node in $NODES; do
  echo "Processing node: $node"
  for image in "${IMAGES[@]}"; do
    echo "  Removing image: $image from $node"
    docker exec "$node" crictl rmi "$image" || echo "    Image $image not found in $node"
  done
done

echo "Done."
