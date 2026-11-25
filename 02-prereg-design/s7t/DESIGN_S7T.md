# S7t — Design: Does Exact Memoization Remain Effective Across Time Steps (T = 2, 3, 5, 7)?

**Status:** v1.0, 18 Nov 2026, locked prior to main execution (`LOCK_S7T.sha256`). Single-pass analysis without data filtering; deviations logged in dated addenda.

**Motivation:** Evaluate whether exact spike-pattern memoization (`T × 32`-bit encoder key) retains cache hit rates and latency speedups over `Dense-AE` zero-skip when `T` increases beyond `T = 3`.

## 0. Verified Pre-Design Facts (Read-Only, 18 Nov)

1. **Time-step ablation models on x86_64 server (`0-snn-ae-unified-v8-3-fair-benchmark`):** `SNN_AE` (`T = 3`), `SNN_AE_T2`, `SNN_AE_T5`, `SNN_AE_T7`, and `Dense_AE` (30 units = `3 seeds × 10 folds` per dataset).
2. **Pipeline difference:** the `v8-3` fair-benchmark pipeline uses different splits, scalers, and training parameters than the main revision pipeline (`0-snn-ae-revision`). Accordingly, comparisons across `T` are conducted strictly **within `v8-3`** (using `v8-3` `T = 3` as anchor) and are not merged into the main tables.
3. **Existing memo kernels** (`s7x_ij_kernels_x86.c`, `s7j_kernels.c`) were fixed to `T = 3`; `s7c_native.c` already supports arbitrary `T`.

## 1. Research Questions

| Code | Question | Role |
|---|---|---|
| `Q1` | How do unique test patterns, validation overlap, and `2^16` hit rate vary with `T`? | Primary (descriptive) |
| `Q2` | Does `SNN-AE` with exact memoization remain faster than zero-skipping `Dense-AE` at every `T`? | Primary (hypothesis test) |
| `Q3` | Does exact memoization remain bit-identical to cache-free `SNN-AE` at every `T`? | Gate |

(`COUNT`/`TRI` grouping and `Dense-AQ` rounding are excluded.)

## 2. Models, Data, and Variants

- **Units:** 30 units/dataset for `T ∈ {2, 3, 5, 7}` + `Dense_AE` from `v8-3`.
- **Data:** `v8-3` splits, scalers, and thresholds (verified via `G1`); full test folds.
- **Variants per unit:** `SNN_NOCACHE_T` (`s7c`), `SNN_MEMO_T` (exact memo, `2^16` validation-prefilled), `DENSE_ZS` (Dense-AE zero-skip).

## 3. Gates

| Gate | Requirement | On Failure |
|---|---|---|
| `G0` | Layer configs (`din=33`, `latent=32`, `dout=33`, `T`, LIF params) extracted via AST `SpikingLayer` without importing training scripts | Abort |
| `G1` | Native per-unit AUC/F1 matches TensorFlow outputs (`|ΔAUC| ≤ 1×10⁻³`) | Abort |
| `G2` | `SNN_MEMO_T` bit-identical to `SNN_NOCACHE_T` across all units, cold/prefill, capture/random orders | Abort |

## 4. New Kernel (`s7t_kernels_x86.c`)

- Derived from `s7x_ij_kernels_x86.c` with runtime `T` (`2 ≤ T ≤ 8`), `T × 32`-bit key, identical hash mixing over `T` words, and miss-path FP order matching `s7c` (`snn_ae`).

## 5. Execution & Analysis (x86_64 Server)

- **Timing:** pinned single thread, `nice 10`, `loadavg < 8`, capture order, shuffled variants per pass, per-unit median.
- **Q2 Primary test:** two-sided Wilcoxon signed-rank on log-ratio `SNN_MEMO_T / DENSE_ZS` across 30 units with Holm correction over 8 tests (`4 T × 2 datasets`). Verdict *"memo remains faster at T"* requires `p_Holm < 0.05` and median ratio `< 1`.
- **Q1 Descriptive:** median and `p10–p90` per `T`; cross-pipeline anchor vs `S7x_ij` (`T = 3`).

## 6. Known Limitations

- Models come from the separate `v8-3` training pipeline; exact memoization only; x86_64 only; no energy measurements.

## 7. Pre-Lock Addendum v1.0 (18 Nov, After 1-Unit Dry Run)

1. **Scalers:** June `fold_models` match `main_results_raw.csv` (`Edge-IIoTset`: `QuantileTransformer(n_quantiles=1000, output_distribution='normal', random_state=42, subsample=200000)`; `CICIoT2023`: `MinMaxScaler`). Splits/holdout `y_hash` verified identical (`G0`).
2. **Tightened `G1`:** per-unit and per-model `|AUC_native − AUC_main_results_raw| ≤ 1×10⁻³`.
3. **CPU pinning:** core 10 (`nice 10`, single thread; core 9 unavailable in cpuset).
4. **Capture order:** stable sort on `frame.time_epoch` (balanced-sampled `v8-3` streams are less contiguous than the main revision pipeline).
5. **Passes:** 15 passes, variant order shuffled per pass (`seed 7`), median per variant, `DENSE_ZS` measured in the same passes.
6. **Fixed slot size:** `s7t_kernels_x86.c` uses fixed 9 key words + 33 floats across all `T` (`11.0 MB` at `2^16`).
7. **Dry run** (1 unit, 3 passes, deleted prior to lock): `G0` passed; `G1` max `|dAUC|` `6.9×10⁻⁸` (Edge) and `3.1×10⁻⁷` (CIC); `G2` passed.
