# E3-7 Native — Native O4 Threshold and Event Policy Rules (v1, LOCKED)

Locked 26 Oct 2026 alongside `e37_native_o4.py` prior to full calibration evaluation.

## 0. Provenance of O4 (Required Manuscript Disclosure)

O4 was **not** produced by the automated `v2` selection script (which chose `p94.5 = 3.585` and missed SYN floods whose `hping3` scores clustered near `~2.6`). Instead, O4 (`p90` combined calibration + persistence) was selected using development attack captures (`A1` + August pcaps) **on SNN-AE**. Consequently:
- O4 was tuned on SNN-AE; baseline models receive the identical rule **without per-model tuning**. This development bias favors SNN-AE and must be disclosed explicitly as a limitation.

## 1. Primary Rule (Locked)

For each model `m ∈ {SNN_AE, Dense_AE, CNN_AE, LSTM_AE}`:
```text
thr_m        = np.percentile(S_m, 90)     # float32 calibration scores (combined array)
anomalous    : s > thr_m                  # strict inequality
condition(t) : a(t) >= 256 and a(t) >= 0.6 * n(t)   # sliding 1 s window [t-1.0, t]
trigger(t)   : condition(t) and prior condition in [t-1.0, t-0.5]  # persistence
episode      : consecutive triggers within <= 3.0 s merged into one event
```
- **No per-model re-selection:** if `p90` produces calibration episodes on a baseline model, those episodes are reported transparently without altering the threshold.

## 2. Calibration Dataset (`27.2 hours`, `2,468,434` Packets)

Combined from 5 benign segments (`cal17_holdout`, `d21_pre0300`, `B1`, `B2`, and `A1_background` with attack/operator windows stripped). Holdout captures (`B3`–`B5`, `A2`, `A3`) are guarded against access during calibration.

## 3. Scoring Implementation & Validation Gates

- Input pipeline: `nan_to_num(float64) → float32 → native scaler → native model` (all from unit `edge_iiotset/s0_f0`, cache-free SNN, `dense_zero_skip=True`), verified by SHA-256 on startup.
- **Gate G0:** calibration packet count must equal `2,468,434` and Keras SNN `p90` must equal `2.3325785398483285`.
- **Gate G1:** report `|thr_SNN,native − 2.3325785398483285|` (logged without pass/fail cutoff).
- **Sensitivity grid (`K3`):** `p85, p87.5, p90, p92.5, p95, p97.5, p99, p99.5` locked in `thresholds_o4_native.json` for descriptive sensitivity analysis only.
