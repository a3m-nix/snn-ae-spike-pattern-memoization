# E3-7 Native — Step 8 Pre-Registration: Live Shadow Evaluation (v1, LOCKED)

Locked 31 Oct 2026 ~14:15 WIB alongside scripts and artifacts in `LOCK_STEP8.sha256` after `T1`/`T2` passed and **prior** to live session `L8`. Post-lock deviations are recorded only via addenda.

Approved configuration (`D1a`, `D2a`, `D3a` from `DESIGN_STEP8_LIVE_OPT.md`): 6 optimized/comparator shadow variants (without CNN/LSTM), site calibration data, 60 min benign + 15 flood injections.

## 1. Research Questions

When optimized `SNN-AE` and `Dense-AE` variants run as shadow detectors in the live pipeline (`tshark` stream, native `site17` scaler, `v2.1` event policy):
1. Does exact `SNN-AE` memoization match cache-free `SNN-AE` scores and events on live traffic (`P1`)?
2. Is exact `SNN-AE` memoization faster per packet than `Dense-AE FP32` on identical live batches (`P2`)?
3. How do grouped/rounded variants (`P3`), live hit rates (`P4`), detections (`P5`), and scoring share vs. feature extraction (`P6`) behave?

## 2. Pre-Lock Design Update (Discovered in Step 8.0)

Smoke testing on 31 Oct revealed that `S7i` benchmark libraries (`-ffp-contract=fast`, fused FMA) were not bit-identical to the `rev7` live runtime (`-ffp-contract=off`: `32.6%` exact on SNN calibration, max diff `0.53`). Therefore:
- **Two benchmark-build references were added:** `SNN_AE_B` (`s7c snn_ae`) and `Dense_AE_B` (`s7c dense_ae ZS`), ensuring all latency and bit-identity comparisons occur within the same compiler build (`-ffp-contract=fast`).
- `P1` compares `SNN_AE_REUSE` against `SNN_AE_B`.
- `SNN_AE` and `Dense_AE` runtime models remain present for continuity with Step 7.

## 3. Configuration (Fixed at Lock)

| Item | Value |
|---|---|
| Service | `rev8`: `snn-edge-live-run-rev8` (`rev8.conf` drop-in); master `live_interface_master_v24.py` |
| Config | `live_interface_config_v10f2_site17v24shadowopt.json` |
| Filter | `F2` (verified identically on service and background capture) |
| Production | `SNN-Keras v2.1`, threshold `2.3325785398483285`, publish ON |
| Shadow | 8 models in `nice +10` child process, publish OFF |
| Libraries | Frozen `S7p` shared objects (`SHA256_LIBS.txt`: `s7c_native_copy`, `s7i_kernels`, `s7j_kernels`) |
| Calibration | `opt_aux.npz`, `prefill_calib.npz`, `thresholds_step8.json` |

**Shadow Models and O4 Thresholds (`p90` Calibration):**

| Model | Kernel | Threshold | Calibration Episodes (Persist) |
|---|---|---|---|
| `SNN_AE` | runtime `snn_ae` | `2.332580` | 0 |
| `Dense_AE` | runtime `dense_ae` ZS | `22.955556` | 0 |
| `SNN_AE_B` | `s7c snn_ae` | `2.332573` | 0 |
| `SNN_AE_REUSE` | `s7i snn_memo_v3` (`2^16`) | `2.332573` (bit-identical to `SNN_AE_B`) | 0 |
| `SNN_AE_RQT` | `s7j snn_rq_memo` `TRI` (`2^16`) | `2.435060` | 0 |
| `Dense_AE_B` | `s7c dense_ae` ZS | `22.955576` | 0 |
| `Dense_AE_AQ3` | `s7i dense_aq_memo_v3` 3-bit (`2^16`) | `27.930431` | 0 |
| `Dense_AE_AQ2` | `s7i dense_aq_memo_v3` 2-bit (`2^16`) | `222.872086` | **11** (reported per O4 §1) |

- **Cache prefill:** every 12th packet from combined calibration (`205,703` packets).
- **Per-batch scoring order:** randomized (`seed 8`); timing via `perf_counter_ns` around scoring calls only.

## 4. Pre-Live Verification Tests (Passed Prior to Lock)

- **Calibration `G0′/C1/C2`:** exact calibration set parity (`2.47M` packets); `SNN_AE_REUSE = SNN_AE_B`; cache capacity/prefill invariance verified.
- **`T0`:** diff `v23 → v24` isolated to shadow adapter files.
- **`T1`:** offline replay of `A7` (`1.59M` packets) passed 4/4 (100% bit-identical scores & events for `REUSE`).
- **`T2`:** paced replay `rev7` vs `rev8` passed (`0` drops; p99 `0.156–0.159 s` vs `0.152–0.162 s`; `×2.0` load `0.893 s`).

## 5. Session L8, Endpoints, and Pre-Registered Interpretation

- **Session:** preflight → **Phase B** (60 min benign) → **Phase M** (15 `hping3` floods, 1,000 pps × 5 s, randomized `seed 8`, ≥ 60 s quiet gap) → end flush; single-pass `e37_step8_analyze.py`.
- **Gates (`G1–G4`):** service health, `L1`/`L2` lag, `0` shadow drops, `100%` scaler parity.
- **Primary endpoints:** `P1` (bit-identical fraction `= 1.0` & identical events); `P2` (median per-batch `n ≥ 32` ratio `SNN_AE_REUSE / Dense_AE_B` with 95% per-minute block bootstrap CI upper bound `< 1`).
- **Secondary/descriptive endpoints:** `P3` (pairwise ratios), `P4` (hit rates), `P5` (Phase M detections within `[t0, t0 + 10 s]`), `P6` (scoring vs feature extraction cost); aggregate ratio and `n < 32` small batches reported separately.
- **Limitations:** single site and unit (`s0_f0`), production background load, site calibration for `RQT`/`AQ`, and O4 threshold rule developed on SNN (`O4_NATIVE_RULES_v1.md §0`).
