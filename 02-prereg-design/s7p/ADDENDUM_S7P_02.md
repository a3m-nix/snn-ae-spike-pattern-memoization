# Addendum S7p-02 — Second Continuation with Diagnostic Logger Wrapper (30 Oct 2026, ~20:47 WIB)

## Events Since Addendum 01

- **16:15 and 16:25:** continuation preflight failed in `dev.set_configuration()` (`USBError Entity not found`).
- **16:28:** after Pi reboot and moving USB to bus 3, preflight failed with `USBError Other error`.
- **16:30:59:** after full FNB-58 power cycle, preflight passed (1,168 lines in 12 s), but `S7h ciciot2023` failed at 16:32:47 (`"No FNIRSI readings during idle measurement"`).
- **16:57–20:45:** intermittent USB enumeration errors (`-71`) resolved after replacing/reseating data cable and rebooting.

## Deviations

1. All logger invocations (`preflight`, `S7h`, `S7g-more`) route through `s7p/fnirsi_logger_wrap.py` (`PREFLIGHT_LOGGER` / `--fnirsi_path`).
2. Wrapper forwards `stdout` verbatim (voltage/current values and sampling rate unchanged) and logs `stderr` to `logs/fnirsi_stderr.log`.
3. **Signal handling:** `SIGTERM` from `FNIRSIReader.stop()` is translated to `SIGINT` so the logger drains the USB endpoint cleanly before exit.
4. Blocks, arguments, order, and 60 s pause remain identical to `run_s7p_rest.sh`.

## Analysis

Unchanged from `DESIGN_S7P_POWER.md §3` and `ADDENDUM_S7P_01.md`; previously completed conditions (`S7j` 108, `S7h edge_iiotset` 30) are not re-measured.
