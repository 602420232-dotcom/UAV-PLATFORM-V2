#!/bin/bash
# UAV Platform - Performance Benchmark Runner
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="$SCRIPT_DIR/reports/$TIMESTAMP"
mkdir -p "$REPORT_DIR"

echo "=================================="
echo "  UAV Performance Benchmark"
echo "=================================="
echo ""
echo "Target: $TARGET_URL"
echo "Report: $REPORT_DIR"
echo ""

# Run JMeter tests
jmeter -n -t "$SCRIPT_DIR/uav-path-planning-jmeter.jmx" \
  -l "$REPORT_DIR/results.jtl" \
  -e -o "$REPORT_DIR/html" \
  -Jtarget_url="${TARGET_URL:-http://localhost:8088}" \
  -Jthreads="${THREADS:-20}" \
  -Jrampup="${RAMPUP:-10}" \
  -Jduration="${DURATION:-300}" \
  -Jthroughput="${THROUGHPUT:-100}"

echo ""
echo "=================================="
echo "  Performance Summary"
echo "=================================="

# Parse results
if command -v jq &> /dev/null; then
  echo "Generating summary..."
  awk -F',' 'NR>1 {
    if ($3 ~ /200/) ok++; else err++
    total++
  } END {
    printf "Total Requests: %d\n", total
    printf "Success: %d (%.1f%%)\n", ok, (ok/total)*100
    printf "Errors: %d (%.1f%%)\n", err, (err/total)*100
  }' "$REPORT_DIR/results.jtl"
fi

echo ""
echo "Report: $REPORT_DIR/html/index.html"
echo "=================================="
