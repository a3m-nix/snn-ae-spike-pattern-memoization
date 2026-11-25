# Addendum S7p-03 — Single Persistent FNIRSI Logger Stream (30 Oct 2026, ~20:58 WIB)

## Rationale

Continuation Run 2 (`ADDENDUM_S7P_02.md`) failed at 20:49 with captured `stderr`:
- The first USB open (`preflight`) succeeded and drained cleanly (`rc = 0`).
- Reopening 68 s later for `S7h` passed `set_configuration`, but the first read after `request_data` timed out (`USBTimeoutError [Errno 110]`).

Because FNB-58 stops responding to repeated reopen requests, a single persistent logger process is kept open for the remainder of the run.

## Deviations

1. **Single persistent logger process:** one `fnirsi_logger.py` (`python3 -u`, `FNIRSI_NO_RESET=1`) is opened once at start, streaming `stdout` to `logs/fnirsi_stream_<timestamp>.txt`, and stopped cleanly at end.
2. **Tail shim for blocks:** `S7h` and `S7g-more` invoke `--fnirsi_path 03-scripts/s7p/fnirsi_tail.py`, which tails newly appended lines (5 ms polling, line-buffered flush) without touching USB. `FNIRSIReader`, energy math, and locked block scripts remain untouched.
3. **Measurement impact:** ≤ 5–10 ms added delivery latency relative to direct pipe, negligible over `≥ 30 s` windows.
4. **Preflight:** ≥ 10 lines in the stream within the first 12 s; liveness verified before each block (`rc = 5` on death).
5. The 60 s inter-process pause (`ADDENDUM_S7P_01.md`) is removed as USB is no longer reopened between blocks.
6. **Pre-run dry test:** validated with mock stream through `FNIRSIReader` (279 readings in 3 s; clean `stop()`).

## Analysis

Unchanged from `DESIGN_S7P_POWER.md §3` and `ADDENDUM_S7P_01.md`.

## Post-Run Note (23:49 WIB, After Completion)

- Run completed at 23:44:15 (`STATUS done`) with **174/174 `valid=True`** conditions (`S7h ciciot2023`: 30; `S7g-more`: 144).
- Because non-interactive background bash processes inherit `SIG_IGN` for `SIGINT`, the `EXIT` trap did not stop the logger; it was subsequently closed cleanly (`rc = 0`) via the built-in `fnirsi_stop` sentinel file at 23:47:56 (`rc_rest = 0`) after all measurements had finished, with zero impact on data.
- Note: this post-run section was appended after `LOCK_S7P_REST3.sha256` was generated; the lock hash applies to the pre-run document.
