from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class UserState:
  last_ts: int
  score: float
  events: int


def update_score(state: UserState | None, ts: int, event_type: int, value: float) -> tuple[UserState, bool, float]:
  if state is None:
    state = UserState(last_ts=ts, score=0.0, events=0)

  gap = max(ts - state.last_ts, 0)
  decay = math.exp(-gap / 3_600.0)
  state.score *= decay

  if event_type in (1, 4, 7):
    state.score += value * 1.7
  elif event_type in (2, 5):
    state.score -= value * 0.4
  else:
    state.score += value * 0.1

  if state.score < 0.0:
    state.score *= 0.5

  state.last_ts = ts
  state.events += 1
  alert = state.score > 250.0 and state.events >= 3
  checksum_part = state.score * 0.0001 if alert else state.score * 0.00001
  return state, alert, checksum_part


def bench_streaming(data_dir: Path, chunk_rows: int) -> tuple[float, int, int, int, float]:
  path = data_dir / "stream_events.csv"
  start = time.perf_counter()
  rows = 0
  chunks = 0
  alerts = 0
  checksum = 0.0
  states: dict[int, UserState] = {}

  with path.open(newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
      rows += 1
      if (rows - 1) % chunk_rows == 0:
        chunks += 1

      user_id = int(row["user_id"])
      ts = int(row["ts"])
      event_type = int(row["event_type"])
      value = float(row["value"])
      state, alert, checksum_part = update_score(states.get(user_id), ts, event_type, value)
      states[user_id] = state
      alerts += int(alert)
      checksum += checksum_part

  elapsed = time.perf_counter() - start
  return elapsed, rows, chunks, alerts, checksum


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument("--data-dir", type=Path, default=Path("data"))
  parser.add_argument("--repeat", type=int, default=3)
  parser.add_argument("--chunk-rows", type=int, default=100_000)
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  seconds: list[float] = []
  rows = 0
  chunks = 0
  alerts = 0
  checksum = 0.0
  for _ in range(args.repeat):
    elapsed, rows, chunks, run_alerts, run_checksum = bench_streaming(args.data_dir, args.chunk_rows)
    seconds.append(elapsed)
    alerts = run_alerts
    checksum += run_checksum

  print(
    json.dumps(
      {
        "engine": "python-csv-loop",
        "task": "streaming-score",
        "rows": rows,
        "chunks": chunks,
        "output_rows": alerts,
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
