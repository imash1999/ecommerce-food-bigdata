#!/bin/bash
set -euo pipefail

JM_URL="${FLINK_JM_REST:-http://flink-jobmanager:8081}"
SQL_FILE="${FLINK_SQL_FILE:-/opt/flink/submit.sql}"

wait_for_jobmanager() {
  echo "Waiting for Flink JobManager at ${JM_URL}..."
  until curl -sf "${JM_URL}/overview" >/dev/null; do
    sleep 3
  done
  echo "JobManager is up"
}

has_running_job() {
  curl -sf "${JM_URL}/jobs" | grep -q '"RUNNING"'
}

submit_job() {
  echo "Submitting ${SQL_FILE}"
  /opt/flink/bin/sql-client.sh -f "${SQL_FILE}"
}

wait_for_jobmanager

while true; do
  if has_running_job; then
    echo "Streaming job is RUNNING"
  else
    echo "No RUNNING Flink job found, submitting again"
    submit_job || echo "Submit failed, will retry"
  fi
  sleep 15
done
