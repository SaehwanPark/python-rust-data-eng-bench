#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-data}"
REPEAT="${REPEAT:-5}"
LOOP_REPEAT="${LOOP_REPEAT:-3}"
N_NUMERIC="${N_NUMERIC:-50000000}"
CHUNK_ROWS="${CHUNK_ROWS:-100000}"
mkdir -p results

uv run python -m python_bench.bench_numeric --n "$N_NUMERIC" --repeat "$REPEAT" | tee results/python_numeric.jsonl
cargo run --release -p rust_bench -- numeric --n "$N_NUMERIC" --repeat "$REPEAT" | tee results/rust_numeric_native.jsonl
cargo run --release -p rust_bench -- numeric-rayon --n "$N_NUMERIC" --repeat "$REPEAT" | tee results/rust_numeric_rayon.jsonl

uv run python -m python_bench.bench_polars groupby --data-dir "$DATA_DIR" --repeat "$REPEAT" | tee results/python_groupby_polars.jsonl
cargo run --release -p rust_bench -- groupby-polars --data-dir "$DATA_DIR" --repeat "$REPEAT" | tee results/rust_groupby_polars.jsonl
cargo run --release -p rust_bench -- groupby-native --data-dir "$DATA_DIR" --repeat "$REPEAT" | tee results/rust_groupby_native.jsonl

uv run python -m python_bench.bench_polars join --data-dir "$DATA_DIR" --repeat "$REPEAT" | tee results/python_join_polars.jsonl
cargo run --release -p rust_bench -- join-polars --data-dir "$DATA_DIR" --repeat "$REPEAT" | tee results/rust_join_polars.jsonl
cargo run --release -p rust_bench -- join-native --data-dir "$DATA_DIR" --repeat "$REPEAT" | tee results/rust_join_native.jsonl

uv run python -m python_bench.bench_loop --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT" | tee results/python_sessionize_loop.jsonl
cargo run --release -p rust_bench -- sessionize --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT" | tee results/rust_sessionize_loop.jsonl

uv run python -m python_bench.bench_streaming --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT" --chunk-rows "$CHUNK_ROWS" | tee results/python_streaming_score.jsonl
cargo run --release -p rust_bench -- stream-score --data-dir "$DATA_DIR" --repeat "$LOOP_REPEAT" --chunk-rows "$CHUNK_ROWS" | tee results/rust_streaming_score.jsonl
