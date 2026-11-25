# S7g — Accuracy vs. Cost Trade-Off Between SNN-AE and Dense-AE on Raspberry Pi 5

Date: 29 Oct 2026, 21:40 WIB. Goal: identify conditions yielding a fair, clear accuracy–cost trade-off between SNN-AE and Dense-AE on Raspberry Pi 5. Sections 1–2 cover the exploratory latency phase; Sections 3–4 define the confirmation energy protocol locked by SHA-256 prior to FNIRSI measurement.

## 1. Exploratory Phase (Executed 21:30–21:37 WIB)

- **Models and data:** `S7f` package (3 units × 2 datasets, revision weights, full test sets, validation-normal), without retraining. Kernel accuracy measured on Pi (`accuracy_<ds>.csv`).
- **Inference time-step sweep (`T = 1, 2, 4, 5, 7`):** accuracy on CICIoT2023 degraded outside `T = 3` (AUC `0.46–0.90`); discarded.
- **New bit-identical kernels (check phase passed 6/6):**
  - `SNN_MEMOV2_{12,14,16}`: `snn_memo` with branchless NEON LIF encoder.
  - `DENSE_AQV2{2,3}_{12,14,16}`: `dense_aq_memo` with NEON `h1` quantization.
  - Both model families received symmetric hit-path vectorization; miss paths remained untouched.
- **Latency Round 1** (SNN-only optimization): archived in `explore_round1/` as a log only and excluded from claims due to asymmetry.
- **Latency Round 2** (both families optimized): used to select confirmation variants.

## 2. Confirmation Variant Selection (Symmetric Rule, Fixed Before Energy Runs)

- **Cache capacity:** `2^16` slots for all cached variants (largest tested capacity, benefiting both families).
- **Variants:** `DENSE_ZS` (cache-free reference), `DENSE_AQV22_16`, `DENSE_AQV23_16`, and `SNN_MEMOV2_16`.
- **Stream order:** `capture` (primary) and `random` (secondary).

## 3. Energy Measurement Protocol (Confirmation)

- Follows `S7f`/`s7a v2`: cooldown to reference temperature `+ 2 °C`, 20 s idle baseline, active window `≥ 30 s`, 3 rounds with randomized condition order, and cache snapshot restore included inside the measurement window (making cached variants conservative).
- Logger uses `FNIRSI_NO_RESET=1` uniformly across both datasets.
- Metrics: board energy above idle per sample (`ΔE`) and total active energy per sample, alongside in-window latency.

## 4. Analysis and Decision Rules

**Accuracy:**
- Primary: 30-unit server medians (SNN-AE and Dense FP32 from rev1; `DENSE_AQ` `ΔAUC`/`ΔF1` from `S7f`, capacity-invariant and verified bit-identical).
- Supporting: 3 Pi units (`accuracy_<ds>.csv`), including recall at fixed FPR `0.1 / 0.5 / 1 / 5%`.

**Dominance:** Variant `A` dominates `B` on dataset `d` and metric `m ∈ {AUC, F1@p99}` if `accuracy(A) ≥ accuracy(B)` (30-unit median) **and** `ΔE(A) < ΔE(B)` in `≥ 8/9` unit–round pairs (capture order).

**Dataset Verdict:**

| Verdict | Condition |
|---|---|
| `TRADE-OFF` | `SNN_MEMOV2_16` is not dominated by any Dense variant on at least one metric, and a Dense variant is either more accurate at higher energy or lower-energy at lower accuracy |
| `SNN DOMINANT` | `SNN_MEMOV2_16` dominates all Dense variants on that metric |
| `SNN DOMINATED` | Some Dense variant dominates `SNN_MEMOV2_16` on both metrics |

Random order, total active energy, and system-level context (`~0.3 µs` kernel vs `103–130 µs` full pipeline) are reported alongside.

## 5. Known Pre-Measurement Limitations

- `n = 3` units for energy (descriptive Pi benchmark).
- NEON optimization in `v2` covers hit paths only; miss paths remain scalar/auto-vectorized.
- `Dense-AQ` uses post-training quantization; quantization-aware training (QAT) was not evaluated.
- Latency Round 2 was observed before locking this confirmation design; `2^16` capacity applies symmetrically to both families.
