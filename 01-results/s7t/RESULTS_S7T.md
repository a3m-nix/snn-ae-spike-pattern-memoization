# S7t — Results: Exact Memoization Across Time Steps T = 2, 3, 5, 7 (18 Nov 2026)

**References and Execution:**
- Design: `02-prereg-design/s7t/DESIGN_S7T.md` (v1.0 + §11 addendum), locked in `LOCK_S7T.sha256` (18 Nov 2026, 18:03:56 WIB) prior to the main run.
- Executed on x86_64 server (`Xeon Silver 4416+`), core 10, `nice 10`, 18:04–18:22 WIB. Single-pass analysis by `s7t_analyze.py`.
- Full outputs: `results/RESULTS_S7T_auto.md`, `results/s7t_tests.csv`, and `results/s7t_summary.csv`.
- Integrity check: `SHA256SUMS_s7t.txt` (251 files, OK).

**Models:** Derived from the `v8-3` fair-benchmark training pipeline (`SNN_AE T2, T3, T5, T7` and `Dense_AE`, 30 units = `3 seeds × 10 folds` per dataset). Because splits and scalers differ from the main revision pipeline, `S7t` numbers are kept separate from the main tables in the paper.

## Validation Gates

| Gate | Outcome |
|---|---|
| G0: `v8.3.1` data reconstructed (sample counts, feature columns, holdout `y_hash`) | Passed on both datasets (400,000 and 1,500,000 samples) |
| G1: Native AUC vs `main_results_raw`, per unit and model (`Dense_AE` + 4 `SNN_AE`) | Max `\|ΔAUC\|` = 8.5×10⁻⁶ (limit 10⁻³) |
| G1 extra: Mean F1@p99 per T vs reference table | Identical: Edge 0.9801 / 0.9937 / 0.9943 / 0.9943; CIC 0.8296 / 0.8358 / 0.8373 / 0.8325 |
| G2: Exact memo bit-identical to cache-free SNN-AE (cold/prefill × capture/random) | 960 / 960 passed |

## Q2 — Memoized Latency vs. Zero-Skipping Dense-AE

Capture order, median across 30 units, two-sided Wilcoxon signed-rank test, Holm-Bonferroni correction across 8 tests.

| Dataset | T | Median Ratio `[p10; p90]` | Units Faster | Speedup vs. Cache-Free SNN-AE | Hit Rate | `p_Holm` |
|---|---|---|---|---|---|---|
| Edge-IIoTset | 2 | 0.291 `[0.273; 0.323]` | 30/30 | 4.1× | 0.983 | 1.5×10⁻⁸ |
| Edge-IIoTset | 3 | 0.370 `[0.342; 0.401]` | 30/30 | 4.4× | 0.854 | 1.5×10⁻⁸ |
| Edge-IIoTset | 5 | 0.490 `[0.466; 0.544]` | 30/30 | 5.0× | 0.654 | 1.5×10⁻⁸ |
| Edge-IIoTset | 7 | 0.528 `[0.495; 0.586]` | 30/30 | 5.4× | 0.626 | 1.5×10⁻⁸ |
| CICIoT2023 | 2 | 0.364 `[0.346; 0.408]` | 30/30 | 4.1× | 0.947 | 1.5×10⁻⁸ |
| CICIoT2023 | 3 | 0.446 `[0.408; 0.472]` | 30/30 | 4.8× | 0.840 | 1.5×10⁻⁸ |
| CICIoT2023 | 5 | 0.620 `[0.575; 0.679]` | 30/30 | 5.5× | 0.624 | 1.5×10⁻⁸ |
| CICIoT2023 | 7 | 0.731 `[0.687; 0.796]` | 30/30 | 6.5× | 0.517 | 1.5×10⁻⁸ |

- **Pre-registered verdict:** *"memo remains faster"* at every `T` on both datasets (`p_Holm < 0.05` and median ratio `< 1` in 8/8 tests).
- **Uniform `p_Holm = 1.5×10⁻⁸`:** exact Wilcoxon minimum for `n = 30` when all 30 units share the same sign.
- **Gain narrows with T:** hit rate drops and latency ratio rises as keys grow longer (`T × 32` bits), yet at `T = 7` memoization still takes 0.53× (Edge) and 0.73× (CIC) of Dense-AE zero-skip time.
- **Speedup vs. cache-free SNN-AE increases with T** (4.1× → 5.4–6.5×), because skipped decoder work per cache hit scales linearly with `T`.

## Q1 — Spike Patterns (Per-Unit Median, Capture Order)

| Dataset | T | Unique Test Patterns (of `n`) | Test Seen in Validation | Top-1,000 Coverage | Spikes/Sample (of max) | AUC | F1@p99 |
|---|---|---|---|---|---|---|---|
| Edge-IIoTset | 2 | 839 (34,000) | 0.517 | 1.000 | 39.4 (64) | 0.9984 | 0.9860 |
| Edge-IIoTset | 3 | 7,709 | 0.427 | 0.698 | 40.1 (96) | 0.9989 | 0.9944 |
| Edge-IIoTset | 5 | 14,127 | 0.289 | 0.535 | 49.3 (160) | 0.9990 | 0.9945 |
| Edge-IIoTset | 7 | 15,276 | 0.266 | 0.507 | 54.7 (224) | 0.9990 | 0.9944 |
| CICIoT2023 | 2 | 10,163 (127,500) | 0.553 | 0.704 | 32.8 (64) | 0.9297 | 0.8318 |
| CICIoT2023 | 3 | 26,165 | 0.500 | 0.504 | 43.9 (96) | 0.9297 | 0.8356 |
| CICIoT2023 | 5 | 52,606 | 0.394 | 0.347 | 70.8 (160) | 0.9277 | 0.8395 |
| CICIoT2023 | 7 | 67,110 | 0.339 | 0.297 | 95.6 (224) | 0.9256 | 0.8339 |

- Unique patterns increase and top-1,000 coverage decreases with `T`, consistent with longer `T × 32`-bit keys.
- On Edge-IIoTset, spike density per time step drops (`39.4/64 → 54.7/224`), moderating the growth of unique patterns.

## Cross-Pipeline Anchor (Descriptive)

- **T=3 (`v8-3`):** hit rate 0.854 (Edge) and 0.840 (CIC), ratio 0.370 / 0.446.
- **T=3 (main revision pipeline, `S7x_ij` x86):** hit rate 0.827 / 0.875, exact memo / zero-skip ratio 0.403 / 0.396.
- **Takeaway:** magnitudes are comparable, though pipelines and stream ordering differ and are kept separate.

## Limitations

- Models come from the `v8-3` training pipeline; only exact memoization was evaluated.
- Evaluated on x86_64 CPU only (no energy measurement).
- Capture order follows balanced-sampled data, making streams less contiguous than in the main revision pipeline.
- **Cache slot layout:** `S7t` used fixed slots (9 key words + 33 floats) across all `T`, corresponding to 11.0 MB at `2^16`.
