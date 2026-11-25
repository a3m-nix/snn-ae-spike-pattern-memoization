# S7j — SNN-AE + Cache with Quantized Spike-Code Keys (Counterpart to Dense-AQ)

Date: 30 Oct 2026, 00:25 WIB. Designed to evaluate whether grouping encoder spike patterns reduces cache misses symmetrically to `Dense-AQ` activation rounding.

## 1. Basis (Exploratory NumPy Analysis via `explore_keys.py`, 3 Units; Non-Confirmatory)

- Each encoder neuron emits one of 5 spike patterns across `T = 3`: none, `t1`, `t2`, `t1+t2`, or all three.
- **Exact key** uses three 32-bit masks (96 bits): `8,975` unique test patterns (Edge), `17,097` (CIC).
- **Spike-count key (`COUNT`):** merges `t1` and `t2` (preserving count 0/1/2/3); accuracy virtually unchanged, ideal hit rate rises (`0.867 → 0.917` Edge; `0.894 → 0.936` CIC).
- **Tri-level key (`TRI`, 0 / 1 / ≥2):** ideal hit rate `0.959` on Edge with preserved accuracy, but AUC drops to `0.875` on CIC.
- **Binary key:** accuracy drops on both datasets; discarded.

## 2. Treatment

- **Kernel `snn_rq_memo`:**
  - Identical encoder and NEON miss path to `snn_memo_v3`.
  - Per-neuron class (`COUNT` or `TRI`) computed bit-sliced from the three masks.
  - On cache miss, the decoder executes on the canonical spike pattern per neuron class (most frequent pattern in per-unit validation-normal data).
- **Variants:** `SNN_RQC_{16,18,20}` (`COUNT`) and `SNN_RQT_{16,18,20}` (`TRI`).
- **Grid comparators:** `DENSE_ZS`, `SNN_MEMOV3_{16,18,20}`, and `DENSE_AQV3{2,3}_{16,18,20}`.
- **Model equivalence:** `RQ` alters the SNN-AE function analogously to how `AQ` alters Dense-AE ("quantized model + cache").

## 3. Phases and Criteria

- **Check phase:** `RQ` scores must be deterministic and invariant to cache capacity and initial state (cold vs. validation-prefilled); failures abort measurement.
- **Accuracy (3 Pi units):** `SNN_COUNT`, `SNN_RQC`, `SNN_RQT`, `DENSE`, `DENSE_AQ2`, `DENSE_AQ3` evaluated on AUC, F1@p99(val), and recall at fixed FPR.
  - **Feasibility threshold (`S7d`):** median per-unit `ΔAUC ≥ −0.005` and `ΔF1 ≥ −0.01` vs. `SNN_COUNT`. Infeasible variants are reported transparently without efficiency claims.
- **Latency:** `S7g` protocol (core 3, 15 passes, randomized variant order, capture primary / random secondary), units `s0_f0`, `s1_f0`, `s2_f0`.

## 4. Limitations

- Descriptive on Pi (`n = 3` units); 30-unit server confirmation is deferred to `S7x_ij`.
- Canonical patterns are derived strictly from validation-normal data.
- `S7i` latency outcomes had not been observed when `S7j` was locked.
