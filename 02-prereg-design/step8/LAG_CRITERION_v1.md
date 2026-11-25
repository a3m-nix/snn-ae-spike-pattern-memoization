# Production Lag Criterion for Live Evaluation (v1, LOCKED Prior to Live Data)

Date: 28 Oct 2026, ~19:00 WIB. Empirical basis: `tshark` capture floor (`~0.6 s`) plus queueing buildup only on sustained bursts `> 4.5k pps` for `≥ 2 s`; shadow child process adds `≤ 0.02 s`.

## Definitions

- **Per-packet lag:** `wall_observed_at − capture_ts` from `packet_runtime_records.csv`.
- **Per-second load:** count of production packets sharing `floor(capture_ts)`.
- **Packet load class:** max per-second load over the packet's second and the preceding 2 seconds:
  `K1 < 1,000`; `K2 1,000–2,999`; `K3 3,000–3,999`; `K4 4,000–4,499`; `K5 ≥ 4,500 pps`.
- **Fixed `rev5` reference (`LIVE_B5`, `p99` per class):** `K1: 0.903 s` (`n=507,789`), `K2: 0.973 s` (`n=330,306`), `K3: 0.893 s` (`n=53,772`), `K4: 1.431 s` (`n=33,595`).

## Criteria

| ID | Type | Rule |
|---|---|---|
| `L1` | Gating | For each class `K1–K4` with `≥ 10,000` packets: `p99 ≤ reference p99 + 0.10 s` (classes `< 10,000` reported descriptively) |
| `L2` | Gating | Combined `K1–K4` packet lag `p99 ≤ 2.0 s` |
| `L3` | Descriptive | `K5`: `n`, `p99`, `max`, fraction `> 2 s`, and buildup episodes (capture-path limitation, non-gating) |

Additional health gates: zero unplanned restarts, `0` dropped shadow batches, `100%` scaler parity, `0` shadow errors. Filter note: `rev7`/`rev8` use filter `F2` whereas `B5` used `F1` (`0.13%` server-traffic difference).
