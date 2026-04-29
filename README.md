# Python vs Rust data-engineering benchmarks

This repo compares Python and Rust for data-engineering style workloads under two assumptions:

1. **Library-grade comparison**: Python uses optimized packages such as NumPy and Polars; Rust also uses established libraries such as Rayon and Polars.
2. **Loop-heavy / streaming comparison**: workloads include stateful row-by-row logic where ordinary loops, mutable state, and branching are part of the hot path.

The goal is not to prove that one language is universally faster. The goal is to separate cases that are often mixed together:

- Python orchestration over native kernels: NumPy and Polars.
- Rust orchestration over native/library kernels: Rayon and Polars.
- Custom loop-heavy business logic: Python CSV loops vs Rust loops.
- Streaming-like event processing: per-user mutable state over an append-only event stream.

## Layout

```text
.
├── Cargo.toml
├── pyproject.toml
├── python_bench/
│   ├── bench_loop.py        # loop-heavy Python sessionization benchmark
│   ├── bench_numeric.py     # NumPy numeric benchmark
│   ├── bench_polars.py      # Python Polars groupby/join benchmarks
│   ├── bench_streaming.py   # streaming/stateful Python benchmark
│   └── make_data.py         # synthetic CSV data generator
├── rust_bench/
│   ├── Cargo.toml
│   └── src/main.rs          # native Rust, Rayon, Rust Polars, streaming benchmarks
└── scripts/
    ├── explain_polars.sh
    ├── make_data.sh
    └── run_all.sh
```

## Requirements

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv)
- Rust stable toolchain
- `cargo`

## Setup

```bash
uv sync
cargo fetch
```

Generate data:

```bash
bash scripts/make_data.sh
```

Default sizes:

- `fact.csv`: 5,000,000 rows
- `dim.csv`: 100,000 rows
- `events.csv`: 5,000,000 sorted event rows for sessionization
- `stream_events.csv`: 5,000,000 append-ordered event rows for streaming/stateful scoring

Override sizes:

```bash
ROWS=10000000 DIM_ROWS=200000 EVENT_ROWS=10000000 bash scripts/make_data.sh
```

## Run everything

```bash
bash scripts/run_all.sh
```

Override benchmark sizes:

```bash
N_NUMERIC=100000000 REPEAT=5 LOOP_REPEAT=3 CHUNK_ROWS=100000 bash scripts/run_all.sh
```

Each benchmark writes JSON lines into `results/` and also prints one JSON object to stdout.

## Benchmarks

### 1. Numeric kernel

Python:

```bash
uv run python -m python_bench.bench_numeric --n 50000000 --repeat 5
```

Rust native:

```bash
cargo run --release -p rust_bench -- numeric --n 50000000 --repeat 5
```

Rust Rayon:

```bash
cargo run --release -p rust_bench -- numeric-rayon --n 50000000 --repeat 5
```

This computes a haversine-like distance transform, clips values, then computes summary statistics. NumPy is expected to be strong because the hot path is native vectorized code. Rayon gives Rust a realistic parallel-library baseline.

### 2. Groupby aggregation, aligned Polars plans

Python Polars:

```bash
uv run python -m python_bench.bench_polars groupby --data-dir data --repeat 5
```

Rust Polars:

```bash
cargo run --release -p rust_bench -- groupby-polars --data-dir data --repeat 5
```

Rust native loop/hash map:

```bash
cargo run --release -p rust_bench -- groupby-native --data-dir data --repeat 5
```

The Python and Rust Polars versions now use an intentionally similar lazy plan shape:

- scan CSV
- select only required columns
- compute `net_amount`
- group by keys
- aggregate identical metrics

The Python benchmark has an `--explain` flag to inspect its optimized plan:

```bash
uv run python -m python_bench.bench_polars groupby --data-dir data --explain
```

### 3. Join + aggregation, aligned Polars plans

Python Polars:

```bash
uv run python -m python_bench.bench_polars join --data-dir data --repeat 5
```

Rust Polars:

```bash
cargo run --release -p rust_bench -- join-polars --data-dir data --repeat 5
```

Rust native loop/hash map:

```bash
cargo run --release -p rust_bench -- join-native --data-dir data --repeat 5
```

The Python and Rust Polars versions now both explicitly project the same columns before joining:

- fact: `user_id`, `amount`, `discount`
- dim: `user_id`, `segment`, `tier`, `multiplier`

This reduces accidental differences from projection pruning and makes the frontends more comparable.

### 4. Loop-heavy sessionization

Python CSV loop:

```bash
uv run python -m python_bench.bench_loop --data-dir data --repeat 3
```

Rust CSV loop:

```bash
cargo run --release -p rust_bench -- sessionize --data-dir data --repeat 3
```

This reads sorted events and applies row-by-row stateful logic:

- start a new session when the user changes or a 30-minute gap appears
- maintain mutable per-session score
- branch on event type
- apply stateful correction when the score goes negative

This benchmark is intentionally less dataframe-friendly. It represents cases where custom control flow, mutable state, and branches are a meaningful part of runtime.

### 5. Streaming/stateful event scoring

Python CSV loop:

```bash
uv run python -m python_bench.bench_streaming --data-dir data --repeat 3 --chunk-rows 100000
```

Rust CSV loop:

```bash
cargo run --release -p rust_bench -- stream-score --data-dir data --repeat 3 --chunk-rows 100000
```

This processes `stream_events.csv` in append order and maintains mutable state per user:

- hash map from user ID to state
- time-decayed score update
- event-type-dependent branching
- alert counting once scores cross a threshold
- chunk counters to mimic micro-batch processing

This benchmark is meant to enrich the suite with a streaming-pipeline pattern. It is not a Polars benchmark. It is closer to custom enrichment, fraud/risk scoring, online feature calculation, or event-driven ETL.

## Polars plan alignment notes

The Python and Rust Polars code paths are now closer, but still not guaranteed byte-for-byte identical internally. Remaining differences may come from:

- Python vs Rust frontend defaults
- Polars feature flags in `Cargo.toml`
- CSV scan defaults
- thread pool configuration
- Polars version differences between Python and Rust packages

For more controlled runs, set the thread count explicitly before running benchmarks:

```bash
export POLARS_MAX_THREADS=8
export RAYON_NUM_THREADS=8
bash scripts/run_all.sh
```

Use the same Polars version family when possible:

```bash
uv run python - <<'PY'
import polars as pl
print(pl.__version__)
PY
cargo tree -p rust_bench | grep polars
```

## How to interpret results

Expected pattern:

- **Python Polars vs Rust Polars** should be close when plans and versions are aligned. They use the same underlying engine, so differences usually come from frontend defaults, build features, CSV loading, and environment.
- **Python NumPy vs Rust Rayon/native** can go either way depending on CPU, vectorization, memory bandwidth, math-library behavior, and thread count.
- **Python CSV loop vs Rust CSV loop** should usually favor Rust, often substantially, because ordinary Python row loops execute Python bytecode for each record.
- **Streaming/stateful scoring** should usually favor Rust because it combines parsing, branching, hash-map updates, mutable state, and scalar math.
- **Rust native groupby/join vs Polars** may lose to Polars because Polars has specialized kernels, parallel execution, query optimization, and efficient columnar memory layout.

## Notes for fairer runs

- Run on AC power and avoid other heavy processes.
- Use `--release` for Rust.
- Run once before collecting numbers to warm filesystem cache and compile artifacts.
- Compare `best_seconds` and median-like values, not only the first run.
- Keep checksums close when comparing equivalent logic.
- Be careful comparing CSV parsing with in-memory work. CSV parsing can dominate runtime.
- Consider pinning CPU governor / performance mode on Linux for serious runs.

## Known caveat

The Rust Polars API changes across versions. This repo pins `polars = "0.53"` in `rust_bench/Cargo.toml`. If your local toolchain resolves a newer incompatible API, either keep this version or adjust the small `scan_csv`, `group_by`, or `join` calls in `rust_bench/src/main.rs`.
