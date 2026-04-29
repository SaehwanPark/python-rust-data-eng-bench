from __future__ import annotations

import argparse
import json
import time

import numpy as np


def run_once(n: int, seed: int) -> dict[str, float]:
  rng = np.random.default_rng(seed)
  lat1 = rng.uniform(-70.0, 70.0, n).astype(np.float64)
  lon1 = rng.uniform(-180.0, 180.0, n).astype(np.float64)
  lat2 = rng.uniform(-70.0, 70.0, n).astype(np.float64)
  lon2 = rng.uniform(-180.0, 180.0, n).astype(np.float64)

  start = time.perf_counter()
  phi1 = np.deg2rad(lat1)
  phi2 = np.deg2rad(lat2)
  d_phi = np.deg2rad(lat2 - lat1)
  d_lam = np.deg2rad(lon2 - lon1)
  a = np.sin(d_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(d_lam / 2.0) ** 2
  distance = 12_742.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
  clipped = np.clip(distance, 0.0, 10_000.0)
  result = {
    "mean": float(clipped.mean()),
    "std": float(clipped.std()),
    "p95": float(np.quantile(clipped, 0.95)),
  }
  elapsed = time.perf_counter() - start
  result["elapsed"] = elapsed
  return result


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser()
  parser.add_argument("--n", type=int, default=50_000_000)
  parser.add_argument("--repeat", type=int, default=5)
  parser.add_argument("--seed", type=int, default=11)
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  seconds: list[float] = []
  checksum = 0.0
  for i in range(args.repeat):
    result = run_once(args.n, args.seed + i)
    seconds.append(result["elapsed"])
    checksum += result["mean"] + result["std"] + result["p95"]

  print(
    json.dumps(
      {
        "engine": "python-numpy",
        "task": "numeric",
        "n": args.n,
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
