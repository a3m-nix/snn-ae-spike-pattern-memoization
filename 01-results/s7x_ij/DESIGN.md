# S7x-ij — 30-Unit x86 Confirmation Design for S7i (v3) and S7j (RQ)

Date: 30 Oct 2026. Written after the correctness check phase (without timing or detection metrics) and **before** accuracy and timing phases were executed. This file is hashed in `logs/design_sha256.txt`; `s7x_ij.py` refuses to run accuracy/timing phases if the design hash mismatches or if any of the 60 units fail correctness checks. Code hashes are recorded in `logs/lock_sha256.txt`.

## 1. Objectives

Re-evaluate the descriptive 3-unit Raspberry Pi findings (`01-results/s7j/RESULTS_S7I_S7J.md`) across all 30 units per dataset:
1. **Accuracy (`SNN_RQC`, `SNN_RQT`):** assess whether spike-count (`COUNT`) and tri-level (`TRI`) grouped SNN-AE variants satisfy feasibility criteria against exact SNN-AE across 30 units, and measure per-unit dispersion.
2. **Latency (`SNN_MEMOV3_16`, `SNN_RQC_16`, `SNN_RQT_16` vs. `DENSE_ZS`, `DENSE_AQV32_16`, `DENSE_AQV33_16`):** test latency differences on x86_64 across 30 units per dataset.

Reference Pi latency ratios vs. `DENSE_ZS` (capture order):

| Variant | Edge-IIoTset | CICIoT2023 |
|---|---|---|
| `AQ2` | 0.403 | 0.433 |
| `AQ3` | 0.474 | 0.501 |
| `MEMOV3` | 0.465 | 0.412 |
| `RQC` | 0.417 | 0.383 |
| `RQT` | 0.377 | 0.368 |

## 2. Kernels and Correctness Phase (Executed Before This Document)

- **Port:** `s7x_ij_kernels_x86.c` ports `s7i_kernels.c` and `s7j_kernels.c` to AVX2 (`4 × 8` lanes, `fmadd`, `cmp_ps GT_OQ`, `blendv`, `movemask`), with symmetric vectorized hit and miss paths for both families. Dense v3 ReLU uses `max_ps(0, h)` preserving `-0` and `NaN` semantics.
- **Compilation:** `gcc 11.4 -O3 -march=native -shared -fPIC`.
- **References:**
  - `s7c_native_copy.c`: `SNN_COUNT` and `DENSE_ZS`.
  - `s7f_memo.c`: `snn_memo` and `dense_aq_memo`.
  - `s7x_ij_ref.c`: scalar cache-free reference for `RQ` using identical encoder/decoder and canonical masks (`s7j_kernels.c`).
- **Canonical patterns `R`:** `rq_table` mirrors `s7j_rpi.py` (most frequent spike pattern per neuron per class on validation-normal per unit; empty classes use the same default fallback as Pi).
- **Check criteria** across `60 units × {capture, random} × {cold, validation prefill}`:
  - `snn_memo_v3` bit-identical to `SNN_COUNT` (`2^16`);
  - `dense_aq_memo_v3` (`b = 2, 3`) bit-identical to `dense_aq_memo` (`2^16`);
  - `snn_rq_memo` (`COUNT`, `TRI`) bit-identical to `snn_rq_ref` at `2^16`, `2^18`, and `2^20` with finite scores (invariance to capacity and initial cache state).

  Any single failure aborts execution. Outputs (`36` combinations per unit = `2,160` total) are in `results/check/` and `logs/check.log`.

## 3. Accuracy Phase (`n = 30` Units per Dataset)

- **Models:** `SNN_EXACT` (`SNN_COUNT`, bit-identical to `SNN_MEMOV3`), `SNN_RQC`, and `SNN_RQT` (evaluated at `2^16` validation-prefilled cache, proven invariant by check phase).
- **Data:** full test fold per unit; threshold = 99th percentile of validation-normal scores of the same model.
- **Metrics** (`s7g_rpi.det_metrics`): AUC, AP, F1/recall/FPR at p99, and recall at FPR `0.1 / 0.5 / 1 / 5%`.
- **Per-unit delta:** `Δ = RQ − SNN_EXACT`.
- **Summary per dataset × RQ variant:** median `Δ` with 95% percentile bootstrap CI (10,000 resamples, seed 42); min, p10, p25, p75, max; counts with `ΔAUC < −0.005` and `ΔF1 < −0.01`; worst unit; two-sided uncorrected Wilcoxon.
- **Feasibility rule (`S7d`, unchanged):** median `ΔAUC ≥ −0.005` **and** median `ΔF1@p99 ≥ −0.01`.
  - **Robustly feasible:** both median and lower 95% CI bound meet the threshold.
  - **Feasible (non-robust):** median meets threshold, lower CI bound does not.
  - **Infeasible:** otherwise.
- **Descriptive cross-check:** `SNN_EXACT` kernel AUC/F1 compared against `inputs/acc30_long.csv` (Keras FP32 scores).

## 4. Timing Phase (`S7x` Protocol, Unchanged)

- **Variants:** `DENSE_ZS` (cache-free), `DENSE_AQV32_16`, `DENSE_AQV33_16`, `SNN_MEMOV3_16`, `SNN_RQC_16`, `SNN_RQT_16` (`2^16` caches reset and validation-prefilled outside timed region).
- **Stream orders:** `capture` (primary; sorted by `source_file, source_row`) and `random` (secondary; `RandomState(43)`).
- **Procedure:** 1 untimed warmup pass + 30 timed passes per unit and order, with all 6 variants shuffled per pass (`RandomState(7)`). Time = `perf_counter_ns / n`; per-unit statistic = median of 30 passes.
- **Environment:** single-threaded, pinned to core 9, `nice -n 10`, `performance` governor, `loadavg` logged; no exclusions or selective reruns.

## 5. Latency Analysis and Decision Rules (`analyze_s7x_ij.py`)

- **Primary family (Holm across 36 tests):** 3 SNN variants × 3 Dense comparators × 2 datasets × 2 orders. Paired two-sided Wilcoxon signed-rank (`n = 30`, `zero_method="wilcox"`) on `t_Dense − t_SNN`; effect size = median ratio `t_SNN / t_Dense` with 95% bootstrap CI (10,000, seed 42), rank-biserial correlation, and faster-unit count.
- **Secondary family (Holm across 8 tests):** `RQC` and `RQT` vs. `MEMOV3` per dataset × order.
- **Verdict rules:** `"SNN faster"` / `"RQ faster"` if `p_Holm < 0.05` and median ratio `< 1`; `"Dense faster"` / `"MEMOV3 faster"` if `p_Holm < 0.05` and median ratio `> 1`; otherwise `"no significant difference"`.
- **Accuracy linkage:** latency verdicts for accuracy-infeasible `RQ` variants are reported for completeness but flagged and excluded from efficiency claims (`S7j` rule).

## 6. Pre-Registered Limitations

- x86 AVX2 tests directionality rather than replacing ARM NEON Raspberry Pi measurements.
- Pi (`S7i`/`S7j`) 3-unit results and `S7x` v2 results were already observed; variants, `2^16` capacity, and rules follow `S7j`/`S7x` unchanged.
- `Dense-AQ` accuracy is cited from `acc30_long.csv` without recomputation.
- Canonical tables `R` are computed via NumPy (BLAS), affecting only validation-based `R` tie-breaking at boundaries, not kernel correctness.
