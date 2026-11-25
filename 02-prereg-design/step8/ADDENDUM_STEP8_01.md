# Addendum 01 to Step 8: Two Analysis-Script Gate Flags Explained (31 Oct 2026, ~15:40 WIB)

Written after running the locked single-pass analysis (`step8_analysis.json`). That output was **neither modified nor re-run**. This addendum documents two script-level gate flags (`restarts_in_window = 1` and `wlan0_stable = false`) with system-journal evidence; no endpoint numbers changed.

## 1. G1 `restarts_in_window = 1`

- `e37_step8_analyze.py` counts all `EDGE_LIVE_INTERFACE_RUNNING` log entries inside `[capture_start, SESSION_END]`.
- The closing restart (`session_end_write_outputs`) is explicitly part of the pre-registered shutdown protocol to flush outputs before `SESSION_END` is logged, so the script counted that scheduled shutdown restart as `1`.
- **Service journal evidence (`snn-edge-live`):**
  - `1793430675`: initial `rev8` deployment restart;
  - `1793430759`: session-start clean restart (`session_start_clean_run`, prior to capture at `1793430786`);
  - `1793435503`: protocol-scheduled closing restart (`session_end_write_outputs`).
  - Zero unplanned restarts occurred; all other `G1` checks passed (`FINAL_SUMMARY` pass, `0` detector/shadow errors, child `rc = 0`, `restarts = 0` across all 12 Phase B ticks).
- **Verdict per pre-registered intent (`DESIGN_STEP8_LIVE_OPT.md §7`, "without unplanned restarts"): `G1` passed.**

## 2. Validity V3 `wlan0_stable = false`

- The `validity` helper inherited from Step 7 checks for a `wlan0` field in `TICK` records; `e37_step8_session.py` omitted that field from `TICK`, causing `all(...)` to evaluate `False`.
- **Evidence:** `NetworkManager` journal (14:12–15:35) shows zero `wlan0` state changes; both preflight and post-session checks confirmed stable association to the office AP (`[REDACTED_SSID]`); capture proceeded continuously (`287,043` raw lines).
- **Verdict: `V3` satisfied** (`V1, V2, V4, V5` all passed in the locked JSON).

## 3. Impact

All gates (`G1–G4`) and validity conditions (`V1–V5`) are satisfied, so `P1–P6` are interpreted per `PREREG_STEP8_v1.md §7`. Locked analysis scripts remain untouched.
