#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
context=kind-kubesec-net
namespace=kubesec-net

kubectl --context "$context" get nodes
kubectl --context "$context" -n "$namespace" wait --for=condition=Ready pod --all --timeout=180s

fetch() {
  kubectl --context "$context" -n "$namespace" exec "$1" -- \
    wget -qO- -T 3 http://web:8080
}

echo "Before the policy: both clients should reach the demo server"
for source in client-approved client-other; do
  output="$(fetch "$source")"
  [[ "$output" == *"hello-kubesec"* ]] || { echo "Connectivity not established: $source" >&2; exit 1; }
done

kubectl --context "$context" apply -f manifests/networkpolicy/default-deny-ingress.yaml
kubectl --context "$context" apply -f manifests/networkpolicy/allow-approved-to-web.yaml

echo "After the policy: approved client should reach web:8080"
# Give CNI enforcement and kube-proxy time to converge.
success=0
for attempt in $(seq 1 20); do
  if fetch client-approved 2>/dev/null | grep -q "hello-kubesec"; then
    success=1
    break
  fi
  sleep 3
done
[[ "$success" == "1" ]] || { echo "Expected approved ingress did not work" >&2; exit 1; }

echo "After the policy: other client must not reach the server"
blocked=0
for attempt in $(seq 1 20); do
  if ! fetch client-other >/dev/null 2>&1; then
    blocked=1
    break
  fi
  sleep 3
done
[[ "$blocked" == "1" ]] || { echo "NetworkPolicy was not enforced: other client can connect" >&2; exit 1; }
echo "PASS: Calico enforced the NetworkPolicy: approved allowed; other denied"
