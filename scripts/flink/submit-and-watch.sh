#!/bin/bash
set -euo pipefail

JM_URL="${FLINK_JM_REST:-http://flink-jobmanager:8081}"
ORDER_SQL="/opt/flink/submit.sql"
EVENTS_SQL="/opt/flink/submit_events.sql"

wait_for_jobmanager() {
  echo "Waiting for Flink JobManager at ${JM_URL}..."
  until curl -sf "${JM_URL}/overview" >/dev/null; do
    sleep 3
  done
  echo "JobManager is up"
}

has_running_source() {
  local source_name="$1"
  local job_ids
  local job_id
  local job_info

  job_ids=$(curl -sf "${JM_URL}/jobs/overview" |
    grep -oE '"jid":"[^"]+"' |
    cut -d '"' -f 4 || true)

  for job_id in ${job_ids}; do
    job_info=$(curl -sf "${JM_URL}/jobs/${job_id}" || true)

    if printf '%s' "${job_info}" |
        grep -q '"state":"RUNNING"' &&
       printf '%s' "${job_info}" |
        grep -q "${source_name}"; then
      return 0
    fi
  done

  return 1
}

submit_if_missing() {
  local source_name="$1"
  local sql_file="$2"

  if has_running_source "${source_name}"; then
    echo "Source ${source_name} already has a RUNNING job"
    return 0
  fi

  echo "No RUNNING job found for ${source_name}; submitting ${sql_file}"
  if ! /opt/flink/bin/sql-client.sh -f "${sql_file}"; then
    echo "ERROR: submission failed for ${source_name}; will retry later"
  fi
}

wait_for_jobmanager

while true; do
  submit_if_missing "order_events" "${ORDER_SQL}"
  submit_if_missing "kafka_events" "${EVENTS_SQL}"
  sleep 30
done
