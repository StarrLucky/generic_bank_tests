#!/usr/bin/env bash
# Forwards every Bank of Anthos service to localhost so tests can reach them.
# Usage: ./scripts/port-forward.sh   (Ctrl+C stops all forwards)
set -euo pipefail

CONTEXT="${KUBE_CONTEXT:-kind-boa}"

# local_port:service:service_port
FORWARDS=(
  "8080:frontend:80"
  "8081:userservice:8080"
  "8082:contacts:8080"
  "8083:ledgerwriter:8080"
  "8084:balancereader:8080"
  "8085:transactionhistory:8080"
)
# WireMock admin API, only if chaos mode is installed (see scripts/wiremock.sh)
if kubectl --context "$CONTEXT" get svc wiremock >/dev/null 2>&1; then
  FORWARDS+=("8086:wiremock:8080")
fi

pids=()
cleanup() { kill "${pids[@]}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

for f in "${FORWARDS[@]}"; do
  IFS=: read -r local svc remote <<<"$f"
  # restart the forward if it drops (pod restarts break port-forward)
  (
    while true; do
      kubectl --context "$CONTEXT" port-forward "svc/$svc" "$local:$remote" >/dev/null 2>&1 || true
      sleep 1
    done
  ) &
  pids+=($!)
  echo "localhost:$local -> $svc:$remote"
done

wait
