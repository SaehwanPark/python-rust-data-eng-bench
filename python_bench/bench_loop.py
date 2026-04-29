from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path


def bench_sessionize(data_dir: Path) -> tuple[float, int, int, float]:
  path = data_dir / "events.csv"
  start = time.perf_counter()

  rows = 0
  sessions = 0
  current_user: int | None = None
  last_ts = -1
  session_score = 0.0
  checksum = 0.0

  with path.open(newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
      rows += 1
      user_id = int(row["user_id"])
      ts = int(row["ts"])
      event_type = int(row["event_type"])
      value = float(row["value"])

      new_session = current_user != user_id or ts - last_ts > 30 * 60
      if new_session:
        if current_user is not None:
          checksum += session_score
        sessions += 1
        session_score = 0.0
        current_user = user_id

      if event_type in (1, 4, 7):
        session_score += value * 1.7
      elif event_type in (2, 5):
        session_score -= value * 0.4
      else:
        session_score += value * 0.1

      if session_score < 0.0:
        session_score *= 0.5

      last_ts = ts

  if current_user is not None:
    checksum += session_score

  elapsed = time.perf_counter() - start
  return elapsed, rows, sessions, checksum


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument("--data-dir", type=Path, default=Path("data"))
  parser.add_argument("--repeat", type=int, default=3)
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  seconds: list[float] = []
  rows = 0
  sessions = 0
  checksum = 0.0

  for _ in range(args.repeat):
    elapsed, rows, sessions, run_checksum = bench_sessionize(args.data_dir)
    seconds.append(elapsed)
    checksum += run_checksum

  print(
    json.dumps(
      {
        "engine": "python-csv-loop",
        "task": "sessionize",
        "rows": rows,
        "output_rows": sessions,
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
