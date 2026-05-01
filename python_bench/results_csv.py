from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import socket
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


CSV_COLUMNS = [
  "suite_run_id",
  "benchmark_run_id",
  "started_at_utc",
  "run_index",
  "hostname",
  "os",
  "os_release",
  "os_version",
  "arch",
  "cpu_model",
  "cpu_count",
  "engine",
  "task",
  "elapsed_seconds",
  "repeat",
  "rows",
  "n",
  "output_rows",
  "chunks",
  "best_seconds",
  "checksum",
]


def cpu_model() -> str:
  system = platform.system()
  if system == "Darwin":
    try:
      return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
      pass
  if system == "Linux":
    try:
      with Path("/proc/cpuinfo").open() as f:
        for line in f:
          if line.lower().startswith("model name"):
            return line.split(":", 1)[1].strip()
    except OSError:
      pass
  return platform.processor() or platform.machine()


def machine_info() -> dict[str, str | int | None]:
  uname = platform.uname()
  return {
    "hostname": socket.gethostname(),
    "os": uname.system,
    "os_release": uname.release,
    "os_version": uname.version,
    "arch": uname.machine,
    "cpu_model": cpu_model(),
    "cpu_count": os.cpu_count(),
  }


def load_results(path: Path) -> list[dict[str, Any]]:
  results: list[dict[str, Any]] = []
  with path.open() as f:
    for line in f:
      line = line.strip()
      if line:
        results.append(json.loads(line))
  return results


def rows_for_result(result: dict[str, Any], info: dict[str, str | int | None], suite_run_id: str) -> list[dict[str, Any]]:
  benchmark_run_id = str(uuid.uuid4())
  started_at_utc = datetime.now(UTC).isoformat(timespec="seconds")
  seconds = result.get("seconds")
  if not isinstance(seconds, list):
    raise ValueError("benchmark result must contain a seconds array")

  rows: list[dict[str, Any]] = []
  for run_index, elapsed in enumerate(seconds, start=1):
    rows.append(
      {
        "suite_run_id": suite_run_id,
        "benchmark_run_id": benchmark_run_id,
        "started_at_utc": started_at_utc,
        "run_index": run_index,
        **info,
        "engine": result.get("engine"),
        "task": result.get("task"),
        "elapsed_seconds": elapsed,
        "repeat": result.get("repeat"),
        "rows": result.get("rows"),
        "n": result.get("n"),
        "output_rows": result.get("output_rows"),
        "chunks": result.get("chunks"),
        "best_seconds": result.get("best_seconds"),
        "checksum": result.get("checksum"),
      }
    )
  return rows


def append_rows(csv_path: Path, rows: list[dict[str, Any]]) -> None:
  csv_path.parent.mkdir(parents=True, exist_ok=True)
  write_header = not csv_path.exists() or csv_path.stat().st_size == 0
  with csv_path.open("a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    if write_header:
      writer.writeheader()
    writer.writerows(rows)


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Append flattened benchmark result rows to a persisted CSV.")
  parser.add_argument("--input", type=Path, required=True, help="JSONL benchmark result file to append from.")
  parser.add_argument("--csv", type=Path, default=Path("results/benchmark_runs.csv"), help="CSV file to append rows to.")
  parser.add_argument("--suite-run-id", default=os.environ.get("SUITE_RUN_ID"), help="Stable ID shared by one benchmark suite run.")
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  suite_run_id = args.suite_run_id or str(uuid.uuid4())
  info = machine_info()
  rows: list[dict[str, Any]] = []
  for result in load_results(args.input):
    rows.extend(rows_for_result(result, info, suite_run_id))
  append_rows(args.csv, rows)


if __name__ == "__main__":
  main()
