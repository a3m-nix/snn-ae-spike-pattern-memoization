# S7k — Design: Per-Attack Impact, Spike Activity, CPU Counters, and Cache Memory

Status: **design v1.1 (9 Nov 2026), locked prior to measurement (`LOCK_S7K.sha256`).** Single-pass analysis; no data filtering; any deviations logged in addenda.

Goal: supply per-subtype accuracy breakdown (`K1`), pattern-reuse mechanics (`K2`), ARM PMU counters (`K3`), and cache memory scaling (`K4`) for the optimized variants. Energy is excluded (covered by `S7p`, 30 Oct).

## 1. Research Questions

| Code | Question | Platform | Role |
|---|---|---|---|
| `K1` | Which attack subtypes lose detection when the model is modified (SNN grouping; Dense activation rounding), and by how much? | Server, 30 units/dataset | **Primary** |
| `K2` | Why does reuse succeed: how many unique patterns occur, how concentrated are they, and how do hit rate, latency, and spikes vary by traffic class? | Pi | Mechanism (descriptive) |
| `K3` | What is the per-sample CPU cost (`cycles`, `instructions`, `L1D_CACHE` access/refill, `MEM_ACCESS`) for each final variant? | Pi | Descriptive |
| `K4` | What is the cache memory footprint across capacities compared with model weights? | Pi | Descriptive |

## 2. Variants

Identical to `S7x-ij`/`S7j` (unchanged kernels): `SNN_COUNT` (cache-free SNN reference), `SNN_MEMOV3_16` (exact memo), `SNN_RQC_16` (`COUNT`), `SNN_RQT_16` (`TRI`), `DENSE`, `DENSE_ZS`, `DENSE_AQV32_16` (4-level), `DENSE_AQV33_16` (8-level). Cache capacity is `2^16` slots prefilled with validation-normal (except in `K4`).

## 3. K1 — Per-Attack-Subtype Detection (x86_64 Server, Primary)

- **Data:** 30 units/dataset (3 seeds × 10 folds), full test folds; subtype labels (`label_type`) joined from `sample.parquet` using exact `S7x-ij` test indices (Edge: 4 attack subtypes; CIC: 15 attack subtypes; 4,250 samples per subtype per unit).
- **Scoring:** `s7x_ij_kernels_x86.c` with `2^16` validation-prefilled cache; threshold = p99 validation-normal of the same model (`= S7x-ij`); `DENSE_ZS` represents Dense-AE FP32.
- **Per unit × variant × subtype metrics:** recall at p99, subtype-vs-normal AUC, `Δrecall` vs base model (`SNN_EXACT` or `DENSE_ZS`), decision-change rate, and normal FPR.
- **Summary & descriptive rules:** per-dataset × variant × subtype median with 95% percentile bootstrap CI (10,000 resamples, seed 42), p10/p90, and count of units with `Δrecall < −0.05`.
  - **Consistent drop:** median `Δrecall < −0.05` **and** `≥ 24/30` units drop `> 0.05` (symmetric rule for consistent rise).
  - **Floor:** subtypes with base median recall `< 0.20` (e.g., `SlowLoris`, `HTTP Flood CIC`) are reported without interpretation.
  - No per-subtype hypothesis tests (`K1` is structured descriptive).
- **Gate G1:** SNN per-unit AUC/F1 must match `S7x-ij/results/accuracy_long.csv` within `|Δ| ≤ 1e-12`; Dense scores cross-checked against `acc30_long.csv` (`|Δ| ≤ 1e-3`).

## 4. K2 — Reuse Mechanism (Pi)

- **Units:** `s0_f0`, `s1_f0`, `s2_f0` per dataset (`s7f/rpi_package`); per-class analysis on `s0_f0` using `test_raw.parquet` (`100%` `sample_id` match).
- **Helper `s7k_keys.c`:** exact encoder copied from `s7j_kernels.c` emitting per-sample keys (`exact`, `COUNT`, `TRI`).
- **Gate G2:** total encoder spikes from keys must equal kernel `stats[2]`, and simulated `2^16` cache hit rate must equal kernel hit rate across all 3 modes; mismatches abort execution.
- **Metrics:** (a) unique keys in validation and test; (b) fraction of test samples seen in validation; (c) top-`k` (`10, 100, 1,000`) coverage; (d) encoder spikes/sample; (e) per-traffic-class hit rate and median latency (15 passes, capture order, validation-prefilled; `s0_f0` only).

## 5. K3 — Hardware CPU Counters (Pi)

- **`perf_event_open` (user space, core 3):** `cycles`, `instructions`, `L1D_CACHE` (`0x04`), `L1D_CACHE_REFILL` (`0x03`), `MEM_ACCESS` (`0x13`); derived IPC and refills per 1,000 instructions.
- **Scope:** 8 variants × 3 units × 2 datasets, capture order, validation-prefilled, median over 5 full-test passes (`pmu_begin`/`pmu_end` wrapping each kernel call).
- **Gate G3:** PMU-instrumented scores must be bit-identical to uninstrumented calls.

## 6. K4 — Memory Footprint (Pi)

- **Analytic:** cache bytes at `2^12, 2^14, 2^16, 2^18, 2^20` for SNN (`16 B` key + `33 floats` = `148 B/slot`) and Dense-AQ, plus weight sizes.
- **Measured:** process `VmRSS` (`/proc/self/status`) before allocation, after allocation, and after validation prefill on `s0_f0`.
- **Small-capacity hit rates (`2^12`, `2^14`):** measured to complete the capacity curve (`2^16–2^20` come from `S7j`).

## 7. Execution, Dry Run, and Pre-Registered Limitations

- **Pi:** `systemd-run` under `e37-lock`, core 3; live service untouched; sequence `check (G2, G3) → K2 → K3 → K4`.
- **Dry run (v1.1):** executed on `edge_iiotset s0_f0` (1 repeat on Pi; 1 unit on server) and deleted prior to lock; only `--out` CLI option added afterward.
- **Limitations:** per-class `K2` covers `s0_f0` only; PMU covers user-space single core; `K3`/`K4` on Pi only; no per-subtype energy.
