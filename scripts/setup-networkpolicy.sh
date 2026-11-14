#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for command_name in kind kubectl docker curl; do
  command -v "$command_name" >/dev/null || { echo "Missing: $command_name" >&2; exit 2; }
done
docker info >/dev/null
if kind get clusters 2>/dev/null | grep -qx kubesec-net; then
  echo "Refusing to replace an existing kubesec-net cluster" >&2
  exit 2
fi

# A default kindnet CNI does not implement NetworkPolicy. This isolated
# kind cluster intentionally disables it to use Calico as the enforcing CNI.
kind create cluster --name kubesec-net --config config/kind-calico.yaml
context=kind-kubesec-net
calico_version=v3.33.0
url="https://raw.githubusercontent.com/projectcalico/calico/${calico_version}/manifests/calico.yaml"
echo "Installing pinned Calico ${calico_version} into temporary kind cluster"
curl --fail --location --silent --show-error --retry 3 "$url" -o /tmp/kubesec-calico.yaml
kubectl --context "$context" create -f /tmp/kubesec-calico.yaml
kubectl --context "$context" -n kube-system rollout status daemonset/calico-node --timeout=360s
kubectl --context "$context" wait --for=condition=Ready nodes --all --timeout=360s
kubectl --context "$context" apply -f manifests/networkpolicy/namespace.yaml
kubectl --context "$context" apply -f manifests/networkpolicy/workloads.yaml
kubectl --context "$context" -n kubesec-net wait --for=condition=Ready pod --all --timeout=240s
echo "Calico CNI and isolated test workloads ready"
