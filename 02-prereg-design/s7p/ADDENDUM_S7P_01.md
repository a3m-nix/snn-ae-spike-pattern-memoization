# Addendum S7p-01 — Continuation After FNB-58 Stall (30 Oct 2026, ~16:00 WIB)

## Incident

- **15:53:00:** FNB-58 stopped emitting readings upon reopening the logger at the start of `S7h ciciot2023` (`"No FNIRSI readings during idle measurement"`, exit `rc = 3`).
- **Diagnostics:** single preflight without reset returned 0 lines in 12 s; USB device remained visible in `lsusb` with no kernel errors.
- **Already recorded valid data:** `S7j` (`108/108` valid) and `S7h edge_iiotset` (`30/30` valid); zero `valid=False` conditions.

## Protocol Deviations

1. **Resume remaining blocks only** (`run_s7p_rest.sh`): `S7h ciciot2023` followed by `S7g-more` (`edge_iiotset`, `ciciot2023`) with identical block arguments; completed valid blocks are not re-measured.
2. **60 s cooldown pause before each new logger-opening process** (procedural change only, motivated by the observation that both stalls at 00:02 and 15:53 occurred immediately upon reopening the USB logger).
3. **Executed via `setsid nohup` under `e37-lock`** rather than `systemd`.
4. **Prerequisite:** physical USB unplug/replug of the FNB-58.

## Analysis

Unchanged from `DESIGN_S7P_POWER.md §3`. Cross-session conditions (`S7h ciciot2023`, `S7g-more`) are noted for sensitivity; within-block dominance comparisons are unaffected.
