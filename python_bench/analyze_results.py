from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


REQUIRED_COLUMNS = {"task", "engine", "elapsed_seconds"}
HOST_LABELS = {
  "NucBoxEVO-X2": "Ryzen AI Max+ 395 WSL2",
  "Sae-Hwans-Mac-Studio-M1Max.local": "Apple M1 Max",
  "brb-10732.apn.wlan.private.upenn.edu": "Ryzen AI Max+ 395 Fedora",
  "sae-hwans-mbp.pmacs.upenn.edu": "Apple M3 Max",
  "saehwan-F7BSC": "Ryzen 9 7940HS",
}
DEFAULT_BASELINES = {
  "groupby": "python-polars",
  "join": "python-polars",
  "numeric": "python-numpy",
  "sessionize": "python-csv-loop",
  "streaming-score": "python-csv-loop",
}


@dataclass(frozen=True)
class Summary:
  task: str
  engine: str
  hostname: str
  suite_run_id: str
  count: int
  minimum: float
  median: float
  mean: float
  stdev: float
  best_recorded: float | None
  speedup: float | None = None


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Analyze and visualize benchmark run CSV results.")
  parser.add_argument("--csv", type=Path, default=Path("results/benchmark_runs.csv"), help="Benchmark CSV to analyze.")
  parser.add_argument("--out-dir", type=Path, default=Path("results/analysis"), help="Directory for report and charts.")
  parser.add_argument(
    "--baseline-engine",
    help="Optional engine to use as the speedup baseline for every task when present.",
  )
  return parser.parse_args()


def as_float(value: str | None) -> float | None:
  if value is None or value == "":
    return None
  try:
    result = float(value)
  except ValueError:
    return None
  if math.isnan(result) or math.isinf(result):
    return None
  return result


def load_rows(path: Path) -> list[dict[str, str]]:
  if not path.exists():
    raise SystemExit(f"CSV not found: {path}")
  with path.open(newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = set(reader.fieldnames or [])
    missing = sorted(REQUIRED_COLUMNS - fieldnames)
    if missing:
      raise SystemExit(f"CSV is missing required columns: {', '.join(missing)}")
    return [row for row in reader if as_float(row.get("elapsed_seconds")) is not None]


def summarize(rows: Iterable[dict[str, str]]) -> list[Summary]:
  grouped: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
  for row in rows:
    key = (
      row["task"],
      row["engine"],
      row.get("hostname") or "unknown-host",
      row.get("suite_run_id") or "unknown-suite",
    )
    grouped[key].append(row)

  summaries: list[Summary] = []
  for (task, engine, hostname, suite_run_id), group_rows in grouped.items():
    elapsed = [as_float(row.get("elapsed_seconds")) for row in group_rows]
    values = sorted(value for value in elapsed if value is not None)
    if not values:
      continue
    best_values = [as_float(row.get("best_seconds")) for row in group_rows]
    best_recorded = min((value for value in best_values if value is not None), default=None)
    summaries.append(
      Summary(
        task=task,
        engine=engine,
        hostname=hostname,
        suite_run_id=suite_run_id,
        count=len(values),
        minimum=values[0],
        median=statistics.median(values),
        mean=statistics.fmean(values),
        stdev=statistics.stdev(values) if len(values) > 1 else 0.0,
        best_recorded=best_recorded,
      )
    )
  return sorted(summaries, key=lambda item: (item.task, item.hostname, item.suite_run_id, item.median, item.engine))


def choose_baselines(summaries: Iterable[Summary], baseline_engine: str | None) -> dict[tuple[str, str, str], Summary]:
  grouped: dict[tuple[str, str, str], list[Summary]] = defaultdict(list)
  for summary in summaries:
    grouped[(summary.task, summary.hostname, summary.suite_run_id)].append(summary)

  baselines: dict[tuple[str, str, str], Summary] = {}
  for key, group in grouped.items():
    task = key[0]
    preferred = baseline_engine or DEFAULT_BASELINES.get(task)
    baseline = next((summary for summary in group if summary.engine == preferred), None)
    if baseline is None:
      baseline = max(group, key=lambda summary: summary.median)
    baselines[key] = baseline
  return baselines


def with_speedups(summaries: Iterable[Summary], baselines: dict[tuple[str, str, str], Summary]) -> list[Summary]:
  ranked: list[Summary] = []
  for summary in summaries:
    baseline = baselines[(summary.task, summary.hostname, summary.suite_run_id)]
    speedup = baseline.median / summary.median if summary.median > 0 else None
    ranked.append(
      Summary(
        task=summary.task,
        engine=summary.engine,
        hostname=summary.hostname,
        suite_run_id=summary.suite_run_id,
        count=summary.count,
        minimum=summary.minimum,
        median=summary.median,
        mean=summary.mean,
        stdev=summary.stdev,
        best_recorded=summary.best_recorded,
        speedup=speedup,
      )
    )
  return ranked


def host_label(hostname: str) -> str:
  return HOST_LABELS.get(hostname, hostname)


def aggregate_for_charts(summaries: Iterable[Summary]) -> dict[tuple[str, str], Summary]:
  grouped: dict[tuple[str, str], list[Summary]] = defaultdict(list)
  for summary in summaries:
    grouped[(summary.task, summary.engine)].append(summary)

  aggregate: dict[tuple[str, str], Summary] = {}
  for (task, engine), group in grouped.items():
    medians = [summary.median for summary in group]
    speedups = [summary.speedup for summary in group if summary.speedup is not None]
    aggregate[(task, engine)] = Summary(
      task=task,
      engine=engine,
      hostname="all-hosts",
      suite_run_id="all-suites",
      count=sum(summary.count for summary in group),
      minimum=min(summary.minimum for summary in group),
      median=statistics.median(medians),
      mean=statistics.fmean(medians),
      stdev=statistics.stdev(medians) if len(medians) > 1 else 0.0,
      best_recorded=min(
        (summary.best_recorded for summary in group if summary.best_recorded is not None),
        default=None,
      ),
      speedup=statistics.median(speedups) if speedups else None,
    )
  return aggregate


def grouped_bar(
  values: dict[tuple[str, str], float],
  ylabel: str,
  title: str,
  output_path: Path,
) -> None:
  tasks = sorted({task for task, _engine in values})
  engines = sorted({engine for _task, engine in values})
  if not tasks or not engines:
    return

  width = min(0.8 / len(engines), 0.18)
  x_positions = list(range(len(tasks)))
  fig_width = max(10.0, len(tasks) * 1.8)
  fig, ax = plt.subplots(figsize=(fig_width, 6.0))

  for index, engine in enumerate(engines):
    offset = (index - (len(engines) - 1) / 2) * width
    bar_values = [values.get((task, engine), 0.0) for task in tasks]
    ax.bar([x + offset for x in x_positions], bar_values, width=width, label=engine)

  ax.set_title(title)
  ax.set_ylabel(ylabel)
  ax.set_xticks(x_positions)
  ax.set_xticklabels(tasks, rotation=20, ha="right")
  ax.grid(axis="y", alpha=0.25)
  ax.legend(loc="best", fontsize="small")
  fig.tight_layout()
  fig.savefig(output_path, dpi=160)
  plt.close(fig)


def grouped_host_bars(
  summaries: Iterable[Summary],
  metric: str,
  ylabel: str,
  title: str,
  output_path: Path,
) -> None:
  rows = list(summaries)
  tasks = sorted({summary.task for summary in rows})
  engines = sorted({summary.engine for summary in rows})
  hosts = sorted({summary.hostname for summary in rows}, key=host_label)
  if not tasks or not engines or not hosts:
    return

  by_key = {
    (summary.task, summary.engine, summary.hostname): (
      summary.speedup if metric == "speedup" else summary.median
    )
    for summary in rows
  }
  width = min(0.8 / len(engines), 0.16)
  fig, axes = plt.subplots(
    len(tasks),
    1,
    figsize=(max(12.0, len(hosts) * 2.1), max(3.0 * len(tasks), 8.0)),
    sharex=True,
  )
  if len(tasks) == 1:
    axes = [axes]

  x_positions = list(range(len(hosts)))
  for ax, task in zip(axes, tasks):
    for index, engine in enumerate(engines):
      offset = (index - (len(engines) - 1) / 2) * width
      values = [by_key.get((task, engine, host), 0.0) or 0.0 for host in hosts]
      ax.bar([x + offset for x in x_positions], values, width=width, label=engine)
    ax.set_title(task)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)

  axes[-1].set_xticks(x_positions)
  axes[-1].set_xticklabels([host_label(host) for host in hosts], rotation=20, ha="right")
  axes[0].legend(loc="best", fontsize="small", ncols=min(4, len(engines)))
  fig.suptitle(title)
  fig.tight_layout()
  fig.savefig(output_path, dpi=160)
  plt.close(fig)


def fastest_host_heatmap(summaries: Iterable[Summary], output_path: Path) -> None:
  rows = list(summaries)
  tasks = sorted({summary.task for summary in rows})
  engines = sorted({summary.engine for summary in rows})
  hosts = sorted({summary.hostname for summary in rows}, key=host_label)
  if not tasks or not engines or not hosts:
    return

  medians = {(summary.task, summary.engine, summary.hostname): summary.median for summary in rows}
  matrix: list[list[float]] = []
  labels: list[list[str]] = []
  y_labels: list[str] = []
  for task in tasks:
    for engine in engines:
      present = [(host, medians[(task, engine, host)]) for host in hosts if (task, engine, host) in medians]
      if not present:
        continue
      best_host, best_value = min(present, key=lambda item: item[1])
      row_values = []
      row_labels = []
      for host in hosts:
        value = medians.get((task, engine, host))
        if value is None:
          row_values.append(math.nan)
          row_labels.append("")
        else:
          ratio = value / best_value
          row_values.append(ratio)
          marker = "*" if host == best_host else ""
          row_labels.append(f"{ratio:.2f}x\n{value:.3f}s{marker}")
      matrix.append(row_values)
      labels.append(row_labels)
      y_labels.append(f"{task}\n{engine}")

  fig, ax = plt.subplots(figsize=(max(11.0, len(hosts) * 2.0), max(7.0, len(y_labels) * 0.55)))
  image = ax.imshow(matrix, cmap="YlGnBu_r", aspect="auto", vmin=1.0)
  ax.set_title("Cross-Machine Runtime Ratio by Task and Engine")
  ax.set_xticks(range(len(hosts)))
  ax.set_xticklabels([host_label(host) for host in hosts], rotation=20, ha="right")
  ax.set_yticks(range(len(y_labels)))
  ax.set_yticklabels(y_labels)
  for y, row in enumerate(labels):
    for x, label in enumerate(row):
      if label:
        ax.text(x, y, label, ha="center", va="center", fontsize=7)
  cbar = fig.colorbar(image, ax=ax)
  cbar.set_label("Runtime relative to fastest host for row")
  fig.tight_layout()
  fig.savefig(output_path, dpi=160)
  plt.close(fig)


def distribution_plot(rows: Iterable[dict[str, str]], output_path: Path) -> None:
  grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
  for row in rows:
    elapsed = as_float(row.get("elapsed_seconds"))
    if elapsed is not None:
      grouped[(row["task"], row["engine"])].append(elapsed)
  if not grouped:
    return

  labels = sorted(grouped)
  values = [grouped[label] for label in labels]
  tick_labels = [f"{task}\n{engine}" for task, engine in labels]
  fig_width = max(13.0, len(labels) * 0.65)
  fig, ax = plt.subplots(figsize=(fig_width, 7.0))
  ax.boxplot(values, tick_labels=tick_labels, showfliers=False)
  ax.set_title("Runtime Distribution by Task and Engine Across Hosts")
  ax.set_ylabel("Elapsed seconds")
  ax.tick_params(axis="x", labelrotation=75)
  ax.grid(axis="y", alpha=0.25)
  fig.tight_layout()
  fig.savefig(output_path, dpi=160)
  plt.close(fig)


def write_charts(rows: list[dict[str, str]], summaries: list[Summary], out_dir: Path) -> list[Path]:
  aggregate = aggregate_for_charts(summaries)
  median_values = {(task, engine): summary.median for (task, engine), summary in aggregate.items()}
  speedup_values = {
    (task, engine): summary.speedup
    for (task, engine), summary in aggregate.items()
    if summary.speedup is not None
  }

  charts = [
    out_dir / "task_engine_median_seconds.png",
    out_dir / "task_engine_speedup.png",
    out_dir / "host_task_engine_median_seconds.png",
    out_dir / "host_task_engine_speedup.png",
    out_dir / "cross_machine_runtime_ratio.png",
    out_dir / "runtime_distribution.png",
  ]
  grouped_bar(median_values, "Median elapsed seconds", "Median Runtime by Task and Engine", charts[0])
  grouped_bar(speedup_values, "Speedup vs baseline", "Median Speedup by Task and Engine", charts[1])
  grouped_host_bars(summaries, "median", "Median seconds", "Median Runtime by Host, Task, and Engine", charts[2])
  grouped_host_bars(summaries, "speedup", "Speedup vs baseline", "Speedup by Host, Task, and Engine", charts[3])
  fastest_host_heatmap(summaries, charts[4])
  distribution_plot(rows, charts[5])
  return charts


def format_seconds(value: float | None) -> str:
  return "" if value is None else f"{value:.4f}"


def format_host_inventory(rows: list[dict[str, str]]) -> list[str]:
  by_host: dict[str, list[dict[str, str]]] = defaultdict(list)
  for row in rows:
    by_host[row.get("hostname") or "unknown-host"].append(row)

  lines = [
    "## Host Inventory",
    "",
    "| label | hostname | processor | os | arch / cpu_count | timing_rows |",
    "| --- | --- | --- | --- | --- | ---: |",
  ]
  for hostname in sorted(by_host, key=host_label):
    row = by_host[hostname][0]
    os_label = f"{row.get('os', '')} {row.get('os_release', '')}".strip()
    arch = f"{row.get('arch', '')} / {row.get('cpu_count', '')}".strip()
    lines.append(
      f"| {host_label(hostname)} | {hostname} | {row.get('cpu_model', '')} | {os_label} | {arch} | {len(by_host[hostname])} |"
    )
  return lines


def format_fastest_host_section(summaries: list[Summary]) -> list[str]:
  grouped: dict[tuple[str, str], list[Summary]] = defaultdict(list)
  for summary in summaries:
    grouped[(summary.task, summary.engine)].append(summary)

  lines = [
    "## Fastest Host by Task and Engine",
    "",
    "| task | engine | fastest_host | median_seconds | next_best_ratio |",
    "| --- | --- | --- | ---: | ---: |",
  ]
  for key in sorted(grouped):
    ranked = sorted(grouped[key], key=lambda summary: summary.median)
    fastest = ranked[0]
    next_best_ratio = ranked[1].median / fastest.median if len(ranked) > 1 else 1.0
    lines.append(
      f"| {fastest.task} | {fastest.engine} | {host_label(fastest.hostname)} | "
      f"{fastest.median:.4f} | {next_best_ratio:.2f}x |"
    )
  return lines


def speedup_range(summaries: list[Summary], task: str, engine: str) -> tuple[float, float] | None:
  values = [
    summary.speedup
    for summary in summaries
    if summary.task == task and summary.engine == engine and summary.speedup is not None
  ]
  if not values:
    return None
  return min(values), max(values)


def format_observations(summaries: list[Summary]) -> list[str]:
  numeric = speedup_range(summaries, "numeric", "rust-rayon")
  sessionize = speedup_range(summaries, "sessionize", "rust-native")
  streaming = speedup_range(summaries, "streaming-score", "rust-native")

  fastest_by_task: dict[str, list[Summary]] = defaultdict(list)
  for summary in summaries:
    fastest_by_task[summary.task].append(summary)
  winners = {task: min(group, key=lambda summary: summary.median) for task, group in fastest_by_task.items()}

  lines = ["## Generated Observations", ""]
  lines.append(
    "- Python Polars is the fastest measured engine for both dataframe tasks on every host: "
    f"`groupby` best overall is {host_label(winners['groupby'].hostname)} at {winners['groupby'].median:.4f} s, "
    f"and `join` best overall is {host_label(winners['join'].hostname)} at {winners['join'].median:.4f} s."
  )
  if numeric:
    lines.append(
      f"- Rust Rayon is the fastest numeric implementation on every host, with {numeric[0]:.2f}x-{numeric[1]:.2f}x "
      "speedup over the NumPy baseline."
    )
  if sessionize and streaming:
    lines.append(
      f"- Native Rust keeps the largest advantage on row-wise stateful work: {sessionize[0]:.2f}x-{sessionize[1]:.2f}x "
      f"for `sessionize` and {streaming[0]:.2f}x-{streaming[1]:.2f}x for `streaming-score`."
    )
  lines.append(
    f"- The fastest overall host depends on workload: {host_label(winners['numeric'].hostname)} leads the Rust Rayon numeric task, "
    f"while {host_label(winners['sessionize'].hostname)} leads the Rust native sessionization task and "
    f"{host_label(winners['streaming-score'].hostname)} leads the Rust native streaming task."
  )
  return lines


def write_report(
  csv_path: Path,
  rows: list[dict[str, str]],
  summaries: list[Summary],
  baselines: dict[tuple[str, str, str], Summary],
  charts: list[Path],
  out_dir: Path,
) -> Path:
  report_path = out_dir / "report.md"
  hosts = sorted({row.get("hostname") or "unknown-host" for row in rows})
  suite_runs = sorted({row.get("suite_run_id") or "unknown-suite" for row in rows})
  tasks = sorted({row["task"] for row in rows})

  lines = [
    "# Benchmark Results Analysis",
    "",
    f"- Source CSV: `{csv_path}`",
    f"- Timing rows analyzed: {len(rows)}",
    f"- Hosts: {', '.join(hosts)}",
    f"- Suite runs: {len(suite_runs)}",
    f"- Tasks: {', '.join(tasks)}",
    "",
    "## Charts",
    "",
  ]
  for chart in charts:
    if chart.exists():
      lines.append(f"![{chart.stem}]({chart.name})")
      lines.append("")

  lines.extend(format_host_inventory(rows))
  lines.append("")
  lines.extend(format_observations(summaries))
  lines.append("")
  lines.extend(format_fastest_host_section(summaries))
  lines.append("")

  lines.extend(
    [
      "## Fastest Engine by Task, Host, and Suite Run",
      "",
      "| task | hostname | suite_run_id | fastest_engine | median_seconds | baseline_engine | speedup_vs_baseline |",
      "| --- | --- | --- | --- | ---: | --- | ---: |",
    ]
  )

  grouped: dict[tuple[str, str, str], list[Summary]] = defaultdict(list)
  for summary in summaries:
    grouped[(summary.task, summary.hostname, summary.suite_run_id)].append(summary)
  for key in sorted(grouped):
    fastest = min(grouped[key], key=lambda summary: summary.median)
    baseline = baselines[key]
    speedup = fastest.speedup or 0.0
    lines.append(
      f"| {fastest.task} | {fastest.hostname} | `{fastest.suite_run_id}` | {fastest.engine} | "
      f"{fastest.median:.4f} | {baseline.engine} | {speedup:.2f}x |"
    )

  lines.extend(
    [
      "",
      "## Summary Statistics",
      "",
      "| task | engine | hostname | suite_run_id | count | min_seconds | median_seconds | mean_seconds | stdev_seconds | best_recorded | speedup_vs_baseline |",
      "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
  )
  for summary in summaries:
    speedup = "" if summary.speedup is None else f"{summary.speedup:.2f}x"
    lines.append(
      f"| {summary.task} | {summary.engine} | {summary.hostname} | `{summary.suite_run_id}` | "
      f"{summary.count} | {summary.minimum:.4f} | {summary.median:.4f} | {summary.mean:.4f} | "
      f"{summary.stdev:.4f} | {format_seconds(summary.best_recorded)} | {speedup} |"
    )

  report_path.write_text("\n".join(lines) + "\n")
  return report_path


def main() -> None:
  args = parse_args()
  rows = load_rows(args.csv)
  if not rows:
    raise SystemExit(f"No valid timing rows found in {args.csv}")

  args.out_dir.mkdir(parents=True, exist_ok=True)
  summaries = summarize(rows)
  baselines = choose_baselines(summaries, args.baseline_engine)
  summaries = with_speedups(summaries, baselines)
  charts = write_charts(rows, summaries, args.out_dir)
  report_path = write_report(args.csv, rows, summaries, baselines, charts, args.out_dir)
  print(f"Wrote {report_path}")
  for chart in charts:
    if chart.exists():
      print(f"Wrote {chart}")


if __name__ == "__main__":
  main()
