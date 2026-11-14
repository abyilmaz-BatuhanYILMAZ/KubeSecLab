#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for cmd in kind kubectl docker; do
  command -v "$cmd" >/dev/null || { echo "Missing required command: $cmd" >&2; exit 2; }
done
docker info >/dev/null
kind create cluster --name kubesec-training --wait 90s
kubectl --context kind-kubesec-training apply -f manifests/safe/namespace.yaml
kubectl --context kind-kubesec-training apply -f manifests/safe/pod.yaml
kubectl --context kind-kubesec-training apply -f manifests/safe/role.yaml
kubectl --context kind-kubesec-training get pods -n kubesec-training
