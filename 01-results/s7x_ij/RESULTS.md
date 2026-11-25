# S7x-ij — 30-Unit x86 Confirmation Results (S7i v3 and S7j RQ)

- **Date:** 30 Oct 2026.
- **Machine:** x86_64 server (`Xeon Silver 4416+`, AVX2, `gcc 11.4 -O3 -march=native`), core 9, `nice -n 10`, single-threaded.
- **Design:** `DESIGN.md` (`sha256: 27d0e122…`), locked 30 Oct 00:33:49 WIB prior to accuracy and timing phases.
- **Execution:** accuracy 00:33–00:36, timing 00:36–00:53; single-pass analysis `analyze_s7x_ij.py` (`sha256: fe25f039…`); no exclusions or reruns.

Below is the structured summary; full automated tables are appended at the end and stored as CSVs in `results/`.

## 1. Correctness

- **Checks:** all **2,160** combinations (`60 units × 36`) passed.
  - `snn_memo_v3` is bit-identical to `SNN_COUNT`.
  - `dense_aq_memo_v3` (`b = 2, 3`) is bit-identical to `dense_aq_memo`.
  - `snn_rq_memo` (`COUNT`, `TRI`) is bit-identical to the cache-free scalar reference across capacities `2^16`, `2^18`, and `2^20` (both cold and validation-prefilled caches), establishing invariance to capacity and initial cache state.
- **Cross-check:** kernel `SNN_EXACT` vs. `inputs/acc30_long.csv` (Keras `SNN_AE_FP32`): median `|ΔAUC| = 0` (Edge) and `5×10⁻⁹` (CIC); median `|ΔF1| = 0` on both datasets.

## 2. Accuracy: RQ vs. Exact SNN (`n = 30` per Dataset; Rule: Median `ΔAUC ≥ −0.005` and Median `ΔF1@p99 ≥ −0.01`)

| Dataset | Model | Median ΔAUC `[CI95]` | Median ΔF1 `[CI95]` | ΔF1 p10 / min | Units ΔAUC < −0.005 | Units ΔF1 < −0.01 | Verdict |
|---|---|---|---|---|---|---|---|
| Edge-IIoTset | `SNN_RQC` | −0.000002 `[−0.000005; −0.0000005]` | −0.00003 `[−0.00014; 0.00005]` | −0.0004 / −0.0014 | 0/30 | 0/30 | robustly feasible |
| Edge-IIoTset | `SNN_RQT` | −0.00004 `[−0.00006; −0.00003]` | −0.0004 `[−0.0006; −0.0001]` | −0.0010 / −0.028 (`s1_f7`) | 0/30 | 1/30 | robustly feasible |
| CICIoT2023 | `SNN_RQC` | **−0.0057** `[−0.0105; −0.0009]` | −0.0037 `[−0.0332; 0.0011]` | −0.054 / **−0.179** (`s2_f2`) | 16/30 | 13/30 | **infeasible** |
| CICIoT2023 | `SNN_RQT` | **−0.0209** `[−0.0321; −0.0130]` | **−0.0645** `[−0.0791; −0.0386]` | −0.116 / −0.186 (`s0_f1`) | 24/30 | 27/30 | **infeasible** |

**Edge-IIoTset:** both RQ variants leave accuracy virtually unchanged (`RQC`: 0/30 units below thresholds; `RQT`: only `s1_f7` with `ΔF1 = −0.028`, all others `≥ −0.0015`).

**CICIoT2023:** both RQ variants are infeasible under the pre-registered `S7d` thresholds (`RQC` fails AUC median at `−0.0057` with wide dispersion; `RQT` drops `−0.0645` F1 across 27/30 units). In keeping with pre-registration, thresholds were not adjusted post-hoc.

## 3. Latency — Primary Family (Holm over 36; Capture Order Primary)

Each cell reports median ratio `t_SNN / t_Dense`, verdict, and number of units (out of 30) where SNN was faster. **†** indicates an accuracy-infeasible RQ variant on that dataset, excluded from efficiency claims (`S7j` rule).

| Dataset | SNN Variant | vs `DENSE_ZS` | vs `DENSE_AQV32_16` | vs `DENSE_AQV33_16` |
|---|---|---|---|---|
| Edge | `SNN_MEMOV3_16` | 0.403 SNN faster (30) | 1.033 no sig. diff (13; `p_Holm=1`) | 0.974 no sig. diff (16; `p_Holm=0.14`) |
| Edge | `SNN_RQC_16` | 0.380 SNN faster (30) | 0.975 no sig. diff (19; `p_Holm=0.084`) | 0.918 SNN faster (28) |
| Edge | `SNN_RQT_16` | 0.356 SNN faster (30) | 0.912 SNN faster (29) | 0.862 SNN faster (30) |
| CIC | `SNN_MEMOV3_16` | 0.396 SNN faster (30) | 0.966 SNN faster (21; `p_Holm=0.007`) | 0.910 SNN faster (27) |
| CIC | `SNN_RQC_16` † | 0.379 SNN faster (30) | 0.912 SNN faster (29) | 0.859 SNN faster (30) |
| CIC | `SNN_RQT_16` † | 0.367 SNN faster (30) | 0.886 SNN faster (30) | 0.840 SNN faster (30) |

- **Random order** matched capture order in 17/18 cells (only CIC `MEMOV3` vs `AQ2` shifted to `0.992`, `p_Holm = 1`).
- **Dense did not win significantly in any cell** once both hit and miss paths were vectorized (`v3`).
- **Pre-registered efficiency claims (capture):**
  - Edge-IIoTset: `MEMOV3` faster than `ZS`; `RQC` faster than `ZS` and `AQ3`; `RQT` faster than `ZS`, `AQ2`, and `AQ3`.
  - CICIoT2023: `MEMOV3` faster than `ZS`, `AQ2` (capture only), and `AQ3`; `RQ` excluded due to accuracy infeasibility.

## 4. Latency — Secondary Family (`RQ` vs. `MEMOV3`; Holm over 8)

All 8 cells yielded `"RQ faster"` (`p_Holm = 1.5×10⁻⁸`; 29–30/30 units):
- `RQC / MEMOV3`: `0.94–0.95` (Edge), `0.95` (CIC)
- `RQT / MEMOV3`: `0.89` (Edge), `0.92` (CIC)

Consistent with higher hit rates (capture medians: Edge `MEMOV3 0.827`, `RQC 0.880`, `RQT 0.923`; CIC `MEMOV3 0.875`, `RQC 0.916`, `RQT 0.932`).

## 5. Descriptive Comparison with Pi (Ratio vs. `DENSE_ZS`, Capture)

| Variant | Edge x86 (`n=30`) | Edge Pi (`n=3`) | CIC x86 (`n=30`) | CIC Pi (`n=3`) |
|---|---|---|---|---|
| `AQ2` | 0.398 | 0.403 | 0.404 | 0.433 |
| `AQ3` | 0.419 | 0.474 | 0.421 | 0.501 |
| `MEMOV3` | 0.403 | 0.465 | 0.396 | 0.412 |
| `RQC` | 0.380 | 0.417 | 0.379 | 0.383 |
| `RQT` | 0.356 | 0.377 | 0.367 | 0.368 |

Directional findings on Pi are confirmed across 30 units on x86, though absolute ratios differ across architectures.

## 6. Noise, Load, and Limitations

- 1-minute `loadavg` max `1.98–4.33`; inter-pass spread median `≤ 2%` in most cells (bimodal `~0.11` in 16/30 units for Edge capture `SNN_RQC_16` due to shared-server jitter, mitigated by 30-pass medians).
- Limitations: x86 AVX2 confirms directionality rather than replacing ARM NEON Pi metrics; `Dense-AQ` accuracy is taken from `inputs/acc30_long.csv`; `R` tables use NumPy tie-breaking.

## Automated Section (analyze_s7x_ij.py)

**Correctness:** all 2,160 checks across 60 units passed: **True**

### Accuracy: RQ vs. Exact SNN (Δ = RQ − exact, per unit, n = 30)

| dataset      | model   |   median_auc_exact |   median_auc_rq |   d_auc_median |   d_auc_ci95_low |   d_auc_min |   median_f1_exact |   median_f1_rq |   d_f1_p99_median |   d_f1_p99_ci95_low |   d_f1_p99_p10 |   d_f1_p99_min |   units_dauc_below_-0.005 |   units_df1_below_-0.01 | worst_unit_df1   | verdict     |
|:-------------|:--------|-------------------:|----------------:|---------------:|-----------------:|------------:|------------------:|---------------:|------------------:|--------------------:|---------------:|---------------:|--------------------------:|------------------------:|:-----------------|:------------|
| edge_iiotset | SNN_RQC |             0.9995 |          0.9995 |     -2.091e-06 |       -4.55e-06  |  -0.0002801 |            0.9948 |         0.9947 |        -2.892e-05 |          -0.0001377 |     -0.0004289 |      -0.001431 |                         0 |                       0 | s1_f5            | robustly feasible |
| edge_iiotset | SNN_RQT |             0.9995 |          0.9994 |     -4.341e-05 |       -6.062e-05 |  -0.0003586 |            0.9948 |         0.9944 |        -0.0003959 |          -0.0005884 |     -0.001044  |      -0.02784  |                         0 |                       1 | s1_f7            | robustly feasible |
| ciciot2023   | SNN_RQC |             0.9135 |          0.9068 |     -0.005692  |       -0.01045   |  -0.05343   |            0.808  |         0.7756 |        -0.003716  |          -0.0332    |     -0.05355   |      -0.1789   |                        16 |                      13 | s2_f2            | infeasible |
| ciciot2023   | SNN_RQT |             0.9135 |          0.8905 |     -0.02086   |       -0.03206   |  -0.06118   |            0.808  |         0.7505 |        -0.06448   |          -0.07914   |     -0.1159    |      -0.1857   |                        24 |                      27 | s0_f1            | infeasible |

Cross-check SNN_EXACT (kernel) vs acc30 SNN_AE_FP32 (Keras): median |ΔAUC| edge_iiotset 0.00e+00, ciciot2023 5.44e-09; median |ΔF1| edge_iiotset 0.00e+00, ciciot2023 0.00e+00

### Latency — Primary Family (SNN vs. Dense; Holm over 36 tests)

| dataset      | order   | variant       | comparator     |   median_ratio |   ratio_ci95_low |   ratio_ci95_high |   units_variant_faster |   rank_biserial_r |    p_holm | verdict                | accuracy_feasible   |
|:-------------|:--------|:--------------|:---------------|---------------:|-----------------:|------------------:|-----------------------:|------------------:|----------:|:-----------------------|:--------------------|
| edge_iiotset | capture | SNN_MEMOV3_16 | DENSE_ZS       |         0.4033 |           0.3874 |            0.4231 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | capture | SNN_MEMOV3_16 | DENSE_AQV32_16 |         1.033  |           0.9645 |            1.075  |                     13 |           -0.1312 | 1         | no significant diff    | True                |
| edge_iiotset | capture | SNN_MEMOV3_16 | DENSE_AQV33_16 |         0.9744 |           0.9106 |            1.02   |                     16 |            0.471  | 0.1405    | no significant diff    | True                |
| edge_iiotset | capture | SNN_RQC_16    | DENSE_ZS       |         0.3802 |           0.3667 |            0.3932 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | capture | SNN_RQC_16    | DENSE_AQV32_16 |         0.9754 |           0.9129 |            1.009  |                     19 |            0.5183 | 0.08433   | no significant diff    | True                |
| edge_iiotset | capture | SNN_RQC_16    | DENSE_AQV33_16 |         0.9182 |           0.8606 |            0.9548 |                     28 |            0.9613 | 7.991e-07 | SNN faster             | True                |
| edge_iiotset | capture | SNN_RQT_16    | DENSE_ZS       |         0.3556 |           0.3447 |            0.3681 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | capture | SNN_RQT_16    | DENSE_AQV32_16 |         0.9122 |           0.8421 |            0.9545 |                     29 |            0.9957 | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | capture | SNN_RQT_16    | DENSE_AQV33_16 |         0.8624 |           0.8077 |            0.901  |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | random  | SNN_MEMOV3_16 | DENSE_ZS       |         0.3925 |           0.3802 |            0.4111 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | random  | SNN_MEMOV3_16 | DENSE_AQV32_16 |         1.046  |           0.98   |            1.089  |                     12 |           -0.3548 | 0.2758    | no significant diff    | True                |
| edge_iiotset | random  | SNN_MEMOV3_16 | DENSE_AQV33_16 |         0.9791 |           0.9143 |            1.025  |                     15 |            0.4538 | 0.1466    | no significant diff    | True                |
| edge_iiotset | random  | SNN_RQC_16    | DENSE_ZS       |         0.3721 |           0.3612 |            0.3813 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | random  | SNN_RQC_16    | DENSE_AQV32_16 |         0.9767 |           0.9274 |            1.02   |                     17 |            0.4065 | 0.2091    | no significant diff    | True                |
| edge_iiotset | random  | SNN_RQC_16    | DENSE_AQV33_16 |         0.9174 |           0.8592 |            0.9558 |                     27 |            0.957  | 9.611e-07 | SNN faster             | True                |
| edge_iiotset | random  | SNN_RQT_16    | DENSE_ZS       |         0.3454 |           0.3405 |            0.3566 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| edge_iiotset | random  | SNN_RQT_16    | DENSE_AQV32_16 |         0.9167 |           0.8531 |            0.9652 |                     27 |            0.957  | 9.611e-07 | SNN faster             | True                |
| edge_iiotset | random  | SNN_RQT_16    | DENSE_AQV33_16 |         0.8621 |           0.806  |            0.9032 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| ciciot2023   | capture | SNN_MEMOV3_16 | DENSE_ZS       |         0.3955 |           0.3371 |            0.4157 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| ciciot2023   | capture | SNN_MEMOV3_16 | DENSE_AQV32_16 |         0.966  |           0.9177 |            0.9836 |                     21 |            0.6688 | 0.006975  | SNN faster             | True                |
| ciciot2023   | capture | SNN_MEMOV3_16 | DENSE_AQV33_16 |         0.9098 |           0.8591 |            0.9341 |                     27 |            0.9656 | 6.519e-07 | SNN faster             | True                |
| ciciot2023   | capture | SNN_RQC_16    | DENSE_ZS       |         0.3792 |           0.3198 |            0.392  |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | capture | SNN_RQC_16    | DENSE_AQV32_16 |         0.912  |           0.8798 |            0.9421 |                     29 |            0.9828 | 2.086e-07 | SNN faster             | False               |
| ciciot2023   | capture | SNN_RQC_16    | DENSE_AQV33_16 |         0.859  |           0.8185 |            0.8939 |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | capture | SNN_RQT_16    | DENSE_ZS       |         0.3668 |           0.3106 |            0.382  |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | capture | SNN_RQT_16    | DENSE_AQV32_16 |         0.8864 |           0.8599 |            0.9139 |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | capture | SNN_RQT_16    | DENSE_AQV33_16 |         0.8403 |           0.795  |            0.8654 |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | random  | SNN_MEMOV3_16 | DENSE_ZS       |         0.3777 |           0.348  |            0.3988 |                     30 |            1      | 6.706e-08 | SNN faster             | True                |
| ciciot2023   | random  | SNN_MEMOV3_16 | DENSE_AQV32_16 |         0.9921 |           0.9459 |            1.028  |                     16 |            0.1398 | 1         | no significant diff    | True                |
| ciciot2023   | random  | SNN_MEMOV3_16 | DENSE_AQV33_16 |         0.9122 |           0.881  |            0.9405 |                     25 |            0.9183 | 5.718e-06 | SNN faster             | True                |
| ciciot2023   | random  | SNN_RQC_16    | DENSE_ZS       |         0.3553 |           0.3253 |            0.3694 |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | random  | SNN_RQC_16    | DENSE_AQV32_16 |         0.9393 |           0.9037 |            0.9706 |                     25 |            0.8108 | 0.000242  | SNN faster             | False               |
| ciciot2023   | random  | SNN_RQC_16    | DENSE_AQV33_16 |         0.8603 |           0.8406 |            0.8942 |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | random  | SNN_RQT_16    | DENSE_ZS       |         0.3448 |           0.3139 |            0.3595 |                     30 |            1      | 6.706e-08 | SNN faster             | False               |
| ciciot2023   | random  | SNN_RQT_16    | DENSE_AQV32_16 |         0.9118 |           0.8798 |            0.9401 |                     29 |            0.9828 | 2.086e-07 | SNN faster             | False               |
| ciciot2023   | random  | SNN_RQT_16    | DENSE_AQV33_16 |         0.8346 |           0.8144 |            0.8687 |                     30 |            1      | 6.706e-08 | SNN faster             | False               |

### Latency — Secondary Family (RQ vs. MEMOV3; Holm over 8 tests)

| dataset      | order   | variant    | comparator    |   median_ratio |   ratio_ci95_low |   ratio_ci95_high |   units_variant_faster |   rank_biserial_r |   p_holm | verdict        |
|:-------------|:--------|:-----------|:--------------|---------------:|-----------------:|------------------:|-----------------------:|------------------:|---------:|:---------------|
| edge_iiotset | capture | SNN_RQC_16 | SNN_MEMOV3_16 |         0.9465 |           0.9415 |            0.9498 |                     30 |            1      | 1.49e-08 | RQ faster      |
| edge_iiotset | capture | SNN_RQT_16 | SNN_MEMOV3_16 |         0.8874 |           0.8779 |            0.8927 |                     30 |            1      | 1.49e-08 | RQ faster      |
| edge_iiotset | random  | SNN_RQC_16 | SNN_MEMOV3_16 |         0.9431 |           0.9371 |            0.9475 |                     30 |            1      | 1.49e-08 | RQ faster      |
| edge_iiotset | random  | SNN_RQT_16 | SNN_MEMOV3_16 |         0.8851 |           0.875  |            0.8896 |                     30 |            1      | 1.49e-08 | RQ faster      |
| ciciot2023   | capture | SNN_RQC_16 | SNN_MEMOV3_16 |         0.9507 |           0.9428 |            0.9564 |                     30 |            1      | 1.49e-08 | RQ faster      |
| ciciot2023   | capture | SNN_RQT_16 | SNN_MEMOV3_16 |         0.9235 |           0.9183 |            0.9347 |                     30 |            1      | 1.49e-08 | RQ faster      |
| ciciot2023   | random  | SNN_RQC_16 | SNN_MEMOV3_16 |         0.9473 |           0.9363 |            0.9543 |                     29 |            0.9957 | 1.49e-08 | RQ faster      |
| ciciot2023   | random  | SNN_RQT_16 | SNN_MEMOV3_16 |         0.9155 |           0.9051 |            0.9262 |                     30 |            1      | 1.49e-08 | RQ faster      |

### Descriptive Summary (Per-Unit Median; Ratio vs. DENSE_ZS; Pi Column = S7i/S7j, 3 Units, Capture)

| dataset      | order   | variant        |   median_ns |   median_ratio_vs_dense_zs |   min_ratio |   max_ratio |   median_hit_rate |   median_rel_spread |   max_loadavg |   pi_ratio_vs_dense_zs |
|:-------------|:--------|:---------------|------------:|---------------------------:|------------:|------------:|------------------:|--------------------:|--------------:|-----------------------:|
| ciciot2023   | capture | DENSE_AQV32_16 |       241.3 |                     0.4037 |      0.3173 |      0.4643 |            0.9562 |            0.006179 |         4.262 |                  0.433 |
| ciciot2023   | capture | DENSE_AQV33_16 |       255.5 |                     0.4209 |      0.3445 |      0.4906 |            0.8678 |            0.01035  |         4.262 |                  0.501 |
| ciciot2023   | capture | DENSE_ZS       |       592.3 |                     1      |      1      |      1      |          nan      |            0.004928 |         4.262 |                nan     |
| ciciot2023   | capture | SNN_MEMOV3_16  |       236.5 |                     0.3955 |      0.2879 |      0.4913 |            0.8745 |            0.009016 |         4.262 |                  0.412 |
| ciciot2023   | capture | SNN_RQC_16     |       225.2 |                     0.3792 |      0.2757 |      0.4761 |            0.9157 |            0.009042 |         4.262 |                  0.383 |
| ciciot2023   | capture | SNN_RQT_16     |       219   |                     0.3668 |      0.2716 |      0.4603 |            0.9324 |            0.008807 |         4.262 |                  0.368 |
| ciciot2023   | random  | DENSE_AQV32_16 |       250.9 |                     0.3721 |      0.3136 |      0.466  |            0.9488 |            0.008846 |         4.333 |                nan     |
| ciciot2023   | random  | DENSE_AQV33_16 |       275.7 |                     0.3981 |      0.3364 |      0.5076 |            0.8497 |            0.01147  |         4.333 |                nan     |
| ciciot2023   | random  | DENSE_ZS       |       669.7 |                     1      |      1      |      1      |          nan      |            0.00544  |         4.333 |                nan     |
| ciciot2023   | random  | SNN_MEMOV3_16  |       255.8 |                     0.3777 |      0.2935 |      0.517  |            0.8492 |            0.01015  |         4.333 |                nan     |
| ciciot2023   | random  | SNN_RQC_16     |       244.1 |                     0.3553 |      0.2864 |      0.5016 |            0.892  |            0.01205  |         4.333 |                nan     |
| ciciot2023   | random  | SNN_RQT_16     |       233.7 |                     0.3448 |      0.2777 |      0.4805 |            0.9118 |            0.01225  |         4.333 |                nan     |
| edge_iiotset | capture | DENSE_AQV32_16 |       244.6 |                     0.3982 |      0.3548 |      0.4352 |            0.9672 |            0.01075  |         1.978 |                  0.403 |
| edge_iiotset | capture | DENSE_AQV33_16 |       260.5 |                     0.4194 |      0.3761 |      0.4576 |            0.8912 |            0.01648  |         1.978 |                  0.474 |
| edge_iiotset | capture | DENSE_ZS       |       638.3 |                     1      |      1      |      1      |          nan      |            0.01313  |         1.978 |                nan     |
| edge_iiotset | capture | SNN_MEMOV3_16  |       256.2 |                     0.4033 |      0.3565 |      0.4489 |            0.8267 |            0.01849  |         1.978 |                  0.465 |
| edge_iiotset | capture | SNN_RQC_16     |       242.6 |                     0.3802 |      0.3328 |      0.425  |            0.8797 |            0.1068   |         1.978 |                  0.417 |
| edge_iiotset | capture | SNN_RQT_16     |       228.4 |                     0.3556 |      0.313  |      0.4022 |            0.9226 |            0.01622  |         1.978 |                  0.377 |
| edge_iiotset | random  | DENSE_AQV32_16 |       249.1 |                     0.3842 |      0.346  |      0.4256 |            0.9649 |            0.01302  |         3.123 |                nan     |
| edge_iiotset | random  | DENSE_AQV33_16 |       267.7 |                     0.411  |      0.357  |      0.4513 |            0.8852 |            0.01497  |         3.123 |                nan     |
| edge_iiotset | random  | DENSE_ZS       |       666.7 |                     1      |      1      |      1      |          nan      |            0.006037 |         3.123 |                nan     |
| edge_iiotset | random  | SNN_MEMOV3_16  |       264.3 |                     0.3925 |      0.3524 |      0.4382 |            0.8198 |            0.01628  |         3.123 |                nan     |
| edge_iiotset | random  | SNN_RQC_16     |       249.6 |                     0.3721 |      0.3318 |      0.4157 |            0.8733 |            0.01761  |         3.123 |                nan     |
| edge_iiotset | random  | SNN_RQT_16     |       234.1 |                     0.3454 |      0.3096 |      0.3891 |            0.9146 |            0.01376  |         3.123 |                nan     |
