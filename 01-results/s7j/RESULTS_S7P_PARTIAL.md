# S7p — Partial Energy Results (30 Oct 2026, ~16:45 WIB)

Design: `02-prereg-design/s7p/DESIGN_S7P_POWER.md` and `02-prereg-design/s7p/ADDENDUM_S7P_01.md`.
*(Note: superseded by the completed 384-condition summary in `01-results/s7p/RESULTS_S7P.md` and `01-results/s7p/RESULTS_S7P_auto.md`.)*

**Data status at time of writing:**
- **Complete:** `S7j` (108/108 valid conditions) and `S7h edge_iiotset` (30/30 valid conditions).
- **Pending:** `S7h ciciot2023` and `S7g-more` (completed later via `ADDENDUM_S7P_03.md`).

## 1. S7j — ΔE (Energy Above Idle, nJ/sample), Median Across 3 Units × 3 Rounds, Capture Order

| Variant | Edge ΔE (nJ) | Edge Latency (µs) | CIC ΔE (nJ) | CIC Latency (µs) |
|---|---|---|---|---|
| `DENSE_ZS` | 1349 | 0.686 | 1256 | 0.651 |
| `DENSE_AQV32_16` | 591 | 0.336 | 577 | 0.296 |
| `DENSE_AQV33_16` | 701 | 0.381 | 618 | 0.343 |
| `SNN_MEMOV3_16` (exact) | 688 | 0.373 | 580 | 0.282 |
| `SNN_RQC_16` | 648 | 0.341 | 535 | 0.261 |
| `SNN_RQT_16` | 585 | 0.315 | 515 | 0.254 |

## 2. SNN/Dense Ratios and Dominance Counts (`k` of 9 Unit–Round Pairs)

- **ΔE (primary, Design §3):** inference power minus pre-condition idle power × time.
- **E_active (sensitivity):** total active power × time (without idle subtraction).

| Dataset | Pair | ΔE Ratio (`k/9`) | E_active Ratio (`k/9`) | SNN Accuracy Feasibility |
|---|---|---|---|---|
| Edge | `RQT / AQ3` | 0.835 (9/9) | 0.820 (9/9) | feasible; AQ3 F1 +0.001 higher |
| Edge | `RQT / AQ2` | 0.992 (5/9) | 0.945 (9/9) | feasible; SNN more accurate |
| Edge | `MEMOV3 / AQ3` | 0.964 (6/9) | 0.969 (7/9) | exact |
| Edge | `MEMOV3 / AQ2` | 1.143 (0/9) | 1.127 (0/9) | exact; Dense uses less energy |
| CIC | `MEMOV3 / AQ3` | 0.881 (6/9) | 0.835 (9/9) | exact; SNN higher AUC, AQ3 higher F1 |
| CIC | `MEMOV3 / AQ2` | 1.005 (4/9) | 0.974 (5/9) | exact; SNN more accurate |
| CIC | `RQT / AQ3` | 0.806 (9/9) | 0.754 (9/9) | **infeasible** |
| Both | Any SNN / `DENSE_ZS` | 0.40–0.52 (9/9) | 0.44–0.55 (9/9) | — |

## 3. Measurement Observation — Low-Idle Artifact (Reported Unfiltered)

- 12 of 108 conditions had measured idle `< 3.6 W` (normal idle ~4.1–4.2 W; 11 occurred on `ciciot2023` between 14:15 and 15:30).
- In those conditions, ΔE rose ~22% above the variant median (`r = −0.84` vs. idle) because background Pi load fluctuated during the idle window.
- Sensitivity check excluding `idle < 3.6 W`: Edge `RQT/AQ3` 8/8; CIC `MEMOV3/AQ3` 5/6 (ratio 0.846); CIC `RQT/AQ3` 8/8.

## 4. S7h `edge_iiotset` (`s0_f0`, 3 Rounds) — Median ΔE (nJ/sample)

| Variant | ΔE (nJ) |
|---|---|
| `DENSE_AQV22_16` | 597 |
| `DENSE_AQV23_16` | 748 |
| `SNN_MEMOV2_16` | 897 |
| `SNN_Q8_MEMO_16` | 1045 |
| `DENSE_ZS` | 1339 |
| `DENSE_Q8_ZS` | 1471 |
| `DENSE_Q8` | 1576 |
| `DENSE` | 1620 |
| `SNN_Q8` | 2369 |
| `SNN_COUNT` | 2873 |

INT8 variants consumed more energy than FP32 for both families because INT8 kernels on Pi remained scalar.

## 5. Descriptive Summary & Limitations

- On Edge-IIoTset, `SNN_RQT_16` uses 16–18% less energy than `Dense-AQ3` in all 9/9 pairs (`ΔE` and `E_active`) with a 0.001 F1 trade-off.
- All cached SNN variants use 2–2.5× less energy above idle than `DENSE_ZS` across all pairs.
- Limitations: `n = 3` Pi units (descriptive); ΔE remains primary and `E_active` sensitivity-only.
