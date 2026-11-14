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
# resourceNames limits get on a single ConfigMap (not all ConfigMaps).
identity="system:serviceaccount:kubesec-training:audit-reader"
kubectl --context kind-kubesec-training auth can-i get configmaps/approved-config --as="$identity" -n kubesec-training | grep -qx yes
for forbidden in \
  "get configmaps/other-config" \
  "list configmaps" \
  "get secrets"; do
  read -r -a argv <<< "$forbidden"
  result="$(kubectl --context kind-kubesec-training auth can-i "${argv[@]}" \
    --as="$identity" -n kubesec-training)"
  [[ "$result" == "no" ]] || { echo "Unexpected privilege: $forbidden -> $result" >&2; exit 1; }
done
kubectl --context kind-kubesec-training get pod secure-pod -n kubesec-training
