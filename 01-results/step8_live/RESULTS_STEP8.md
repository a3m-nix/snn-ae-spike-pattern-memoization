# E3-7 Native — Step 8 Results: Live Shadow Evaluation of Optimized Models (L8, 31 Oct 2026)

**References:**
- Pre-registration: `02-prereg-design/step8/PREREG_STEP8_v1.md`, locked in `LOCK_STEP8.sha256` (`ab2eddaa…`) prior to the live session. `ADDENDUM_STEP8_01.md` documents two analysis-script gate flags.
- Live session: `L8-20261031-141236`, 14:12–15:32 WIB, `rev8` service.
- Single-pass analysis output: `analysis/step8_analysis.json`.

## Execution Summary

- **Phase B (Benign):** 60 minutes of benign office traffic plus Raspberry Pi and Kali traffic generators.
- **Phase M (Injection):** 15 scheduled flood injections (`rc = 0`), waiting 0–10 s for event closure after each injection.
- **Session conditions:** clock offset 0.095 s at start and 0.110 s at end; capture filter F2 verified across all sources; **286,787 packets** scored by the shadow process; no manual operator traffic.

## Gates and Validity Checks

| Gate / Check | Result |
|---|---|
| G1 Service health | Pass (`FINAL_SUMMARY` pass, 0 errors, child `rc = 0`; only protocol-scheduled restarts — see `ADDENDUM_STEP8_01.md`) |
| G2 Production lag | L1 K1 p99 = 0.915 s (limit 1.003 s), K2 p99 = 0.971 s (limit 1.073 s); L2 p99 = 0.937 s, max = 1.167 s |
| G3 Shadow drops | 0 batches dropped |
| G4 Scaler parity | 286,787 / 286,787 packets exact match |
| Validity checks | V1, V2, V4, V5 passed; V3 satisfied (`ADDENDUM_STEP8_01.md`) |

## Endpoints

**P1 — Output Identity: PASS.** Exact-memoized SNN-AE scores were **100% bit-identical** to the cache-free SNN-AE across all 286,787 live packets. Detected events and closure timestamps were identical (14 events).

**P2 — Per-Packet Inference Time, SNN-AE + Exact Reuse vs. Dense-AE FP32: PASS.** Median per-batch ratio (`n ≥ 32`) was **0.772**, 95% CI [0.649, 0.894].

| Slice | Ratio (`SNN_AE_REUSE / Dense_AE_B`) |
|---|---|
| Benign phase (batches `n ≥ 32`) | 0.914 |
| **Injection phase (batches `n ≥ 32`)** | **0.527** |
| Aggregate across all packets (including small batches) | 0.976 |
| Small batches (`n < 32`) | 1.14 |

- **Batch coverage:** batches with `n ≥ 32` accounted for 1,174 of 6,979 batches, containing 228,275 packets (80%).
- **Small batches:** on small batches, per-call overhead dominates, masking the decoder-reuse speedup.

**P3 — Secondary Pairwise Comparisons (descriptive, median per batch `n ≥ 32`, 95% CI):**

| Pair | Ratio | 95% CI | Injection Phase (Phase M) |
|---|---|---|---|
| Exact Reuse / Dense-AE 8-level | 1.002 | 0.991–1.028 | 0.973 |
| Exact Reuse / Dense-AE 4-level | 1.016 | 0.999–1.035 | 0.974 |
| Tri-level Grouping / Dense-AE 8-level | 1.040 | 1.023–1.067 | 1.014 |
| Tri-level Grouping / Dense-AE 4-level | 1.049 | 1.024–1.076 | 1.008 |
| Tri-level Grouping / Dense-AE FP32 | 0.795 | 0.670–0.914 | 0.542 |
| SNN-AE / Dense-AE runtime (unoptimized) | 1.714 | 1.683–1.745 | 1.724 |

- Against quantized Dense-AE, exact SNN reuse achieves parity in throughput (and is slightly faster during the injection phase), consistent with `S7x_ij` on Edge-IIoTset.
- Tri-level grouping was slightly slower (~4–5%) than quantized Dense-AE on live traffic, with the difference nearly vanishing during the injection phase.

**P4 — Cache Hit Rate (per-minute block bootstrap 95% CI):**

| Variant | Phase B (Benign) | Phase M (Injection) |
|---|---|---|
| SNN-AE + exact reuse | 0.904 [0.859, 0.930] | 0.961 [0.953, 0.966] |
| SNN-AE tri-level grouping | 0.960 | 0.961 |
| Dense-AE 8-level | 0.996 | 0.998 |
| Dense-AE 4-level | 0.997 | 0.999 |

**P5 — Phase M Detections (event start within `[t0, t0 + 10 s]`):**

| Model | ICMP | SYN | UDP | Total | Median TTD (s) |
|---|---|---|---|---|---|
| Production SNN-Keras | 5/5 | 5/5 | 4/5 | 14/15 | – |
| SNN-AE (runtime, benchmark build, + exact reuse, + tri-level) | 5/5 | 5/5 | 4/5 | **14/15** | 0.69 / 0.68 / 0.86 |
| Dense-AE (runtime, FP32, 8-level) | 5/5 | 0/5 | 4/5 | 9/15 | 0.70 / – / 0.87 |
| **Dense-AE 4-level** | 0/5 | 0/5 | 0/5 | **0/15** | – |

- **Phase B:** 0 events across all models; 0 events outside injection windows.
- **SYN floods:** only the SNN family detected SYN floods. Because O4 thresholds were developed on SNN-AE, this finding is **not** framed as general detection superiority (`PREREG_STEP8_v1.md` §7).
- **Dense-AE 4-level:** lost all 15 detections under its O4 threshold (`222.9`, which already triggered 11 alarm episodes during benign calibration) due to activation rounding error.

**P6 — Per-Packet Pipeline Cost Breakdown (live):**

| Pipeline Stage | Time per Packet |
|---|---|
| Production feature extraction | 23 µs (median) |
| Native scaler transform | 7.2 µs |
| SNN-AE + exact reuse scoring | 1.2 µs (median, batches `n ≥ 32`); 2.3 µs (aggregate) |

## Interpretation (Pre-Registered §7)

1. **Exact reuse leaves live outputs unchanged:** all SNN-AE detections (14/15 floods, 0 benign false alarms, identical TTD) are preserved bit-for-bit.
2. **SNN-AE + exact reuse is faster than Dense-AE FP32 on live traffic:** 0.772× median per batch (`n ≥ 32`), and 0.527× during the injection phase, with smaller gains under sparse benign batches.
3. **Speed parity with quantized Dense-AE without accuracy loss:** 8-level Dense-AE retained 9/15 detections while 4-level Dense-AE dropped to 0/15; exact SNN memoization achieved comparable speed without altering outputs.
4. **Model scoring is no longer the pipeline bottleneck:** feature extraction (~23 µs) and scaling (~7 µs) dominate model scoring (~1–2 µs).

## Limitations

- Single deployment site, single model unit (`s0_f0` Edge-IIoTset), and one ~79-minute live session.
- Live timing is affected by concurrent production background load (mitigated via per-batch randomized scoring order).
- Per-variant energy was not measured during the live run.
- Offline dataset accuracy claims for grouped and rounded variants remain anchored to the 30-unit benchmark (`S7x_ij` / `S7k`).
