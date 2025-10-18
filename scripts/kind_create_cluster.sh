#!/bin/bash

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --name) CLUSTER_NAME="$2"; shift ;;
        --nodes) NODE_COUNT="$2"; shift ;;
    esac
    shift
done

echo "Creating Kind cluster '${CLUSTER_NAME}' with ${NODE_COUNT} nodes"

cat <<EOF | kind create cluster --name "${CLUSTER_NAME}" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
$(for i in $(seq 1 $NODE_COUNT); do echo "  - role: worker"; done)
EOF