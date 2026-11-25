# Bit-Identity Verification at Small Cache Capacities (`2^12`, `2^14`), 18 Nov 2026

**Objective.** Address internal review feedback noting that prior Pi bit-identity logs covered `2^16`/`2^18`/`2^20`, whereas cache-capacity curves and highlights include `2^12` and `2^14`.

**Method.** Run `phase_check` from `03-scripts/s7i/s7i_rpi.py` unchanged, substituting `CAPS3 = [12, 14]`.

**Scope and Criteria.**
- Units and data: 6 units (`s0/s1/s2_f0 × 2 datasets`) from `s7f/rpi_package`, capture order, cold and validation-prefilled caches.
- `SNN_MEMOV3_{12,14}` must be bit-identical to `SNN_COUNT`.
- `DENSE_AQV3{2,3}_{12,14}` must be bit-identical to `DENSE_AQ{b}`.

**Execution.** Raspberry Pi 5, core 3, under `e37-lock`; live services untouched. Outputs saved in `01-results/s7k_capcheck/`.
