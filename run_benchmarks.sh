#!/usr/bin/env bash
# Run the 30-query benchmark for each engine and save pytest-benchmark's output to results/.
# Neo4j must be running (see neo4j/README.md); the embedded engines need build_graph.py first.
# lance-csr runs twice, with its Lance datasets in memory and read lazily from disk.
# Pass engine directories to run a subset, e.g. ./run_benchmarks.sh kuzu lance_csr.
set -u
cd "$(dirname "$0")"
# The machine and date the results were measured on, for anyone quoting them.
{
  echo "date: $(date -u +%F)"
  echo "machine: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || uname -m), $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 )) GB"
  echo "os: $(sw_vers -productName 2>/dev/null || uname -s) $(sw_vers -productVersion 2>/dev/null || uname -r)"
  # Battery power can throttle the CPU, so record the power source (macOS only).
  pmset -g batt 2>/dev/null | head -1 | sed -n "s/.*'\(.*\)'.*/power: \1/p"
} > results/environment.yml
FLAGS=(
  --benchmark-min-rounds=5
  --benchmark-min-time=0.000005
  --benchmark-max-time=1.0
  --benchmark-timer=time.perf_counter
  --benchmark-calibration-precision=10
  --benchmark-warmup=off
  --benchmark-warmup-iterations=5
  --benchmark-disable-gc
  --benchmark-sort=fullname
)
RUNS=(
  "neo4j neo4j-2026.09.0"
  "kuzu kuzu-0.11.3"
  "ladybugdb ladybug-0.21.2"
  "lance_graph lance-graph-0.5.4"
  "duckpgq duckpgq-1.5.6"
  "falkordb falkordb-6.0.2"
  "lance_csr lance-csr-0.3.1-memory memory"
  "lance_csr lance-csr-0.3.1-lazy lazy"
)
for run in "${RUNS[@]}"; do
  read -r dir name mode <<< "$run"
  if [ $# -gt 0 ] && [[ ! " $* " =~ " $dir " ]]; then continue; fi
  (cd "$dir" && LANCE_CSR_MODE="${mode:-}" uv run --frozen pytest benchmark_query.py -p no:faulthandler "${FLAGS[@]}" > "../results/$name.txt" 2>&1)
  echo "$name: $(tail -1 "results/$name.txt")"
done
