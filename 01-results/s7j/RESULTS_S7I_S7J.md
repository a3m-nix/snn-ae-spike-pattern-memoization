# Results S7i and S7j — Vectorized SNN-AE + Cache Optimization on Raspberry Pi 5 (Latency, 30 Oct 2026 00:15–00:24)

Designs: `02-prereg-design/s7i/DESIGN_S7I_OPT.md` (`LOCK_S7I`) and `02-prereg-design/s7j/DESIGN_S7J_RQ.md` (`LOCK_S7J`).
Scope: descriptive, 3 units (`s0_f0`, `s1_f0`, `s2_f0`). Energy was measured later in `S7p` because the FNIRSI FNB-58 meter stopped responding at 00:02.

## 1. Bit-Identity and Determinism Checks

- **S7i:** 72/72 bit-identity checks passed.
  - `SNN_MEMOV3` (capacities `2^16`, `2^18`, `2^20`; cold and validation-prefilled cache) = `SNN_COUNT`.
  - `DENSE_AQV3{2,3}` = `DENSE_AQ{2,3}` (`s7f`).
- **S7j:** `SNN_RQC` and `SNN_RQT` scores were deterministic and invariant to cache capacity and initial cache contents (6/6 units).

## 2. Latency (Ratio vs. `DENSE_ZS`, Median Across 3 Units, Capture Order; Random Order Shows Same Pattern)

| Variant | Edge-IIoTset Ratio | Edge Hit Rate | CICIoT2023 Ratio | CIC Hit Rate |
|---|---|---|---|---|
| `DENSE_AQV32_16` (Dense 2-bit + cache) | 0.403 | 0.973 | 0.433 | 0.959 |
| `DENSE_AQV33_16` (Dense 3-bit + cache) | 0.474 | 0.903 | 0.501 | 0.865 |
| `SNN_MEMOV2_16` (S7g) | ~0.58 | 0.825 | ~0.47 | 0.883 |
| `SNN_MEMOV3_16` (exact, NEON miss path) | 0.465 | 0.825 | 0.412 | 0.883 |
| `SNN_RQC_16` (spike-count key) | 0.417 | 0.890 | 0.383 | 0.923 |
| `SNN_RQT_16` (tri-level key) | **0.377** | 0.925 | **0.368** | 0.936 |

- **Larger capacities (`2^18` and `2^20`)** did not improve latency for any family: hit rates rose by 0.1–1.5 percentage points, offset by slower memory accesses. `2^16` (9.7 MB) remained optimal.
- **Dense-AQ v3 matched v2**, as Dense's miss path was already auto-vectorized and rarely executed.

## 3. Accuracy (Pi, 3 Units; Median)

| Model | Edge AUC | Edge F1@p99 | CIC AUC | CIC F1@p99 |
|---|---|---|---|---|
| `DENSE` (FP32) | 0.9995 | 0.9959 | 0.9025 | 0.8413 |
| `DENSE_AQ2` | 0.9980 | 0.9760 | 0.8540 | 0.7474 |
| `DENSE_AQ3` | 0.9994 | 0.9961 | 0.8746 | 0.8335 |
| `SNN_AE` (exact, = `MEMOV3`) | 0.9994 | 0.9951 | 0.9043 | 0.8272 |
| `SNN_RQC` | 0.9994 | 0.9950 | 0.9106 | 0.8012 |
| `SNN_RQT` | 0.9993 | 0.9950 | 0.8750 | 0.7550 |

Acceptance rule (`S7d`): median per-unit `ΔAUC ≥ −0.005` and `ΔF1 ≥ −0.01` vs. `SNN_AE`.
- **Edge-IIoTset:** both `RQC` and `RQT` pass (`|Δ| ≤ 0.0006` across all 3 units).
- **CICIoT2023, `RQC`:** passes by median (`ΔF1 = −0.0053`), but unstable across units (one unit drops 0.053).
- **CICIoT2023, `RQT`:** infeasible (`ΔAUC` −0.013 to −0.038; `ΔF1` −0.07 to −0.11).

## 4. Descriptive Verdict per Dataset

**Edge-IIoTset — best SNN variant is `SNN_RQT_16`.**
- Fastest among all tested variants (`0.377 × DENSE_ZS`).
- vs. `Dense-AQ2`: `SNN_RQT_16` is faster (0.377 vs 0.403) **and** more accurate (F1 0.995 vs 0.976) — SNN dominates.
- vs. `Dense-AQ3`: `SNN_RQT_16` is ~20% faster, while `Dense-AQ3` has +0.001 higher F1 (accuracy–speed trade-off).
- vs. `Dense FP32`: `SNN_RQT_16` is ~2.65× faster with 0.001 lower F1.

**CICIoT2023 — best SNN variant is `SNN_MEMOV3_16` (exact, unchanged model).**
- vs. `Dense-AQ2`: SNN is faster (0.412 vs 0.433) and more accurate in both AUC and F1 — SNN dominates.
- vs. `Dense-AQ3`: SNN is ~18% faster with higher AUC, while `Dense-AQ3` leads on F1@p99 (Pi 0.834 vs 0.827; 30-unit server 0.830 vs 0.808).
- vs. `Dense FP32`: SNN is ~2.4× faster with comparable AUC, while `Dense FP32` leads on F1@p99.
- `RQC` is slightly faster (0.383) but lacks verified 30-unit accuracy stability.

## 5. Limitations and Follow-Up

- **Sample size:** `n = 3` units, latency only; energy (`S7p`) and 30-unit server confirmation (`S7x_ij`) follow separately.
- **Canonical patterns:** computed per unit from validation-normal data.
- **Stronger Dense comparators** (e.g., QAT or canonical quantization) were outside this post-training scope.
