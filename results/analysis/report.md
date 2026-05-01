# Benchmark Results Analysis

- Source CSV: `results/benchmark_runs.csv`
- Timing rows analyzed: 780
- Hosts: brb-10732.apn.wlan.private.upenn.edu, sae-hwans-mbp.pmacs.upenn.edu, saehwan-F7BSC
- Suite runs: 3
- Tasks: groupby, join, numeric, sessionize, streaming-score

## Charts

![task_engine_median_seconds](task_engine_median_seconds.png)

![task_engine_speedup](task_engine_speedup.png)

![runtime_distribution](runtime_distribution.png)

## Fastest Engine by Task, Host, and Suite Run

| task | hostname | suite_run_id | fastest_engine | median_seconds | baseline_engine | speedup_vs_baseline |
| --- | --- | --- | --- | ---: | --- | ---: |
| groupby | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | python-polars | 0.0790 | python-polars | 1.00x |
| groupby | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | python-polars | 0.0684 | python-polars | 1.00x |
| groupby | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | python-polars | 0.1155 | python-polars | 1.00x |
| join | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | python-polars | 0.1348 | python-polars | 1.00x |
| join | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | python-polars | 0.1240 | python-polars | 1.00x |
| join | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | python-polars | 0.1699 | python-polars | 1.00x |
| numeric | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | rust-rayon | 0.6999 | python-numpy | 3.57x |
| numeric | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | rust-rayon | 0.6654 | python-numpy | 3.40x |
| numeric | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | rust-rayon | 0.9092 | python-numpy | 2.65x |
| sessionize | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | rust-native | 0.3657 | python-csv-loop | 15.14x |
| sessionize | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | rust-native | 0.6059 | python-csv-loop | 8.57x |
| sessionize | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | rust-native | 0.4213 | python-csv-loop | 11.76x |
| streaming-score | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | rust-native | 0.5053 | python-csv-loop | 14.03x |
| streaming-score | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | rust-native | 0.7770 | python-csv-loop | 8.89x |
| streaming-score | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | rust-native | 0.5725 | python-csv-loop | 13.03x |

## Summary Statistics

| task | engine | hostname | suite_run_id | count | min_seconds | median_seconds | mean_seconds | stdev_seconds | best_recorded | speedup_vs_baseline |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| groupby | python-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.0724 | 0.0790 | 0.0791 | 0.0038 | 0.0724 | 1.00x |
| groupby | rust-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.4260 | 0.4305 | 0.4314 | 0.0058 | 0.4260 | 0.18x |
| groupby | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.4973 | 0.5078 | 0.5073 | 0.0062 | 0.4973 | 0.16x |
| groupby | python-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.0628 | 0.0684 | 0.0694 | 0.0053 | 0.0628 | 1.00x |
| groupby | rust-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.2940 | 0.3000 | 0.3003 | 0.0040 | 0.2940 | 0.23x |
| groupby | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.7377 | 0.7452 | 0.7436 | 0.0035 | 0.7377 | 0.09x |
| groupby | python-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.0976 | 0.1155 | 0.1146 | 0.0089 | 0.0976 | 1.00x |
| groupby | rust-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.4585 | 0.4660 | 0.4660 | 0.0040 | 0.4585 | 0.25x |
| groupby | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.5770 | 0.5898 | 0.5891 | 0.0039 | 0.5770 | 0.20x |
| join | python-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.1196 | 0.1348 | 0.1357 | 0.0090 | 0.1196 | 1.00x |
| join | rust-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.5027 | 0.5235 | 0.5215 | 0.0106 | 0.5027 | 0.26x |
| join | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.6163 | 0.6230 | 0.6235 | 0.0054 | 0.6163 | 0.22x |
| join | python-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.1134 | 0.1240 | 0.1242 | 0.0046 | 0.1134 | 1.00x |
| join | rust-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.3447 | 0.3520 | 0.3522 | 0.0037 | 0.3447 | 0.35x |
| join | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.9307 | 0.9438 | 0.9433 | 0.0068 | 0.9307 | 0.13x |
| join | python-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.1584 | 0.1699 | 0.1726 | 0.0143 | 0.1584 | 1.00x |
| join | rust-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.5746 | 0.5847 | 0.5865 | 0.0074 | 0.5746 | 0.29x |
| join | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.7128 | 0.7292 | 0.7289 | 0.0058 | 0.7128 | 0.23x |
| numeric | rust-rayon | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.6860 | 0.6999 | 0.6990 | 0.0090 | 0.6860 | 3.57x |
| numeric | python-numpy | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 2.4342 | 2.4991 | 2.5012 | 0.0434 | 2.4342 | 1.00x |
| numeric | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 2.5702 | 2.5829 | 2.5839 | 0.0079 | 2.5702 | 0.97x |
| numeric | rust-rayon | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.6516 | 0.6654 | 0.6652 | 0.0063 | 0.6516 | 3.40x |
| numeric | python-numpy | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 2.2153 | 2.2608 | 2.2764 | 0.0501 | 2.2153 | 1.00x |
| numeric | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 2.8267 | 2.8883 | 2.8827 | 0.0302 | 2.8267 | 0.78x |
| numeric | rust-rayon | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.9012 | 0.9092 | 0.9124 | 0.0094 | 0.9012 | 2.65x |
| numeric | python-numpy | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 2.4080 | 2.4123 | 2.4301 | 0.0263 | 2.4080 | 1.00x |
| numeric | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 2.9888 | 3.0004 | 3.0027 | 0.0124 | 2.9888 | 0.80x |
| sessionize | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.3580 | 0.3657 | 0.3653 | 0.0019 | 0.3580 | 15.14x |
| sessionize | python-csv-loop | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 5.5102 | 5.5388 | 5.5592 | 0.0416 | 5.5102 | 1.00x |
| sessionize | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.5975 | 0.6059 | 0.6062 | 0.0044 | 0.5975 | 8.57x |
| sessionize | python-csv-loop | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 5.1700 | 5.1917 | 5.1924 | 0.0168 | 5.1700 | 1.00x |
| sessionize | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.4136 | 0.4213 | 0.4201 | 0.0033 | 0.4136 | 11.76x |
| sessionize | python-csv-loop | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 4.9323 | 4.9551 | 4.9634 | 0.0289 | 4.9323 | 1.00x |
| streaming-score | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.4952 | 0.5053 | 0.5038 | 0.0037 | 0.4952 | 14.03x |
| streaming-score | python-csv-loop | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 7.0243 | 7.0909 | 7.0986 | 0.0400 | 7.0243 | 1.00x |
| streaming-score | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.7683 | 0.7770 | 0.7786 | 0.0072 | 0.7683 | 8.89x |
| streaming-score | python-csv-loop | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 6.8421 | 6.9098 | 6.9140 | 0.0554 | 6.8421 | 1.00x |
| streaming-score | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.5698 | 0.5725 | 0.5727 | 0.0028 | 0.5698 | 13.03x |
| streaming-score | python-csv-loop | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 7.3307 | 7.4592 | 7.4529 | 0.0555 | 7.3307 | 1.00x |
