# S7p Results — FNIRSI Power & Energy on Raspberry Pi 5 (30 Oct 2026, 13:32–23:44 WIB)

Related documents:
- **Design:** `02-prereg-design/s7p/DESIGN_S7P_POWER.md`; `ADDENDUM_S7P_01.md`–`03.md` (continuations after FNB-58 stalls; persistent single-process logger for `S7h ciciot2023` and `S7g-more`).
- **Analysis script:** `03-scripts/s7p/analyze_s7p.py`.
- **Full outputs:** `RESULTS_S7P_auto.md` and `s7p_power_long.csv`.

Summary: **384 conditions, all valid** (312 `S7p` conditions + 72 `S7g` capture conditions from 29 Oct).

## 1. Summary

| Pair (`S7g §4`: accuracy ≥ and lower ΔE in ≥ 8/9) | ΔE Ratio (`k`) | `E_active` Ratio (`k`) | 30-Unit Accuracy (SNN vs Dense) | Interpretation |
|---|---|---|---|---|
| **Edge** `SNN_RQT_16` vs `Dense-AQ3` | 0.835 (9/9) | 0.820 (9/9) | AUC 0.9994 vs 0.9996; F1 0.9944 vs 0.9954 | **Trade-off:** SNN −16% energy, Dense +0.001 F1 |
| **Edge** `SNN_RQT_16` vs `Dense-AQ2` | 0.992 (5/9) | 0.945 (9/9) | AUC 0.9994 vs 0.9982; F1 0.9944 vs 0.9798 | ΔE parity, SNN more accurate; SNN dominates on `E_active` |
| **CIC** `SNN_MEMOV3_16` (exact) vs `Dense-AQ3` | 0.881 (6/9) | 0.835 (9/9) | AUC 0.914 vs 0.864; F1 0.808 vs 0.830 | AUC vs F1 trade-off; SNN trends lower energy, misses ≥ 8/9 on ΔE |
| **CIC** `SNN_MEMOV3_16` vs `Dense-AQ2` | 1.005 (4/9) | 0.974 (5/9) | AUC 0.914 vs 0.841; F1 0.808 vs 0.773 | Energy parity; SNN more accurate on both metrics |
| **Edge** `SNN_MEMOV3_16` vs `Dense-AQ2` | 1.143 (0/9) | 1.127 (0/9) | F1 0.9948 vs 0.9798 | Inverse trade-off: Dense-AQ2 uses less energy, SNN more accurate |
| All SNN + cache vs `Dense FP32 (ZS)` | 0.40–0.57 (all) | 0.39–0.62 | dataset-dependent | SNN 1.8–2.5× less energy (S7j v3 block: 0.40–0.52, i.e., 1.9–2.5×) |

**Edge-IIoTset**
- Under tri-level grouping (`SNN_RQT_16`), the expected trade-off appears clearly: 16% lower energy than `Dense-AQ3` across all 9/9 pairs on both ΔE and `E_active`, with 0.001 lower F1; energy parity or better vs. `Dense-AQ2` with higher accuracy.

**CICIoT2023**
- Exact `SNN_MEMOV3_16` leads in AUC while `Dense-AQ3` leads in F1@p99.
- SNN energy advantage is consistent on `E_active` (9/9) but reaches 6/9 on primary ΔE due to low-idle variance.
- `RQT`/`RQC` on CICIoT2023 are even faster/lower-energy but fail accuracy feasibility (`S7x_ij`), so they are reported without efficiency claims.

## 2. S7g 9 Units (Legacy v2 Kernel, `SNN_MEMOV2_16`; 27 Unit–Round Pairs, Capture Order)

| Dataset | vs `ZS` | vs `AQ2` | vs `AQ3` |
|---|---|---|---|
| Edge | 0.568 (27/27) | 1.288 (3/27) | 1.149 (4/27); `Dense-AQ3` dominates on `E_active` |
| CIC | 0.480 (27/27) | 1.104 (7/27) | 0.974 (17/27) |

- **v2 kernels:** confirmed `S7g` 3-unit findings (`Dense-AQ` uses less energy than `SNN v2` on Edge).
- **v3 + RQ kernels (`S7j`):** reversed the gap against `AQ3` and reached parity with `AQ2`, demonstrating that `S7i`/`S7j` optimizations drive the trade-off.

## 3. S7h (`s0_f0`): FP32 vs INT8, Median ΔE (nJ/sample)

| Variant | Edge (nJ) | CIC (nJ) |
|---|---|---|
| `DENSE_AQV22_16` | 597 | 548 |
| `SNN_MEMOV2_16` | 897 | 593 |
| `DENSE_AQV23_16` | 748 | 665 |
| `SNN_Q8_MEMO_16` | 1045 | 846 |
| `DENSE_ZS` | 1339 | 1271 |
| `DENSE_Q8_ZS` | 1471 | 1345 |
| `DENSE` / `DENSE_Q8` | 1620 / 1576 | 1711 / 1659 |
| `SNN_COUNT` / `SNN_Q8` | 2873 / 2369 | 2345 / 2211 |

- Cached/ZS INT8 consumed more energy than FP32 in both families because Pi INT8 kernels remained scalar.
- Cache-free `SNN_COUNT` was the highest-energy variant (1.8–2.2× `DENSE_ZS`).

## 4. Measurement Quality

- **Validity:** 384/384 valid conditions; FNIRSI sampling rate ~100 Hz on both direct pipe and persistent single-stream reader.
- **Idle power fluctuation:** `idle_W` spanned 2.98–4.58 W across all blocks (3.18–4.50 W in S7j). Conditions with `idle < 3.6 W` showed ~20–30% higher ΔE (`r = −0.75` vs. idle) due to background Pi services/network fluctuations. Data were not filtered; `E_active` is reported alongside primary ΔE as a sensitivity check.
- **Reader differences across blocks:** `S7h ciciot2023` and `S7g-more` used the persistent stream reader (`ADDENDUM_S7P_03.md`), whereas other blocks used direct pipes. All dominance comparisons are computed strictly within the same block.
- **FNB-58 stalls** (00:02, 15:53, 16:32, 20:48) occurred only upon reopening the USB logger, never mid-measurement. The persistent single-logger stream completed 174 conditions uninterrupted.

## 5. Limitations

- **Sample sizes:** `S7j` `n = 3` units × 3 rounds; `S7g` `n = 9` units × 3 rounds; `S7h` `s0_f0` only (all descriptive).
- **Measurement boundary:** board-level USB-C power includes background OS/network load.
- **Accuracy reference:** 30-unit server medians (`acc30_long.csv` and `S7x_ij`).
- **Run history:** continued across three resumes documented in `ADDENDUM_S7P_01.md`–`03.md` without altering per-condition protocols.
