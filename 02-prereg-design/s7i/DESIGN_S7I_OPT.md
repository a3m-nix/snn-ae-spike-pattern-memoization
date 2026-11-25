# S7i — Further Optimization of SNN-AE + Cache (Latency, Raspberry Pi 5)

Date: 30 Oct 2026, 00:15 WIB. Note: FNIRSI FNB-58 was unresponsive after 00:02, so `S7i` measures latency only; energy was scheduled later (`S7p`) after physically power-cycling the meter.

## 1. Diagnosis from S7g Data (Prior to This Design)

- **Hit paths are already at parity:** `SNN_MEMOV2` hit cost matches `DENSE_AQV2`.
- **Edge-IIoTset deficit stems from hit rate:** SNN `0.825` vs `AQ3 0.903` and `AQ2 0.973` (`2^16`).
- **SNN hit rate scales with capacity** (`2^12: 0.693 → 2^14: 0.783 → 2^16: 0.825`), indicating remaining conflict/capacity misses.
- **SNN miss path was scalar and branching** (LIF decoder `if`-branches + scalar spike count), whereas Dense miss paths were branchless matrix multiplications auto-vectorized by `gcc`.

## 2. Treatment (Symmetric Across Both Families)

- **`snn_memo_v3`:** `v2` plus NEON-vectorized miss path (`Wd` row accumulation, branchless LIF decoder, `cnt·Wo` accumulation).
- **`dense_aq_memo_v3`:** `v2` plus NEON-vectorized miss path (`h2` accumulation, ReLU, output accumulation).
- **Cache capacities:** `2^16` (9.7 MB), `2^18` (39 MB), and `2^20` (155 MB) for `dout = 33`.
- **Anchors to `S7g`:** `DENSE`, `DENSE_ZS`, `SNN_COUNT`, `DENSE_AQV2{2,3}_16`, and `SNN_MEMOV2_16`.

## 3. Validity Gate (Check Phase Prior to Timing)

- `SNN_MEMOV3_{16,18,20}` (cold and validation-prefilled) bit-identical to `SNN_COUNT`.
- `DENSE_AQV3{2,3}_{16,18,20}` bit-identical to `DENSE_AQ{2,3}` (`s7f`).
- Any failing variant is excluded from timing.

## 4. Measurements and Analysis

- **Latency:** `S7g` protocol (core 3, 15 passes, randomized variant order per pass, capture primary / random secondary), units `s0_f0`, `s1_f0`, `s2_f0` under `e37-lock`.
- **Primary comparisons per dataset:** `SNN_MEMOV3_c` vs `DENSE_AQV3{2,3}_c` at matching capacity, plus fastest variant per family across capacities.
- **Accuracy:** unchanged by construction (bit-identical to references; 30-unit server medians apply).
- **Scope:** descriptive (`n = 3` Pi units); x86 confirmation requires a separate portable AVX2 port (`S7x_ij`).

## 5. Limitations

- `2^20` cache (155 MB) carries a substantial edge-device memory cost, reported explicitly as a capacity trade-off.
- `S7g` results were observed prior to this design; treatments and capacity sweeps apply symmetrically.
