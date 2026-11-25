#!/usr/bin/env python3
"""
E3-7 native — analisis langkah 8 (prereg/PREREG_STEP8_v1.md §6). Argumen: --run <step8/runs/L8-...> [--out DIR]
Fungsi langkah 7 diimpor (e37_step7_analyze: load_run, validity, t0_map, analyze_A; e37_step7_rev7_analyze: lag_L);
direktori live diarahkan ke tree v24 dan daftar model ke 8 model langkah 8.
  Gerbang  G1 layanan sehat; G2 L1/L2 (LAG_CRITERION_v1); G3 0 batch shadow dibuang; G4 paritas scaler 100 %
  P1  SNN_AE_REUSE vs SNN_AE_B: fraksi paket bit-identik (kriteria 1,0) dan daftar event/close identik
  P2  rasio waktu skor per paket SNN_AE_REUSE / Dense_AE_B per batch (n >= 32): median, CI 95 % bootstrap blok
      per menit (2000 ulangan, seed 8); agregat sum/sum. Lolos bila batas atas CI < 1
  P3  pasangan sekunder (deskriptif, dua arah): RQT/AQ3, RQT/AQ2, REUSE/AQ3, REUSE/AQ2, RQT/Dense_AE_B,
      SNN_AE/Dense_AE (runtime)
  P4  hit rate varian ber-cache per fase (B, M), CI bootstrap blok per menit
  P5  deteksi fase M per model (aturan langkah 7: event dalam [t0, t0+10 s]) dan event selama fase B
  P6  waktu ekstraksi fitur produksi per paket vs waktu skor shadow per paket (median per batch)
Output: <run>/analysis/step8_analysis.json
"""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/home/a3m-nix/disertasi-snn")
sys.path.insert(0, str(Path(__file__).parent))
import e37_step7_analyze as A7  # noqa: E402
import e37_step7_rev7_analyze as R  # noqa: E402

A7.LIVE = ROOT / "15-paced-replay" / "edge-live-interface-v24-shadowopt" / "results"
MODELS = ("SNN_AE", "Dense_AE", "SNN_AE_B", "SNN_AE_REUSE", "SNN_AE_RQT", "Dense_AE_B", "Dense_AE_AQ3", "Dense_AE_AQ2")
A7.MODELS = MODELS
PAIRS = [("SNN_AE_REUSE", "Dense_AE_B"), ("SNN_AE_RQT", "Dense_AE_AQ3"), ("SNN_AE_RQT", "Dense_AE_AQ2"),
         ("SNN_AE_REUSE", "Dense_AE_AQ3"), ("SNN_AE_REUSE", "Dense_AE_AQ2"), ("SNN_AE_RQT", "Dense_AE_B"),
         ("SNN_AE", "Dense_AE")]
NMIN_BATCH, NBOOT, SEED = 32, 2000, 8


def block_boot(values, blocks, stat, nboot=NBOOT, seed=SEED):
    """CI 95 % bootstrap blok: blok (menit) diambil ulang dengan pengembalian, statistik dihitung ulang."""
    ub = np.unique(blocks)
    idx = {b: np.nonzero(blocks == b)[0] for b in ub}
    rng = np.random.default_rng(seed); est = []
    for _ in range(nboot):
        pick = np.concatenate([idx[b] for b in rng.choice(ub, len(ub), replace=True)])
        est.append(stat(values[pick]))
    return [float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))]


def phase_of(wall, S):
    k = S["k"]
    b0, b1 = k["PHASE_B_START"]["rpi_time"], k["PHASE_B_END"]["rpi_time"]
    m0 = k["PHASE_M_START"]["rpi_time"]; m1 = k.get("SESSION_END", S["recs"][-1])["rpi_time"]
    ph = np.full(len(wall), "", dtype=object)
    ph[(wall >= b0) & (wall < b1)] = "B"; ph[(wall >= m0) & (wall <= m1)] = "M"
    return ph


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--run", required=True); ap.add_argument("--out")
    a = ap.parse_args()
    S = A7.load_run(Path(a.run))
    live = S["live"]
    res = {"run": S["dir"].name, "live_run": live.name, "capture": S["cap"].name,
           "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

    # ---- gerbang
    sv = A7.shadow_validity(live)
    lag = R.lag_L(live, S["lo"], S["hi"])
    restarts = A7.journal(S["lo"], S["hi"], "EDGE_LIVE_INTERFACE_RUNNING")
    res["validity"] = A7.validity(S)
    res["gates"] = {"G1_service": {"final_pass": sv["final_pass"], "detector_errors": sv["detector_errors"],
                                   "child_rc": sv["child_rc"], "shadow_errors": sv["errors"],
                                   "restarts_in_window": len(restarts),
                                   "pass": bool(sv["final_pass"] and not sv["detector_errors"] and sv["child_rc"] == 0
                                                and not sv["errors"] and len(restarts) == 0)},
                    "G2_lag": {"L1_pass": lag["L1_pass"], "L2_pass": lag["L2_pass"], "L1": lag["L1"], "L2": lag["L2"],
                               "pass": bool(lag["L1_pass"] and lag["L2_pass"])},
                    "G3_drops": {"dropped_batches": sv["dropped_batches"], "pass": sv["dropped_batches"] == 0},
                    "G4_parity": {"rows": sv["scaler_parity_rows"], "bad": sv["scaler_parity_bad_rows"],
                                  "pass": bool(sv["scaler_parity_rows"] and sv["scaler_parity_bad_rows"] == 0)}}
    res["gates"]["pass"] = all(v["pass"] for v in res["gates"].values() if isinstance(v, dict))
    res["lag_full"] = lag

    # ---- P1
    pk = np.load(live / "shadow_packets.npz")
    sa, sb = pk["SNN_AE_REUSE"], pk["SNN_AE_B"]
    ev = {m: [] for m in MODELS}; cl = {m: [] for m in MODELS}
    for e in csv.DictReader(open(live / "shadow_events.csv")):
        (ev if e["kind"] == "EVENT" else cl)[e["model"]].append(float(e["ts"]))
    res["P1"] = {"packets": int(len(sa)), "bitid_frac": float(np.mean(sa.view(np.uint32) == sb.view(np.uint32))) if len(sa) else None,
                 "events_identical": ev["SNN_AE_REUSE"] == ev["SNN_AE_B"] and cl["SNN_AE_REUSE"] == cl["SNN_AE_B"],
                 "events": {m: len(ev[m]) for m in MODELS}}
    res["P1"]["pass"] = bool(res["P1"]["bitid_frac"] == 1.0 and res["P1"]["events_identical"])

    # ---- P2/P3 waktu
    tz = np.load(live / "shadow_timing.npz")
    names = [str(x) for x in tz["models"]]; col = {m: i for i, m in enumerate(names)}
    n, dt, wall = tz["n"], tz["dt_ns"].astype(np.float64), tz["wall"]
    big = n >= NMIN_BATCH
    minute = np.floor(wall / 60).astype(np.int64)
    ph = phase_of(wall, S)
    res["timing_batches"] = {"total": int(len(n)), "n_ge_32": int(big.sum()), "packets_in_n_ge_32": int(n[big].sum()),
                             "first_variant_counts": np.bincount(tz["first"], minlength=len(names)).tolist()}
    res["us_per_packet"] = {}
    for m in names:
        res["us_per_packet"][m] = {"aggregate_all": float(dt[:, col[m]].sum() / n.sum() / 1e3),
                                   "median_batch_n_ge_32": float(np.median(dt[big, col[m]] / n[big] / 1e3)) if big.any() else None}
    res["pairs"] = {}
    for x, y in PAIRS:
        r = dt[big, col[x]] / dt[big, col[y]]
        d = {"median_ratio": float(np.median(r)) if len(r) else None,
             "ci95_block_minute": block_boot(r, minute[big], np.median) if len(r) else None,
             "aggregate_ratio": float(dt[:, col[x]].sum() / dt[:, col[y]].sum()),
             "by_phase": {p: float(np.median(r[ph[big] == p])) if (ph[big] == p).any() else None for p in ("B", "M")},
             "small_batches_median_ratio": float(np.median(dt[~big, col[x]] / dt[~big, col[y]])) if (~big).any() else None}
        res["pairs"][f"{x}/{y}"] = d
    p2 = res["pairs"]["SNN_AE_REUSE/Dense_AE_B"]
    res["P2"] = {**p2, "pass": bool(p2["ci95_block_minute"] and p2["ci95_block_minute"][1] < 1.0)}

    # ---- P4 hit rate per fase
    cached = [str(x) for x in tz["cached"]]; hc = tz["hits_cum"].astype(np.int64)
    dh = np.diff(np.concatenate([np.zeros((1,) + hc.shape[1:], np.int64), hc]), axis=0)
    res["P4"] = {}
    for i, m in enumerate(cached):
        d = {}
        for p in ("B", "M"):
            w = ph == p
            h, mi = dh[w, i, 0], dh[w, i, 1]
            if (h + mi).sum():
                d[p] = {"hit_rate": float(h.sum() / (h + mi).sum()), "lookups": int((h + mi).sum()),
                        "ci95_block_minute": block_boot(np.stack([h, mi], 1), minute[w],
                                                        lambda z: z[:, 0].sum() / max(1, z.sum()))}
        res["P4"][m] = d

    # ---- P5 deteksi
    A = A7.analyze_A(S)
    res["P5"] = {"injections": A["injections"], "per_model": A["per_model"],
                 "phase_B_events": {m: sum(S["k"]["PHASE_B_START"]["rpi_time"] <= t <= S["k"]["PHASE_B_END"]["rpi_time"]
                                           for t in ev[m]) for m in MODELS},
                 "mcnemar_vs_SNN_AE_descriptive": A["mcnemar_snn_vs_baseline_ML"]}

    # ---- P6 ekstraksi fitur produksi
    fe = []
    with open(live / "packet_runtime_records.csv") as f:
        for r in csv.DictReader(f):
            v = r.get("feature_extraction_ms")
            if v not in (None, "", "None"):
                fe.append(float(v))
    fe = np.array(fe)
    res["P6"] = {"feature_extraction_ms_per_packet_median": float(np.median(fe)) if len(fe) else None,
                 "feature_extraction_n": int(len(fe)),
                 "shadow_score_us_per_packet": {m: res["us_per_packet"][m]["aggregate_all"] for m in names},
                 "scaler_us_per_packet": float(tz["scaler_ns"].sum() / n.sum() / 1e3)}

    od = Path(a.out) if a.out else S["dir"] / "analysis"; od.mkdir(parents=True, exist_ok=True)
    (od / "step8_analysis.json").write_text(json.dumps(res, indent=2, default=float) + "\n")
    print(json.dumps({"gates": res["gates"]["pass"], "P1": res["P1"]["pass"], "P2": res["P2"]["median_ratio"],
                      "P2_ci": res["P2"]["ci95_block_minute"], "P2_pass": res["P2"]["pass"]}, default=float))
    print("OUT", od / "step8_analysis.json")


if __name__ == "__main__":
    main()
