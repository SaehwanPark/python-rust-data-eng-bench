# Benchmark Results Analysis

- Source CSV: `results/benchmark_runs.csv`
- Timing rows analyzed: 1300
- Hosts: NucBoxEVO-X2, Sae-Hwans-Mac-Studio-M1Max.local, brb-10732.apn.wlan.private.upenn.edu, sae-hwans-mbp.pmacs.upenn.edu, saehwan-F7BSC
- Suite runs: 5
- Tasks: groupby, join, numeric, sessionize, streaming-score

## Charts

![task_engine_median_seconds](task_engine_median_seconds.png)

![task_engine_speedup](task_engine_speedup.png)

![host_task_engine_median_seconds](host_task_engine_median_seconds.png)

![host_task_engine_speedup](host_task_engine_speedup.png)

![cross_machine_runtime_ratio](cross_machine_runtime_ratio.png)

![runtime_distribution](runtime_distribution.png)

## Host Inventory

| label | hostname | processor | os | arch / cpu_count | timing_rows |
| --- | --- | --- | --- | --- | ---: |
| Apple M1 Max | Sae-Hwans-Mac-Studio-M1Max.local | Apple M1 Max | Darwin 25.4.0 | arm64 / 10 | 260 |
| Apple M3 Max | sae-hwans-mbp.pmacs.upenn.edu | Apple M3 Max | Darwin 25.4.0 | arm64 / 16 | 260 |
| Ryzen 9 7940HS | saehwan-F7BSC | AMD Ryzen 9 7940HS w/ Radeon 780M Graphics | Linux 6.17.0-23-generic | x86_64 / 16 | 260 |
| Ryzen AI Max+ 395 Fedora | brb-10732.apn.wlan.private.upenn.edu | AMD RYZEN AI MAX+ 395 w/ Radeon 8060S | Linux 6.19.14-200.fc43.x86_64 | x86_64 / 32 | 260 |
| Ryzen AI Max+ 395 WSL2 | NucBoxEVO-X2 | AMD RYZEN AI MAX+ 395 w/ Radeon 8060S | Linux 6.6.87.2-microsoft-standard-WSL2 | x86_64 / 32 | 260 |

## Generated Observations

- Python Polars is the fastest measured engine for both dataframe tasks on every host: `groupby` best overall is Apple M3 Max at 0.0684 s, and `join` best overall is Apple M3 Max at 0.1240 s.
- Rust Rayon is the fastest numeric implementation on every host, with 2.65x-4.63x speedup over the NumPy baseline.
- Native Rust keeps the largest advantage on row-wise stateful work: 8.08x-15.14x for `sessionize` and 8.62x-14.03x for `streaming-score`.
- The fastest overall host depends on workload: Apple M3 Max leads the Rust Rayon numeric task, while Ryzen AI Max+ 395 Fedora leads the Rust native sessionization task and Ryzen AI Max+ 395 Fedora leads the Rust native streaming task.

## Fastest Host by Task and Engine

| task | engine | fastest_host | median_seconds | next_best_ratio |
| --- | --- | --- | ---: | ---: |
| groupby | python-polars | Apple M3 Max | 0.0684 | 1.15x |
| groupby | rust-native | Ryzen AI Max+ 395 Fedora | 0.5078 | 1.00x |
| groupby | rust-polars | Apple M3 Max | 0.3000 | 1.43x |
| join | python-polars | Apple M3 Max | 0.1240 | 1.09x |
| join | rust-native | Ryzen AI Max+ 395 Fedora | 0.6230 | 1.04x |
| join | rust-polars | Apple M3 Max | 0.3520 | 1.49x |
| numeric | python-numpy | Apple M3 Max | 2.2608 | 1.07x |
| numeric | rust-native | Ryzen AI Max+ 395 Fedora | 2.5829 | 1.06x |
| numeric | rust-rayon | Apple M3 Max | 0.6654 | 1.05x |
| sessionize | python-csv-loop | Ryzen AI Max+ 395 WSL2 | 4.8497 | 1.02x |
| sessionize | rust-native | Ryzen AI Max+ 395 Fedora | 0.3657 | 1.01x |
| streaming-score | python-csv-loop | Apple M3 Max | 6.9098 | 1.01x |
| streaming-score | rust-native | Ryzen AI Max+ 395 Fedora | 0.5053 | 1.03x |

## Fastest Engine by Task, Host, and Suite Run

| task | hostname | suite_run_id | fastest_engine | median_seconds | baseline_engine | speedup_vs_baseline |
| --- | --- | --- | --- | ---: | --- | ---: |
| groupby | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | python-polars | 0.1200 | python-polars | 1.00x |
| groupby | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | python-polars | 0.1016 | python-polars | 1.00x |
| groupby | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | python-polars | 0.0790 | python-polars | 1.00x |
| groupby | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | python-polars | 0.0684 | python-polars | 1.00x |
| groupby | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | python-polars | 0.1155 | python-polars | 1.00x |
| join | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | python-polars | 0.2684 | python-polars | 1.00x |
| join | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | python-polars | 0.2216 | python-polars | 1.00x |
| join | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | python-polars | 0.1348 | python-polars | 1.00x |
| join | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | python-polars | 0.1240 | python-polars | 1.00x |
| join | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | python-polars | 0.1699 | python-polars | 1.00x |
| numeric | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | rust-rayon | 0.8184 | python-numpy | 4.63x |
| numeric | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | rust-rayon | 0.9675 | python-numpy | 2.84x |
| numeric | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | rust-rayon | 0.6999 | python-numpy | 3.57x |
| numeric | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | rust-rayon | 0.6654 | python-numpy | 3.40x |
| numeric | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | rust-rayon | 0.9092 | python-numpy | 2.65x |
| sessionize | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | rust-native | 0.3683 | python-csv-loop | 13.17x |
| sessionize | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | rust-native | 0.7132 | python-csv-loop | 8.08x |
| sessionize | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | rust-native | 0.3657 | python-csv-loop | 15.14x |
| sessionize | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | rust-native | 0.6059 | python-csv-loop | 8.57x |
| sessionize | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | rust-native | 0.4213 | python-csv-loop | 11.76x |
| streaming-score | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | rust-native | 0.5213 | python-csv-loop | 13.45x |
| streaming-score | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | rust-native | 0.8996 | python-csv-loop | 8.62x |
| streaming-score | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | rust-native | 0.5053 | python-csv-loop | 14.03x |
| streaming-score | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | rust-native | 0.7770 | python-csv-loop | 8.89x |
| streaming-score | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | rust-native | 0.5725 | python-csv-loop | 13.03x |

## Summary Statistics

| task | engine | hostname | suite_run_id | count | min_seconds | median_seconds | mean_seconds | stdev_seconds | best_recorded | speedup_vs_baseline |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| groupby | python-polars | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.1040 | 0.1200 | 0.1280 | 0.0328 | 0.1040 | 1.00x |
| groupby | rust-polars | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.4651 | 0.4681 | 0.4835 | 0.0499 | 0.4651 | 0.26x |
| groupby | rust-native | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.5026 | 0.5099 | 0.5093 | 0.0056 | 0.5026 | 0.24x |
| groupby | python-polars | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.0963 | 0.1016 | 0.1017 | 0.0043 | 0.0963 | 1.00x |
| groupby | rust-polars | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.4577 | 0.4619 | 0.4627 | 0.0039 | 0.4577 | 0.22x |
| groupby | rust-native | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.8954 | 0.8987 | 0.9029 | 0.0083 | 0.8954 | 0.11x |
| groupby | python-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.0724 | 0.0790 | 0.0791 | 0.0038 | 0.0724 | 1.00x |
| groupby | rust-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.4260 | 0.4305 | 0.4314 | 0.0058 | 0.4260 | 0.18x |
| groupby | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.4973 | 0.5078 | 0.5073 | 0.0062 | 0.4973 | 0.16x |
| groupby | python-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.0628 | 0.0684 | 0.0694 | 0.0053 | 0.0628 | 1.00x |
| groupby | rust-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.2940 | 0.3000 | 0.3003 | 0.0040 | 0.2940 | 0.23x |
| groupby | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.7377 | 0.7452 | 0.7436 | 0.0035 | 0.7377 | 0.09x |
| groupby | python-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.0976 | 0.1155 | 0.1146 | 0.0089 | 0.0976 | 1.00x |
| groupby | rust-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.4585 | 0.4660 | 0.4660 | 0.0040 | 0.4585 | 0.25x |
| groupby | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.5770 | 0.5898 | 0.5891 | 0.0039 | 0.5770 | 0.20x |
| join | python-polars | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.2260 | 0.2684 | 0.2703 | 0.0297 | 0.2260 | 1.00x |
| join | rust-polars | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.6048 | 0.6190 | 0.6276 | 0.0206 | 0.6048 | 0.43x |
| join | rust-native | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.6455 | 0.6474 | 0.6492 | 0.0049 | 0.6455 | 0.41x |
| join | python-polars | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.1831 | 0.2216 | 0.2222 | 0.0206 | 0.1831 | 1.00x |
| join | rust-polars | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.5178 | 0.5367 | 0.5377 | 0.0114 | 0.5178 | 0.41x |
| join | rust-native | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 1.0492 | 1.0822 | 1.0840 | 0.0209 | 1.0492 | 0.20x |
| join | python-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.1196 | 0.1348 | 0.1357 | 0.0090 | 0.1196 | 1.00x |
| join | rust-polars | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.5027 | 0.5235 | 0.5215 | 0.0106 | 0.5027 | 0.26x |
| join | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.6163 | 0.6230 | 0.6235 | 0.0054 | 0.6163 | 0.22x |
| join | python-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.1134 | 0.1240 | 0.1242 | 0.0046 | 0.1134 | 1.00x |
| join | rust-polars | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.3447 | 0.3520 | 0.3522 | 0.0037 | 0.3447 | 0.35x |
| join | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.9307 | 0.9438 | 0.9433 | 0.0068 | 0.9307 | 0.13x |
| join | python-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.1584 | 0.1699 | 0.1726 | 0.0143 | 0.1584 | 1.00x |
| join | rust-polars | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.5746 | 0.5847 | 0.5865 | 0.0074 | 0.5746 | 0.29x |
| join | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.7128 | 0.7292 | 0.7289 | 0.0058 | 0.7128 | 0.23x |
| numeric | rust-rayon | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.7896 | 0.8184 | 0.8254 | 0.0248 | 0.7896 | 4.63x |
| numeric | rust-native | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 2.6848 | 2.7282 | 2.7294 | 0.0354 | 2.6848 | 1.39x |
| numeric | python-numpy | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 3.7036 | 3.7908 | 3.7873 | 0.0476 | 3.7036 | 1.00x |
| numeric | rust-rayon | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.9582 | 0.9675 | 0.9666 | 0.0070 | 0.9582 | 2.84x |
| numeric | python-numpy | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 2.7278 | 2.7429 | 2.7810 | 0.1010 | 2.7278 | 1.00x |
| numeric | rust-native | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 3.5412 | 3.5520 | 3.5564 | 0.0160 | 3.5412 | 0.77x |
| numeric | rust-rayon | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.6860 | 0.6999 | 0.6990 | 0.0090 | 0.6860 | 3.57x |
| numeric | python-numpy | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 2.4342 | 2.4991 | 2.5012 | 0.0434 | 2.4342 | 1.00x |
| numeric | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 2.5702 | 2.5829 | 2.5839 | 0.0079 | 2.5702 | 0.97x |
| numeric | rust-rayon | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.6516 | 0.6654 | 0.6652 | 0.0063 | 0.6516 | 3.40x |
| numeric | python-numpy | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 2.2153 | 2.2608 | 2.2764 | 0.0501 | 2.2153 | 1.00x |
| numeric | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 2.8267 | 2.8883 | 2.8827 | 0.0302 | 2.8267 | 0.78x |
| numeric | rust-rayon | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.9012 | 0.9092 | 0.9124 | 0.0094 | 0.9012 | 2.65x |
| numeric | python-numpy | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 2.4080 | 2.4123 | 2.4301 | 0.0263 | 2.4080 | 1.00x |
| numeric | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 2.9888 | 3.0004 | 3.0027 | 0.0124 | 2.9888 | 0.80x |
| sessionize | rust-native | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.3671 | 0.3683 | 0.3688 | 0.0015 | 0.3671 | 13.17x |
| sessionize | python-csv-loop | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 4.8082 | 4.8497 | 4.8575 | 0.0358 | 4.8082 | 1.00x |
| sessionize | rust-native | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.7096 | 0.7132 | 0.7141 | 0.0038 | 0.7096 | 8.08x |
| sessionize | python-csv-loop | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 5.7489 | 5.7640 | 5.7744 | 0.0325 | 5.7489 | 1.00x |
| sessionize | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.3580 | 0.3657 | 0.3653 | 0.0019 | 0.3580 | 15.14x |
| sessionize | python-csv-loop | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 5.5102 | 5.5388 | 5.5592 | 0.0416 | 5.5102 | 1.00x |
| sessionize | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.5975 | 0.6059 | 0.6062 | 0.0044 | 0.5975 | 8.57x |
| sessionize | python-csv-loop | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 5.1700 | 5.1917 | 5.1924 | 0.0168 | 5.1700 | 1.00x |
| sessionize | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.4136 | 0.4213 | 0.4201 | 0.0033 | 0.4136 | 11.76x |
| sessionize | python-csv-loop | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 4.9323 | 4.9551 | 4.9634 | 0.0289 | 4.9323 | 1.00x |
| streaming-score | rust-native | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 0.5055 | 0.5213 | 0.5222 | 0.0107 | 0.5055 | 13.45x |
| streaming-score | python-csv-loop | NucBoxEVO-X2 | `f85688b1-9123-4d28-a4bf-e5ead852a027` | 20 | 6.8635 | 7.0134 | 7.0686 | 0.1907 | 6.8635 | 1.00x |
| streaming-score | rust-native | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 0.8938 | 0.8996 | 0.9018 | 0.0081 | 0.8938 | 8.62x |
| streaming-score | python-csv-loop | Sae-Hwans-Mac-Studio-M1Max.local | `1efac902-458f-4981-8043-a350f6a4c591` | 20 | 7.6407 | 7.7513 | 7.8023 | 0.2299 | 7.6407 | 1.00x |
| streaming-score | rust-native | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 0.4952 | 0.5053 | 0.5038 | 0.0037 | 0.4952 | 14.03x |
| streaming-score | python-csv-loop | brb-10732.apn.wlan.private.upenn.edu | `5ec3ae94-6f41-494c-94d1-6ecc35cfa759` | 20 | 7.0243 | 7.0909 | 7.0986 | 0.0400 | 7.0243 | 1.00x |
| streaming-score | rust-native | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 0.7683 | 0.7770 | 0.7786 | 0.0072 | 0.7683 | 8.89x |
| streaming-score | python-csv-loop | sae-hwans-mbp.pmacs.upenn.edu | `b454effd-b605-4aaa-801c-de5fdae9f0a1` | 20 | 6.8421 | 6.9098 | 6.9140 | 0.0554 | 6.8421 | 1.00x |
| streaming-score | rust-native | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 0.5698 | 0.5725 | 0.5727 | 0.0028 | 0.5698 | 13.03x |
| streaming-score | python-csv-loop | saehwan-F7BSC | `b39ff5a0-ec02-4b14-bb01-189c861e4f6b` | 20 | 7.3307 | 7.4592 | 7.4529 | 0.0555 | 7.3307 | 1.00x |
