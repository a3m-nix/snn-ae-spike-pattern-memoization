# Exact Spike-Pattern Memoization for Spiking Autoencoder Intrusion Detection on Edge CPUs

Experimental code, pre-registration designs, native C/Python kernels, and benchmark/live-deployment results for exact spike-pattern memoization and spike-count grouping in Spiking Neural Network Autoencoders (SNN-AE).

## Repository Structure

| Directory / File | Contents |
|---|---|
| `01-results/` | Experimental outputs, logs, and analysis summaries across all suites (`s7c`, `s7g`, `s7i`, `s7j`, `s7k`, `s7k_capcheck`, `s7p`, `s7t`, `s7x_ij`, and `step8_live`) |
| `02-prereg-design/` | Pre-registered experimental designs, protocol addenda, and cryptographic lock manifests (`LOCK_*.sha256`) |
| `03-scripts/` | Native C kernels (ARM NEON, x86 AVX2, scalar references), Raspberry Pi 5 and x86 benchmark runners, FNIRSI power logger utilities, live shadow scripts, and frozen shared libraries |
| `LARGE_FILES.md` | Inventory and SHA-256 hashes of large or sensitive raw datasets and packet captures not mirrored to GitHub |
| `SHA256SUMS` | SHA-256 checksums for all tracked experiment files in this repository |

## Experiment Overview

| Suite | Platform | Purpose |
|---|---|---|
| `s7c` | Raspberry Pi 5 (ARMv8) | Cache-free native C baseline (`SNN_COUNT`, `DENSE_ZS`) under `performance` governor |
| `s7g` | Raspberry Pi 5 (ARMv8) | Accuracy–cost trade-off exploration and 9-unit energy confirmation (`SNN_MEMOV2` vs. `DENSE_AQV2`) |
| `s7i`, `s7j` | Raspberry Pi 5 (ARMv8) | Vectorized NEON hit/miss paths (`SNN_MEMOV3`, `DENSE_AQV3`) and spike-count/tri-level grouping (`SNN_RQC`, `SNN_RQT`) across cache capacities |
| `s7x_ij` | x86_64 server (AVX2) | 30-unit confirmation (`3 seeds × 10 folds` per dataset) with 2,160 bit-identity checks, accuracy feasibility, and Holm-corrected latency tests |
| `s7p` | Raspberry Pi 5 + FNIRSI FNB-58 | Board-level USB-C power and energy-above-idle (ΔE) measurements at ~100 Hz (384 valid conditions across `S7g`, `S7g-more`, `S7h`, `S7j`) |
| `s7k` | x86_64 server + Raspberry Pi 5 | Per-attack-subtype recall (`K1`, 30 units), spike-pattern recurrence and per-class traffic breakdown (`K2`), ARM PMU hardware counters (`K3`), and cache memory/capacity scaling (`K4`) |
| `s7k_capcheck` | Raspberry Pi 5 | Bit-identity verification at smaller cache capacities (`2^12` and `2^14` slots, 48/48 checks) |
| `s7t` | x86_64 server (AVX2) | Time-step ablation (`T ∈ {2, 3, 5, 7}`, 30 units/dataset, 960/960 bit-identity checks) |
| `step8_live` | Raspberry Pi 5 (live Wi-Fi) | 79-minute live shadow deployment (`286,787` scored packets; 60 min benign + 17.5 min 15-flood injection) |

## Note on Pre-Registration Lock Files

Pre-registration lock files (`LOCK_*.sha256` in `02-prereg-design/`, `01-results/s7t/LOCK_S7T.sha256`, and `01-results/s7x_ij/logs/design_sha256.txt`) preserve the original SHA-256 digests computed when each protocol was locked prior to execution (when the narrative design documents were originally authored in Indonesian). Those original lock manifests are retained unmodified for provenance; the narrative `.md` documents in this repository have been translated into English for international publication.
