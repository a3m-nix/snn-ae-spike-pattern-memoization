# S7k Results — Per-Attack Impact, Reuse Mechanism, CPU Counters, and Memory (9 Nov 2026)

**References and Execution:**
- Design: `02-prereg-design/s7k/DESIGN_S7K.md` (v1.1), locked in `LOCK_S7K.sha256` (09:24:14 WIB) prior to measurement.
- Lock verified before analysis.
- Pi: 09:24–09:28 WIB under `e37-lock`, core 3. Server: 30 units/dataset, core 9, `nice 10`.
- Single-pass analysis: `03-scripts/s7k/s7k_analyze.py`. Full tables: `RESULTS_S7K_auto.md` and CSVs in this directory.
- Server results verified against `SHA256SUMS_results.txt` (OK).

## Validation Gates

| Gate | Outcome |
|---|---|
| G0: Subtype labels ↔ `y` (server, 60 units) | Pass |
| G1 SNN: AUC/F1 = `S7x-ij` | Identical (`Δ = 0`) across all 60 units |
| G1 Dense: vs `acc30_long` (descriptive) | Max `\|ΔAUC\| = 3×10⁻⁷`, `\|ΔF1\| = 2×10⁻¹⁶` |
| G2: Simulated total spikes and hit rate = kernel (Pi) | Pass 6/6 |
| G3: Scores with PMU = without PMU (8 variants) | Pass 6/6 |

## K1 — Per-Attack-Subtype Detection (30 Units, Median; Δ vs. Base Model)

- **Exact memoization never changes a single decision**, because its scores are bit-identical to the unoptimized SNN-AE.
- **Edge-IIoTset:** `COUNT`/`TRI` grouping and 8-level `Dense-AE` leave detection virtually unchanged (`|Δ| ≤ 0.002`). The only notable drop occurs on **4-level Dense-AE for HTTP Flood**: `−0.084 [−0.170; −0.037]`, with `18/30` units dropping by more than `0.05`.
- **CICIoT2023, 4-level Dense-AE:** activation rounding degrades recall on several TCP and ICMP floods:

| Subtype | Recall Dense FP32 | Recall Dense 4-level | Δ `[CI95]` | Units Dropping > 0.05 | Flag |
|---|---|---|---|---|---|
| PSHACK Flood | 0.994 | 0.618 | −0.321 `[−0.366; −0.217]` | 27/30 | consistent drop |
| SYN Flood | 0.986 | 0.773 | −0.218 `[−0.282; −0.098]` | 26/30 | consistent drop |
| ICMP Flood | 0.997 | 0.726 | −0.222 `[−0.912; −0.000]` | 17/30 | – |
| SynonymousIP Flood | 0.996 | 0.806 | −0.189 `[−0.282; −0.066]` | 22/30 | – |
| TCP Flood | 0.998 | 0.879 | −0.116 `[−0.268; −0.055]` | 21/30 | – |

  8-level `Dense-AE` dropped on PSHACK Flood (`−0.091`; 18/30) and SYN Flood (`−0.028`).
- **CICIoT2023, SNN-AE grouping:** explains why grouping was rejected on CICIoT2023:
  - `TRI` reduced TCP Flood `−0.153` (`25/30`, consistent drop), SYN `−0.144`, SynonymousIP `−0.132`, PSHACK `−0.092`, and ICMP Flood `−0.178`.
  - `COUNT` had smaller drops: PSHACK `−0.019`, SYN `−0.012`.
- **Comparative note:** on CICIoT2023, base exact `SNN-AE` recall is lower than `Dense FP32` on PSHACK (0.653 vs 0.994), ICMP Flood (0.775 vs 0.997), and SYN Flood (0.942 vs 0.986), consistent with F1 0.808 vs 0.839. Thus, `Dense FP32` starts with higher recall on those subtypes but loses much of it when rounded to match SNN-AE speed, whereas exact `SNN-AE` remains unchanged.
- **Floor subtypes** (base recall `< 0.20` for all models: `SlowLoris`, `HTTP Flood CIC`, `UDP Flood CIC`, `Mirai-udpplain`) are reported without interpretation.

## K2 — Reuse Mechanism (Pi)

- **Within-stream recurrence dominates:**
  - Only **46%** (Edge) and **27%** (CIC) of test samples have spike patterns already seen in validation.
  - Yet exact memoization achieves **0.83** and **0.88** hit rates, showing that most hits arise from patterns recurring within the test stream after an initial miss rather than from validation prefill alone.
- **Pattern concentration** (median across 3 units):
  - Top 1,000 patterns cover **67%** (Edge) and **64%** (CIC) of test samples under exact keys;
  - Under `TRI` keys, top-1,000 coverage reaches **86%** and **79%**.
- **Per-traffic-class breakdown (`s0_f0`):**
  - **Edge floods produce compact pattern sets:** ICMP `48`, UDP `117`, and SYN `367` unique patterns out of 4,250 packets, achieving hit rates of `0.84–0.99` (ICMP 0.99, UDP 0.97, SYN 0.84) and latencies `220–281 ns`. Normal traffic produced `7,979` unique patterns over 16,747 packets (`0.75` hit rate, `379 ns`).
  - **On CICIoT2023,** ICMP/UDP/fragmentation reached `0.95–0.98` hit rates, whereas TCP Flood (`0.64`) and PSHACK (`0.57`) had more diverse patterns (`848–1,833` unique patterns).
  - **vs. 8-level Dense-AE:** exact `SNN-AE` is faster on **13 of 15** CIC subtypes, with the largest gaps on TCP floods (`TCP Flood` 374 vs 646 ns; `RSTFIN` 309 vs 550 ns).
- **Encoder spikes per sample** (`T = 3`): mean **38.4** (Edge) and **31.7** (CIC) out of 96 possible slots.

## K3 — CPU Cost per Sample (Pi, Median Across 3 Units)

| Variant | Edge Cycles | Edge Instructions | CIC Cycles | CIC Instructions | IPC (Edge) | L1D Refills / 1k Instr. (Edge) |
|---|---|---|---|---|---|---|
| Cache-free SNN-AE (`SNN_COUNT`) | 3,741 | 10,824 | 3,292 | 10,036 | 2.92 | 0.12 |
| Exact memo SNN-AE (`SNN_MEMOV3_16`) | 750 | 1,719 | 631 | 1,443 | 2.29 | 1.79 |
| SNN-AE TRI (`SNN_RQT_16`) | 609 | 1,431 | 563 | 1,340 | 2.36 | 1.91 |
| Dense-AE FP32 | 1,971 | 7,086 | 2,004 | 7,128 | 3.60 | 0.19 |
| Dense-AE zero-skip | 1,636 | 5,910 | 1,551 | 5,428 | 3.56 | 0.22 |
| Dense-AE 8-level | 763 | 1,948 | 780 | 1,974 | 2.55 | 1.52 |
| Dense-AE 4-level | 657 | 1,735 | 667 | 1,748 | 2.64 | 1.32 |

- **Memoization cuts SNN-AE work:** cycles drop **80–81%** and instructions **84–86%**. Instructions are also lower than `Dense-AE` zero-skip (`−71%` Edge, `−73%` CIC).
- **Lower IPC and ~8× higher L1D refills:** cache lookups are more memory-bound than arithmetic loops, yet total cycles remain **54–59%** lower than `Dense-AE` zero-skip.

## K4 — Memory Footprint

- **Sizes:**
  - Model weights: SNN-AE `12.9 KB` (`12,932 B`), Dense-AE `13.2 KB` (`13,188 B`);
  - Cache `2^16`: `9.7 MB` (`9,699,328 B` analytic);
  - Cache `2^14`: `2.4 MB` (`2,424,832 B`);
  - Cache `2^12`: `0.6 MB` (`606,208 B`).
- **Occupancy after prefill (`2^16`):** `10,539` (Edge, **16%**) and `7,168` (CIC, **11%**) of 65,536 slots filled.
- **Smaller capacities retain nearly full speed** (latency ratio vs. `Dense-AE` zero-skip, median 3 units):

| Capacity | Edge Exact | CIC Exact | Edge TRI |
|---|---|---|---|
| `2^12` (0.6 MB) | 0.497 (hit 0.69) | 0.409 (hit 0.83) | 0.394 |
| `2^14` (2.4 MB) | 0.465 (hit 0.78) | 0.404 (hit 0.87) | 0.376 |
| `2^16` (9.7 MB) | 0.461 (hit 0.83) | 0.412 (hit 0.88) | 0.375 |

  A **2.4 MB** (`2^14`) cache preserves nearly all speedup, reducing cache memory 4× with negligible latency impact.
- **Process RSS:** the allocator reuses existing heap pages below `2^16`, so analytic footprint and slot occupancy are reported as primary memory metrics; RSS increases by 29–117 MB at `2^18–2^20`.

## Limitations

- Pi measurements (`K2`–`K4`) are descriptive across 3 units; per-class breakdown covers `s0_f0` only.
- PMU counters measure user-space single-core execution.
- Per-subtype energy was not measured.
- `K1` is structured descriptive analysis without per-subtype hypothesis tests.
