# S7p — FNIRSI Energy Phase (30 Oct 2026 14:00 WIB: S7i/S7j, S7h, S7g-more)

Written 30 Oct 2026 ~10:30 WIB prior to any energy measurements in this block, following physical USB power-cycling of the FNIRSI FNB-58 meter.

## 1. Protocol

- **Power protocol:** `S7g §3` (`02-prereg-design/s7g/DESIGN_S7G_TRADEOFF.md`), unchanged:
  - Cooldown to reference temperature `+ 2 °C`, followed by 20 s idle measurement per condition.
  - Active measurement window `≥ 30 s`; cache snapshot restore included inside the timed/power window.
  - Validity criterion: reading rate `≥ 0.5 × idle rate`.
  - `FNIRSI_NO_RESET=1`; logger reopened at most 3 times per condition without `dev.reset()`.
- **Preflight (`preflight_fnirsi.sh`):** reads FNB-58 HID once for 12 s (passes if `≥ 10` lines); failure exits (`rc = 4`) without retries. Any mid-block failure halts subsequent blocks.

## 2. Blocks (Fixed Order, Decreasing Priority)

| Block | Script | Variants | Units | Order | Rounds | Conditions | Est. Time |
|---|---|---|---|---|---|---|---|
| 1. `S7i/S7j` | `s7j/s7j_rpi.py --phase power` | `DENSE_ZS`, `SNN_MEMOV3_16`, `SNN_RQC_16`, `SNN_RQT_16`, `DENSE_AQV32_16`, `DENSE_AQV33_16` | `s0_f0`, `s1_f0`, `s2_f0` | `capture` | 3 | 54 / dataset | ~1h 45m |
| 2. `S7h` | `s7d_pi/s7h_rpi.py --phase power` | 10 FP32 + INT8 variants | `s0_f0` | `capture` | 3 | 30 / dataset | ~1h |
| 3. `S7g-more` | `s7g/s7g_more_rpi.py --phase power` | `DENSE_ZS`, `DENSE_AQV22_16`, `DENSE_AQV23_16`, `SNN_MEMOV2_16` | `s{0,1,2}_f{1,2}` | `capture` | 3 | 72 / dataset | ~2h 20m |

- Block 1 uses a symmetric grid on both datasets (`SNN_RQT_16` is still measured on CICIoT2023 despite failing accuracy feasibility, and reported without efficiency claims per `S7j §3`).

## 3. Pre-Specified Analysis

- **Primary metric:** `ΔE` (board energy above idle per sample) per unit–round.
- **Dominance rule (`S7g §4`):** accuracy `≥` comparator (30-unit server median) **and** lower `ΔE` in `≥ 8/9` unit–round pairs.
  - SNN comparators: `SNN_RQT_16` (Edge-IIoTset), `SNN_MEMOV3_16` (both datasets); `SNN_RQC_16` reported as ablation.
- **Latency consistency:** `ΔE` ratios compared descriptively with `S7i`/`S7j` latency ratios.
- **Invalid conditions** (`power_valid=false` after 3 attempts) are reported transparently and never silently dropped.

## 4. Known Background Perturbations (Flagged for Sensitivity, Unfiltered)

- Hourly monitoring timer (`~1–8 s`, `nice 10`) flagged for windows overlapping `HH:00–HH:03`.
- Live edge service remains running as in `S7g`.
