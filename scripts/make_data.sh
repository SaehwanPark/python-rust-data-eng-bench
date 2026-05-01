#!/usr/bin/env bash
set -euo pipefail

ROWS="${ROWS:-5000000}"
DIM_ROWS="${DIM_ROWS:-100000}"
EVENT_ROWS="${EVENT_ROWS:-5000000}"
DATA_DIR="${DATA_DIR:-data}"

uv run python -m python_bench.make_data --rows "$ROWS" --dim-rows "$DIM_ROWS" --event-rows "$EVENT_ROWS" --out "$DATA_DIR"
