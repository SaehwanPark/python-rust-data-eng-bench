from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import polars as pl


def count_rows(path: Path) -> int:
  return pl.scan_csv(path).select(pl.len()).collect().item()


def make_groupby_plan(data_dir: Path) -> pl.LazyFrame:
  fact_path = data_dir / "fact.csv"
  return (
    pl.scan_csv(fact_path)
    .select(["region", "channel", "amount", "discount"])
    .with_columns(((pl.col("amount") * (1.0 - pl.col("discount"))).alias("net_amount")))
    .group_by(["region", "channel"])
    .agg(
      pl.len().alias("n"),
      pl.col("amount").sum().alias("gross_sum"),
      pl.col("net_amount").sum().alias("net_sum"),
      pl.col("discount").mean().alias("avg_discount"),
    )
  )


def bench_groupby(data_dir: Path) -> tuple[float, int, float]:
  start = time.perf_counter()
  out = make_groupby_plan(data_dir).collect()
  elapsed = time.perf_counter() - start
  checksum = float(out["net_sum"].sum() + out["avg_discount"].sum())
  return elapsed, out.height, checksum


def make_join_plan(data_dir: Path) -> pl.LazyFrame:
  fact_path = data_dir / "fact.csv"
  dim_path = data_dir / "dim.csv"
  fact = pl.scan_csv(fact_path).select(["user_id", "amount", "discount"])
  dim = pl.scan_csv(dim_path).select(["user_id", "segment", "tier", "multiplier"])
  return (
    fact
    .join(dim, on="user_id", how="inner")
    .with_columns((pl.col("amount") * pl.col("multiplier") * (1.0 - pl.col("discount"))).alias("weighted_net"))
    .group_by(["segment", "tier"])
    .agg(
      pl.len().alias("n"),
      pl.col("weighted_net").sum().alias("weighted_net_sum"),
      pl.col("amount").mean().alias("avg_amount"),
    )
  )


def bench_join(data_dir: Path) -> tuple[float, int, float]:
  start = time.perf_counter()
  out = make_join_plan(data_dir).collect()
  elapsed = time.perf_counter() - start
  checksum = float(out["weighted_net_sum"].sum() + out["avg_amount"].sum())
  return elapsed, out.height, checksum


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument("task", choices=["groupby", "join"])
  parser.add_argument("--data-dir", type=Path, default=Path("data"))
  parser.add_argument("--repeat", type=int, default=5)
  parser.add_argument("--explain", action="store_true", help="Print the optimized Polars plan and exit.")
  return parser.parse_args()


def main() -> None:
  args = parse_args()

  if args.explain:
    plan = make_groupby_plan(args.data_dir) if args.task == "groupby" else make_join_plan(args.data_dir)
    print(plan.explain(optimized=True))
    return

  seconds: list[float] = []
  output_rows = 0
  checksum = 0.0
  rows = count_rows(args.data_dir / "fact.csv")

  for _ in range(args.repeat):
    if args.task == "groupby":
      elapsed, output_rows, run_checksum = bench_groupby(args.data_dir)
    else:
      elapsed, output_rows, run_checksum = bench_join(args.data_dir)
    seconds.append(elapsed)
    checksum += run_checksum

  print(
    json.dumps(
      {
        "engine": "python-polars",
        "task": args.task,
        "rows": rows,
        "output_rows": output_rows,
        "repeat": args.repeat,
        "seconds": seconds,
        "best_seconds": min(seconds),
        "checksum": checksum,
      },
      separators=(",", ":"),
    )
  )


if __name__ == "__main__":
  main()
