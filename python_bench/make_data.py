from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import polars as pl


def make_data(rows: int, dim_rows: int, event_rows: int, out: Path, seed: int) -> None:
  rng = np.random.default_rng(seed)
  out.mkdir(parents=True, exist_ok=True)

  user_ids = rng.integers(0, dim_rows, size=rows, dtype=np.int64)
  regions = rng.integers(0, 25, size=rows, dtype=np.int16)
  channels = rng.integers(0, 12, size=rows, dtype=np.int16)
  amount = rng.gamma(shape=2.0, scale=35.0, size=rows).astype(np.float64)
  discount = rng.random(size=rows, dtype=np.float64) * 0.35

  fact = pl.DataFrame(
    {
      "user_id": user_ids,
      "region": regions,
      "channel": channels,
      "amount": amount,
      "discount": discount,
    }
  )
  fact.write_csv(out / "fact.csv")

  dim_user_ids = np.arange(dim_rows, dtype=np.int64)
  segment = rng.integers(0, 50, size=dim_rows, dtype=np.int16)
  tier = rng.integers(0, 6, size=dim_rows, dtype=np.int16)
  multiplier = (0.8 + rng.random(size=dim_rows) * 0.6).astype(np.float64)

  dim = pl.DataFrame(
    {
      "user_id": dim_user_ids,
      "segment": segment,
      "tier": tier,
      "multiplier": multiplier,
    }
  )
  dim.write_csv(out / "dim.csv")

  event_user_ids = rng.integers(0, dim_rows, size=event_rows, dtype=np.int64)
  ts = rng.integers(0, 30 * 24 * 60 * 60, size=event_rows, dtype=np.int64)
  event_type = rng.integers(0, 8, size=event_rows, dtype=np.int16)
  value = rng.gamma(shape=1.7, scale=12.0, size=event_rows).astype(np.float64)

  events = (
    pl.DataFrame(
      {
        "user_id": event_user_ids,
        "ts": ts,
        "event_type": event_type,
        "value": value,
      }
    )
    .sort(["user_id", "ts"])
  )
  events.write_csv(out / "events.csv")

  stream_user_ids = rng.integers(0, dim_rows, size=event_rows, dtype=np.int64)
  stream_ts = np.cumsum(rng.integers(0, 4, size=event_rows, dtype=np.int64))
  stream_event_type = rng.integers(0, 8, size=event_rows, dtype=np.int16)
  stream_value = rng.gamma(shape=1.7, scale=12.0, size=event_rows).astype(np.float64)
  stream_events = pl.DataFrame(
    {
      "user_id": stream_user_ids,
      "ts": stream_ts,
      "event_type": stream_event_type,
      "value": stream_value,
    }
  )
  stream_events.write_csv(out / "stream_events.csv")

  print(
    f"wrote {rows:,} fact rows, {dim_rows:,} dimension rows, "
    f"{event_rows:,} sorted event rows, and {event_rows:,} streaming event rows to {out}"
  )


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument("--rows", type=int, default=5_000_000)
  parser.add_argument("--dim-rows", type=int, default=100_000)
  parser.add_argument("--event-rows", type=int, default=5_000_000)
  parser.add_argument("--out", type=Path, default=Path("data"))
  parser.add_argument("--seed", type=int, default=7)
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  make_data(
    rows=args.rows,
    dim_rows=args.dim_rows,
    event_rows=args.event_rows,
    out=args.out,
    seed=args.seed,
  )


if __name__ == "__main__":
  main()
