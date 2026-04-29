use clap::{Parser, Subcommand};
use polars::prelude::*;
use rand::distributions::{Distribution, Uniform};
use rand::rngs::StdRng;
use rand::SeedableRng;
use rayon::prelude::*;
use serde::Serialize;
use std::collections::HashMap;
use std::error::Error;
use std::path::{Path, PathBuf};
use std::time::Instant;

#[derive(Parser)]
#[command(author, version, about)]
struct Cli {
  #[command(subcommand)]
  command: Command,
}

#[derive(Subcommand)]
enum Command {
  Numeric { #[arg(long, default_value_t = 50_000_000)] n: usize, #[arg(long, default_value_t = 5)] repeat: usize, #[arg(long, default_value_t = 11)] seed: u64 },
  NumericRayon { #[arg(long, default_value_t = 50_000_000)] n: usize, #[arg(long, default_value_t = 5)] repeat: usize, #[arg(long, default_value_t = 11)] seed: u64 },
  GroupbyNative { #[arg(long, default_value = "data")] data_dir: PathBuf, #[arg(long, default_value_t = 5)] repeat: usize },
  GroupbyPolars { #[arg(long, default_value = "data")] data_dir: PathBuf, #[arg(long, default_value_t = 5)] repeat: usize },
  JoinNative { #[arg(long, default_value = "data")] data_dir: PathBuf, #[arg(long, default_value_t = 5)] repeat: usize },
  JoinPolars { #[arg(long, default_value = "data")] data_dir: PathBuf, #[arg(long, default_value_t = 5)] repeat: usize },
  Sessionize { #[arg(long, default_value = "data")] data_dir: PathBuf, #[arg(long, default_value_t = 3)] repeat: usize },
  StreamScore { #[arg(long, default_value = "data")] data_dir: PathBuf, #[arg(long, default_value_t = 3)] repeat: usize, #[arg(long, default_value_t = 100_000)] chunk_rows: usize },
}

#[derive(Serialize)]
struct BenchResult {
  engine: String,
  task: String,
  repeat: usize,
  seconds: Vec<f64>,
  best_seconds: f64,
  rows: Option<usize>,
  n: Option<usize>,
  output_rows: Option<usize>,
  checksum: f64,
}

#[derive(Default, Clone, Copy)]
struct Agg { count: u64, gross_sum: f64, net_sum: f64, discount_sum: f64 }

#[derive(Default, Clone, Copy)]
struct JoinAgg { count: u64, weighted_net_sum: f64, amount_sum: f64 }

#[derive(Clone, Copy)]
struct DimRow { segment: u16, tier: u16, multiplier: f64 }

#[derive(Clone, Copy)]
struct UserState { last_ts: i64, score: f64, events: u32 }

fn main() -> Result<(), Box<dyn Error>> {
  let cli = Cli::parse();
  match cli.command {
    Command::Numeric { n, repeat, seed } => run_numeric(n, repeat, seed, false)?,
    Command::NumericRayon { n, repeat, seed } => run_numeric(n, repeat, seed, true)?,
    Command::GroupbyNative { data_dir, repeat } => run_groupby_native(&data_dir, repeat)?,
    Command::GroupbyPolars { data_dir, repeat } => run_groupby_polars(&data_dir, repeat)?,
    Command::JoinNative { data_dir, repeat } => run_join_native(&data_dir, repeat)?,
    Command::JoinPolars { data_dir, repeat } => run_join_polars(&data_dir, repeat)?,
    Command::Sessionize { data_dir, repeat } => run_sessionize(&data_dir, repeat)?,
    Command::StreamScore { data_dir, repeat, chunk_rows } => run_stream_score(&data_dir, repeat, chunk_rows)?,
  }
  Ok(())
}

fn run_numeric(n: usize, repeat: usize, seed: u64, parallel: bool) -> Result<(), Box<dyn Error>> {
  let mut seconds = Vec::with_capacity(repeat);
  let mut checksum = 0.0;
  for i in 0..repeat {
    let (elapsed, run_checksum) = if parallel { numeric_rayon_once(n, seed + i as u64) } else { numeric_once(n, seed + i as u64) };
    seconds.push(elapsed);
    checksum += run_checksum;
  }
  print_result(BenchResult { engine: if parallel { "rust-rayon" } else { "rust-native" }.to_string(), task: "numeric".to_string(), repeat, seconds: seconds.clone(), best_seconds: min_f64(&seconds), rows: None, n: Some(n), output_rows: None, checksum })
}

fn generate_numeric_inputs(n: usize, seed: u64) -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
  let mut rng = StdRng::seed_from_u64(seed);
  let lat_dist = Uniform::new(-70.0_f64, 70.0_f64);
  let lon_dist = Uniform::new(-180.0_f64, 180.0_f64);
  let mut lat1 = Vec::with_capacity(n);
  let mut lon1 = Vec::with_capacity(n);
  let mut lat2 = Vec::with_capacity(n);
  let mut lon2 = Vec::with_capacity(n);
  for _ in 0..n {
    lat1.push(lat_dist.sample(&mut rng));
    lon1.push(lon_dist.sample(&mut rng));
    lat2.push(lat_dist.sample(&mut rng));
    lon2.push(lon_dist.sample(&mut rng));
  }
  (lat1, lon1, lat2, lon2)
}

fn haversine_clipped(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
  let phi1 = lat1.to_radians();
  let phi2 = lat2.to_radians();
  let d_phi = (lat2 - lat1).to_radians();
  let d_lam = (lon2 - lon1).to_radians();
  let a = (d_phi / 2.0).sin().powi(2) + phi1.cos() * phi2.cos() * (d_lam / 2.0).sin().powi(2);
  let distance = 12_742.0 * a.sqrt().atan2((1.0 - a).sqrt());
  distance.clamp(0.0, 10_000.0)
}

fn summarize_values(mut values: Vec<f64>) -> f64 {
  let n = values.len();
  let sum = values.iter().sum::<f64>();
  let mean = sum / n as f64;
  let variance = values.iter().map(|value| { let diff = value - mean; diff * diff }).sum::<f64>() / n as f64;
  values.sort_unstable_by(|a, b| a.total_cmp(b));
  let p95 = values[((n as f64 * 0.95) as usize).min(n - 1)];
  mean + variance.sqrt() + p95
}

fn numeric_once(n: usize, seed: u64) -> (f64, f64) {
  let (lat1, lon1, lat2, lon2) = generate_numeric_inputs(n, seed);
  let start = Instant::now();
  let values = (0..n).map(|idx| haversine_clipped(lat1[idx], lon1[idx], lat2[idx], lon2[idx])).collect::<Vec<_>>();
  let checksum = summarize_values(values);
  (start.elapsed().as_secs_f64(), checksum)
}

fn numeric_rayon_once(n: usize, seed: u64) -> (f64, f64) {
  let (lat1, lon1, lat2, lon2) = generate_numeric_inputs(n, seed);
  let start = Instant::now();
  let values = (0..n).into_par_iter().map(|idx| haversine_clipped(lat1[idx], lon1[idx], lat2[idx], lon2[idx])).collect::<Vec<_>>();
  let checksum = summarize_values(values);
  (start.elapsed().as_secs_f64(), checksum)
}

fn run_groupby_native(data_dir: &Path, repeat: usize) -> Result<(), Box<dyn Error>> {
  let fact_path = data_dir.join("fact.csv");
  let rows = count_csv_rows(&fact_path)?;
  let mut seconds = Vec::with_capacity(repeat);
  let mut output_rows = 0;
  let mut checksum = 0.0;
  for _ in 0..repeat {
    let start = Instant::now();
    let (groups, run_checksum) = groupby_native_once(&fact_path)?;
    seconds.push(start.elapsed().as_secs_f64());
    output_rows = groups;
    checksum += run_checksum;
  }
  print_result(BenchResult { engine: "rust-native".to_string(), task: "groupby".to_string(), repeat, seconds: seconds.clone(), best_seconds: min_f64(&seconds), rows: Some(rows), n: None, output_rows: Some(output_rows), checksum })
}

fn groupby_native_once(fact_path: &Path) -> Result<(usize, f64), Box<dyn Error>> {
  let mut rdr = csv::Reader::from_path(fact_path)?;
  let mut groups: HashMap<(u16, u16), Agg> = HashMap::new();
  for rec in rdr.records() {
    let rec = rec?;
    let region: u16 = rec[1].parse()?;
    let channel: u16 = rec[2].parse()?;
    let amount: f64 = rec[3].parse()?;
    let discount: f64 = rec[4].parse()?;
    let net_amount = amount * (1.0 - discount);
    let agg = groups.entry((region, channel)).or_default();
    agg.count += 1;
    agg.gross_sum += amount;
    agg.net_sum += net_amount;
    agg.discount_sum += discount;
  }
  let checksum = groups.values().map(|agg| agg.net_sum + agg.discount_sum / agg.count as f64).sum();
  Ok((groups.len(), checksum))
}

fn run_groupby_polars(data_dir: &Path, repeat: usize) -> Result<(), Box<dyn Error>> {
  let fact_path = data_dir.join("fact.csv");
  let rows = count_csv_rows(&fact_path)?;
  let mut seconds = Vec::with_capacity(repeat);
  let mut output_rows = 0;
  let mut checksum = 0.0;
  for _ in 0..repeat {
    let start = Instant::now();
    let out = scan_csv(&fact_path)?
      .select([col("region"), col("channel"), col("amount"), col("discount")])
      .with_columns([((col("amount") * (lit(1.0) - col("discount"))).alias("net_amount"))])
      .group_by([col("region"), col("channel")])
      .agg([len().alias("n"), col("amount").sum().alias("gross_sum"), col("net_amount").sum().alias("net_sum"), col("discount").mean().alias("avg_discount")])
      .collect()?;
    seconds.push(start.elapsed().as_secs_f64());
    output_rows = out.height();
    checksum += sum_f64(&out, "net_sum")? + sum_f64(&out, "avg_discount")?;
  }
  print_result(BenchResult { engine: "rust-polars".to_string(), task: "groupby".to_string(), repeat, seconds: seconds.clone(), best_seconds: min_f64(&seconds), rows: Some(rows), n: None, output_rows: Some(output_rows), checksum })
}

fn run_join_native(data_dir: &Path, repeat: usize) -> Result<(), Box<dyn Error>> {
  let fact_path = data_dir.join("fact.csv");
  let dim_path = data_dir.join("dim.csv");
  let rows = count_csv_rows(&fact_path)?;
  let dim = read_dim(&dim_path)?;
  let mut seconds = Vec::with_capacity(repeat);
  let mut output_rows = 0;
  let mut checksum = 0.0;
  for _ in 0..repeat {
    let start = Instant::now();
    let (groups, run_checksum) = join_native_once(&fact_path, &dim)?;
    seconds.push(start.elapsed().as_secs_f64());
    output_rows = groups;
    checksum += run_checksum;
  }
  print_result(BenchResult { engine: "rust-native".to_string(), task: "join".to_string(), repeat, seconds: seconds.clone(), best_seconds: min_f64(&seconds), rows: Some(rows), n: None, output_rows: Some(output_rows), checksum })
}

fn join_native_once(fact_path: &Path, dim: &HashMap<u64, DimRow>) -> Result<(usize, f64), Box<dyn Error>> {
  let mut rdr = csv::Reader::from_path(fact_path)?;
  let mut groups: HashMap<(u16, u16), JoinAgg> = HashMap::new();
  for rec in rdr.records() {
    let rec = rec?;
    let user_id: u64 = rec[0].parse()?;
    let amount: f64 = rec[3].parse()?;
    let discount: f64 = rec[4].parse()?;
    if let Some(dim_row) = dim.get(&user_id) {
      let weighted_net = amount * dim_row.multiplier * (1.0 - discount);
      let agg = groups.entry((dim_row.segment, dim_row.tier)).or_default();
      agg.count += 1;
      agg.weighted_net_sum += weighted_net;
      agg.amount_sum += amount;
    }
  }
  let checksum = groups.values().map(|agg| agg.weighted_net_sum + agg.amount_sum / agg.count as f64).sum();
  Ok((groups.len(), checksum))
}

fn run_join_polars(data_dir: &Path, repeat: usize) -> Result<(), Box<dyn Error>> {
  let fact_path = data_dir.join("fact.csv");
  let dim_path = data_dir.join("dim.csv");
  let rows = count_csv_rows(&fact_path)?;
  let mut seconds = Vec::with_capacity(repeat);
  let mut output_rows = 0;
  let mut checksum = 0.0;
  for _ in 0..repeat {
    let start = Instant::now();
    let fact = scan_csv(&fact_path)?.select([col("user_id"), col("amount"), col("discount")]);
    let dim = scan_csv(&dim_path)?.select([col("user_id"), col("segment"), col("tier"), col("multiplier")]);
    let out = fact
      .join(dim, [col("user_id")], [col("user_id")], JoinArgs::new(JoinType::Inner))
      .with_columns([(col("amount") * col("multiplier") * (lit(1.0) - col("discount"))).alias("weighted_net")])
      .group_by([col("segment"), col("tier")])
      .agg([len().alias("n"), col("weighted_net").sum().alias("weighted_net_sum"), col("amount").mean().alias("avg_amount")])
      .collect()?;
    seconds.push(start.elapsed().as_secs_f64());
    output_rows = out.height();
    checksum += sum_f64(&out, "weighted_net_sum")? + sum_f64(&out, "avg_amount")?;
  }
  print_result(BenchResult { engine: "rust-polars".to_string(), task: "join".to_string(), repeat, seconds: seconds.clone(), best_seconds: min_f64(&seconds), rows: Some(rows), n: None, output_rows: Some(output_rows), checksum })
}

fn run_sessionize(data_dir: &Path, repeat: usize) -> Result<(), Box<dyn Error>> {
  let events_path = data_dir.join("events.csv");
  let mut seconds = Vec::with_capacity(repeat);
  let mut rows = 0;
  let mut sessions = 0;
  let mut checksum = 0.0;
  for _ in 0..repeat {
    let start = Instant::now();
    let (run_rows, run_sessions, run_checksum) = sessionize_once(&events_path)?;
    seconds.push(start.elapsed().as_secs_f64());
    rows = run_rows;
    sessions = run_sessions;
    checksum += run_checksum;
  }
  print_result(BenchResult { engine: "rust-native".to_string(), task: "sessionize".to_string(), repeat, seconds: seconds.clone(), best_seconds: min_f64(&seconds), rows: Some(rows), n: None, output_rows: Some(sessions), checksum })
}

fn sessionize_once(events_path: &Path) -> Result<(usize, usize, f64), Box<dyn Error>> {
  let mut rdr = csv::Reader::from_path(events_path)?;
  let mut rows = 0usize;
  let mut sessions = 0usize;
  let mut current_user: Option<u64> = None;
  let mut last_ts = 0i64;
  let mut session_score = 0.0;
  let mut checksum = 0.0;
  for rec in rdr.records() {
    let rec = rec?;
    rows += 1;
    let user_id: u64 = rec[0].parse()?;
    let ts: i64 = rec[1].parse()?;
    let event_type: u16 = rec[2].parse()?;
    let value: f64 = rec[3].parse()?;
    let new_session = current_user != Some(user_id) || ts - last_ts > 30 * 60;
    if new_session {
      if current_user.is_some() { checksum += session_score; }
      sessions += 1;
      session_score = 0.0;
      current_user = Some(user_id);
    }
    if matches!(event_type, 1 | 4 | 7) { session_score += value * 1.7; }
    else if matches!(event_type, 2 | 5) { session_score -= value * 0.4; }
    else { session_score += value * 0.1; }
    if session_score < 0.0 { session_score *= 0.5; }
    last_ts = ts;
  }
  if current_user.is_some() { checksum += session_score; }
  Ok((rows, sessions, checksum))
}

fn run_stream_score(data_dir: &Path, repeat: usize, chunk_rows: usize) -> Result<(), Box<dyn Error>> {
  let events_path = data_dir.join("stream_events.csv");
  let mut seconds = Vec::with_capacity(repeat);
  let mut rows = 0usize;
  let mut chunks = 0usize;
  let mut alerts = 0usize;
  let mut checksum = 0.0;
  for _ in 0..repeat {
    let start = Instant::now();
    let (run_rows, run_chunks, run_alerts, run_checksum) = stream_score_once(&events_path, chunk_rows)?;
    seconds.push(start.elapsed().as_secs_f64());
    rows = run_rows;
    chunks = run_chunks;
    alerts = run_alerts;
    checksum += run_checksum;
  }
  let mut result = serde_json::to_value(BenchResult {
    engine: "rust-native".to_string(),
    task: "streaming-score".to_string(),
    repeat,
    seconds: seconds.clone(),
    best_seconds: min_f64(&seconds),
    rows: Some(rows),
    n: None,
    output_rows: Some(alerts),
    checksum,
  })?;
  result["chunks"] = serde_json::json!(chunks);
  println!("{}", serde_json::to_string(&result)?);
  Ok(())
}

fn stream_score_once(events_path: &Path, chunk_rows: usize) -> Result<(usize, usize, usize, f64), Box<dyn Error>> {
  let mut rdr = csv::Reader::from_path(events_path)?;
  let mut states: HashMap<u64, UserState> = HashMap::new();
  let mut rows = 0usize;
  let mut chunks = 0usize;
  let mut alerts = 0usize;
  let mut checksum = 0.0;
  for rec in rdr.records() {
    let rec = rec?;
    if rows % chunk_rows == 0 { chunks += 1; }
    rows += 1;
    let user_id: u64 = rec[0].parse()?;
    let ts: i64 = rec[1].parse()?;
    let event_type: u16 = rec[2].parse()?;
    let value: f64 = rec[3].parse()?;
    let state = states.entry(user_id).or_insert(UserState { last_ts: ts, score: 0.0, events: 0 });
    let gap = (ts - state.last_ts).max(0) as f64;
    let decay = (-gap / 3_600.0).exp();
    state.score *= decay;
    if matches!(event_type, 1 | 4 | 7) { state.score += value * 1.7; }
    else if matches!(event_type, 2 | 5) { state.score -= value * 0.4; }
    else { state.score += value * 0.1; }
    if state.score < 0.0 { state.score *= 0.5; }
    state.last_ts = ts;
    state.events += 1;
    let alert = state.score > 250.0 && state.events >= 3;
    if alert {
      alerts += 1;
      checksum += state.score * 0.0001;
    } else {
      checksum += state.score * 0.00001;
    }
  }
  Ok((rows, chunks, alerts, checksum))
}

fn scan_csv(path: &Path) -> PolarsResult<LazyFrame> {
  let path = PlRefPath::try_from_path(path)?;
  LazyCsvReader::new(path).with_has_header(true).finish()
}

fn sum_f64(df: &DataFrame, column: &str) -> PolarsResult<f64> {
  Ok(df.column(column)?.f64()?.sum().unwrap_or(0.0))
}

fn read_dim(dim_path: &Path) -> Result<HashMap<u64, DimRow>, Box<dyn Error>> {
  let mut rdr = csv::Reader::from_path(dim_path)?;
  let mut dim = HashMap::new();
  for rec in rdr.records() {
    let rec = rec?;
    dim.insert(rec[0].parse()?, DimRow { segment: rec[1].parse()?, tier: rec[2].parse()?, multiplier: rec[3].parse()? });
  }
  Ok(dim)
}

fn count_csv_rows(path: &Path) -> Result<usize, Box<dyn Error>> {
  let mut rdr = csv::Reader::from_path(path)?;
  let mut rows = 0;
  for rec in rdr.records() { rec?; rows += 1; }
  Ok(rows)
}

fn min_f64(values: &[f64]) -> f64 { values.iter().copied().fold(f64::INFINITY, f64::min) }

fn print_result(result: BenchResult) -> Result<(), Box<dyn Error>> {
  println!("{}", serde_json::to_string(&result)?);
  Ok(())
}
