#!/usr/bin/env bash
set -euo pipefail
DATA_DIR="${DATA_DIR:-data}"
uv run python -m python_bench.bench_polars groupby --data-dir "$DATA_DIR" --explain > results/python_groupby_polars_plan.txt
uv run python -m python_bench.bench_polars join --data-dir "$DATA_DIR" --explain > results/python_join_polars_plan.txt
cargo run --release -p rust_bench -- groupby-polars --data-dir "$DATA_DIR" --repeat 1 > /dev/null
cargo run --release -p rust_bench -- join-polars --data-dir "$DATA_DIR" --repeat 1 > /dev/null
printf 'Python optimized plans written to results/*.txt. Rust plan printing is not exposed by this CLI; compare code shape and timings.\n'
