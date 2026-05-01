#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-data}"
REPEAT="${REPEAT:-20}"
LOOP_REPEAT="${LOOP_REPEAT:-20}"
N_NUMERIC="${N_NUMERIC:-50000000}"
CHUNK_ROWS="${CHUNK_ROWS:-100000}"
RESULTS_CSV="${RESULTS_CSV:-results/benchmark_runs.csv}"
SUITE_RUN_ID="${SUITE_RUN_ID:-$(uv run python -c 'import uuid; print(uuid.uuid4())')}"
export SUITE_RUN_ID
mkdir -p results

run_bench() {
  local output_path="$1"
  shift
  "$@" | tee "$output_path"
  uv run python -m python_bench.results_csv --input "$output_path" --csv "$RESULTS_CSV" --suite-run-id "$SUITE_RUN_ID"
}

run_bench results/python_numeric.jsonl uv run python -m python_bench.bench_numeric --n "$N_NUMERIC" --repeat "$REPEAT"
run_bench results/rust_numeric_native.jsonl cargo run --release -p rust_bench -- numeric --n "$N_NUMERIC" --repeat "$REPEAT"
run_bench results/rust_numeric_rayon.jsonl cargo run --release -p rust_bench -- numeric-rayon --n "$N_NUMERIC" --repeat "$REPEAT"

run_bench results/python_groupby_polars.jsonl uv run python -m python_bench.bench_polars groupby --data-dir "$DATA_DIR" --repeat "$REPEAT"
run_bench results/rust_groupby_polars.jsonl cargo run --release -p rust_bench -- groupby-polars --data-dir "$DATA_DIR" --repeat "$REPEAT"
run_bench results/rust_groupby_native.jsonl cargo run --release -p rust_bench -- groupby-native --data-dir "$DATA_DIR" --repeat "$REPEAT"

run_bench results/python_join_polars.jsonl uv run python -m python_bench.bench_polars join --data-dir "$DATA_DIR" --repeat "$REPEAT"
run_bench results/rust_join_polars.jsonl cargo run --release -p rust_bench -- join-polars --data-dir "$DATA_DIR" --repeat "$REPEAT"
run_bench results/rust_join_native.jsonl cargo run --release -p rust_bench -- join-native --data-dir "$DATA_DIR" --repeat "$REPEAT"

run_bench results/python_sessionize_loop.jsonl uv run python -m python_bench.bench_loop --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT"
run_bench results/rust_sessionize_loop.jsonl cargo run --release -p rust_bench -- sessionize --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT"

run_bench results/python_streaming_score.jsonl uv run python -m python_bench.bench_streaming --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT" --chunk-rows "$CHUNK_ROWS"
run_bench results/rust_streaming_score.jsonl cargo run --release -p rust_bench -- stream-score --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT" --chunk-rows "$CHUNK_ROWS"
