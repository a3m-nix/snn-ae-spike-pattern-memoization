# E3-7 Step 8 — Live Shadow Evaluation of Optimized Models (Draft v0, Pre-Lock)

Prepared 31 Oct 2026 prior to `PREREG_STEP8_v1.md` and live deployment.

## 1. Objectives

Evaluate optimized variants (`SNN-AE` exact memoization, `SNN-AE` tri-level grouping, and `Dense-AE` with activation rounding) as shadow models inside the live Raspberry Pi 5 detection pipeline:
1. **Output identity:** Does exact memoization produce bit-identical scores and events to cache-free `SNN-AE` on live traffic?
2. **Latency:** What is per-packet inference time for each variant on identical live batches?
3. **Hit rate:** What cache hit rates occur on real benign and attack traffic?
4. **Production impact:** Does production lag continue to satisfy the `rev7` criteria?

## 2. Unchanged Production Pipeline

- **Production detector:** `SNN-Keras rev7` (decisions and cloud alerts unchanged).
- **Pipeline:** capture filter `F2`, site-17 scaler, event policy, and isolated `nice +10` shadow child process remain identical to `rev7`.

## 3. Proposed Shadow Variants

| Variant | Kernel | Threshold | Role |
|---|---|---|---|
| Cache-free `SNN-AE` | `snn_ae` (`rev7` lib, `f6725e2e…`) | Locked O4 | Reference |
| **`SNN-AE` + exact reuse** | `snn_memo_v3` (`S7i`, `2^16`) | O4 `SNN-AE` | **Primary** |
| `SNN-AE` + tri-level grouping | `snn_rq_memo` `TRI` (`S7j`, `2^16`) | New O4 (§5) | Secondary |
| `Dense-AE` FP32 zero-skip | `dense_ae` (`rev7` lib) | Locked O4 | Dense reference |
| `Dense-AE` 8-level + reuse | `dense_aq_memo_v3` (`S7i`, `2^16`) | New O4 (§5) | Main quantized comparator |
| `Dense-AE` 4-level + reuse | `dense_aq_memo_v3` (`S7i`, `2^16`) | New O4 (§5) | Comparator |

- **Libraries:** frozen `s7i_kernels.so` (`b948a30a…`) and `s7j_kernels.so` (`ff10c62b…`), verified by SHA-256 on startup.
- **Cache prefill:** all caches prefilled with identical site-normal calibration data prior to timing.
- `CNN-AE` and `LSTM-AE` excluded from Step 8 shadow to focus shadow budget on SNN vs. Dense comparators.

## 4. Timing Instrumentation

- Each batch array `Zn` is scored by all variants in randomized per-batch order (fixed seed) using `perf_counter_ns` around scoring calls; per-batch `n`, variant times, and hit/miss counts are logged to `shadow_timing.npz`.

## 5. Offline Preparation (Step 8.0) and Live Schedule (Step 8.1)

- Canonical patterns (`RQT`), rounding steps (`AQ`), and O4 thresholds (`p90`) are computed strictly from site calibration data (`O4_NATIVE_RULES_v1`).
- Offline replay gates `T1` (100% bit-identity on `A7` capture) and `T2` (paced replay lag/drop check) must pass before locking `LOCK_STEP8.sha256`.
- Live session: **Phase B** (60 min benign) + **Phase M** (15 injections: `ICMP`/`UDP`/`SYN × 5`, 1,000 pps × 5 s, ≥ 60 s intervals), ~90 min total, no manual operator traffic.

## 6. Proposed Gates, Endpoints, and Pre-Run Limitations

- **Gates:** healthy service (`0` unplanned restarts), `L1`/`L2` lag pass, `0` shadow drops, `100%` scaler parity.
- **Endpoints:** `P1` (100% bit-identical scores & events), `P2` (median per-batch `n ≥ 32` latency ratio vs `Dense-AE FP32`), `P3` (secondary ratios), `P4` (live hit rates), `P5` (Phase M detections), `P6` (inference share vs feature extraction).
- **Limitations:** per-variant energy not measured live (mW differences masked by 3.0–4.4 W board idle variance); single site and single model unit (`s0_f0` Edge-IIoTset); site calibration used for `RQT`/`AQ`.
