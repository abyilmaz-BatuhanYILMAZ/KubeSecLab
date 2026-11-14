#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Never run insecure manifest via a normal apply; server dry-run is deliberate.
kubectl --context kind-kubesec-training auth can-i get pods \
  --as=system:serviceaccount:kubesec-training:demo-reader -n kubesec-training
if kubectl --context kind-kubesec-training auth can-i delete pods \
  --as=system:serviceaccount:kubesec-training:demo-reader -n kubesec-training; then
  echo "Unexpected delete permission" >&2
  exit 1
fi
if kubectl --context kind-kubesec-training apply --dry-run=server -f manifests/vulnerable/privileged-pod.yaml; then
  echo "Unexpected admission success: insecure Pod was not rejected" >&2
  exit 1
else
  echo "Expected: Pod Security Admission rejected the insecure Pod"
fi
kubectl --context kind-kubesec-training get pod secure-pod -n kubesec-training
