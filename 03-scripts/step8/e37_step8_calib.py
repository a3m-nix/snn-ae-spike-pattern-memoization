#!/usr/bin/env python3
"""
E3-7 native — LANGKAH 8.0: data bantu dan threshold O4 untuk varian optimasi (DESIGN_STEP8_LIVE_OPT.md §5).
Set kalibrasi = set O4 langkah 4 (O4_NATIVE_RULES_v1, diimpor dari e37_native_o4.py, tidak disalin ulang selain
definisi filter `keeps`). Tidak membaca data serangan, holdout, atau data langkah 5/7.
  G0'  skor SNN_AE dan Dense_AE runtime per segmen bit-identik dengan calib_scores_native.npz langkah 4
  aux  delta2/delta3 (s7g aq_delta: p99,9 h1 / (2^b - 1)) dan R_tri (s7j rq_table mode T) dari Zn kalibrasi gabungan
  thr  p90 skor kalibrasi gabungan per varian (aturan O4 tanpa perubahan); SNN_AE_REUSE wajib bit-identik dengan
       SNN_AE_B (C1) sehingga thresholdnya sama; varian ber-cache wajib tidak bergantung isi awal cache (C2)
  prefill  Zn kalibrasi gabungan setiap paket ke-12 (urutan segmen O4) untuk isi awal cache live
Output: results/step8-calib-<stamp>/{opt_aux.npz, prefill_calib.npz, thresholds_step8.json}. Tidak mengubah sistem.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path("/home/a3m-nix/disertasi-snn")
OUT = ROOT / "23-e37-native"
V24 = ROOT / "15-paced-replay" / "edge-live-interface-v24-shadowopt"
ART = OUT / "step8" / "artifacts"
O4_RES = OUT / "results" / "o4-native-20261026-180510"
sys.path.insert(0, str(OUT / "scripts"))
sys.path.insert(0, str(V24 / "canonical"))
import e37_native_o4 as O  # noqa: E402
import opt_kernels as K  # noqa: E402

F = O.F
LIBS = {"s7c": ART / "s7c_native_copy.so", "s7i": ART / "s7i_kernels.so", "s7j": ART / "s7j_kernels.so"}
LIB_SHA = {"s7c": "6ae3976dada98cc8637feac0116b2c3d2b53503db7ebfbffb3008b0a7807e168",
           "s7i": "b948a30a6ad48ead89bb6d9a9cf2f2a966f00c841669e0da8f946e26382e2e62",
           "s7j": "ff10c62b1baf065bb9b604851a4af9bb5dac0ccf2584d9739557e5585ac8091a"}
O4_NPZ_SHA = None          # dicatat; integritas dibuktikan oleh G0' (bit-identik)
PREFILL_STRIDE = 12
LOGCAP = 16


def main():
    t_run = time.time()
    for p, want in O.EXPECT.items():
        if want is not None and O.sha(p) != want:
            raise SystemExit(f"SHA_MISMATCH {p}")
    rt = O.EdgeAERuntime()
    nsc = rt.scaler(str(OUT / "artifacts" / "scaler_site17_native.npz"))
    nm = {m: rt.model(str(O.PAY / f"weights_{m}.npz")) for m in ("SNN_AE", "Dense_AE")}
    ref = np.load(O4_RES / "calib_scores_native.npz")
    T4 = json.loads((O4_RES / "thresholds_o4_native.json").read_text())

    # ---- set kalibrasi: definisi persis e37_native_o4.main()
    split = json.loads((F.REFIT / "report.json").read_text())["split_epoch"]
    recs = [json.loads(l) for l in open(F.A1 / "orchestrator.jsonl")]
    inj = [r for r in recs if r["kind"] == "INJECT"]
    off = float(np.mean([r["kali_minus_rpi_s"] for r in recs if r["kind"] == "CLOCK_OFFSET"]))
    wins = [(r["kali_start"] - off - 1, r["kali_end"] - off + 10) for r in inj] + [(1792747645.0, 1792747656.0)]

    def a1_bg(ts):
        k = np.ones(len(ts), bool)
        for a, b in wins:
            k &= ~((ts >= a) & (ts <= b))
        return k

    keeps = {"cal17_holdout": lambda ts: ts >= split, "d21_pre0300": lambda ts: ts < 1792612825.0,
             "B1": None, "B2": None, "A1_background": a1_bg}
    Zs, cal_ts, g0 = {}, {}, {}
    for name, p in O.CAL_TSV.items():
        ts, X = O.load(p, keeps[name])
        Z = nsc.transform(X); del X
        g0[name] = {m: bool(np.array_equal(nm[m].score(Z), ref[f"{name}__{m}"])) for m in nm}
        g0[name]["ts"] = bool(np.array_equal(ts, ref[f"{name}__ts"]))
        Zs[name], cal_ts[name] = Z, ts
        print("cal", name, len(ts), g0[name], flush=True)
    n_all = sum(len(t) for t in cal_ts.values())
    g0_pass = n_all == O.G0_N and all(all(v.values()) for v in g0.values())
    print("G0'", n_all, g0_pass, flush=True)
    if not g0_pass:
        raise SystemExit("G0'_FAIL: kalibrasi tidak sama dengan langkah 4; berhenti")

    # ---- data bantu dari kalibrasi gabungan
    Zall = np.concatenate([Zs[n] for n in O.CAL_TSV])
    w = {"SNN_AE": K.weights(O.PAY / "weights_SNN_AE.npz"), "Dense_AE": K.weights(O.PAY / "weights_Dense_AE.npz")}
    aux = {"delta2": K.aq_delta(w["Dense_AE"], Zall, 2), "delta3": K.aq_delta(w["Dense_AE"], Zall, 3)}
    aux["R_tri"], rq_counts = K.rq_table_tri(w["SNN_AE"], Zall)
    print("aux", {k: v.tolist()[:4] for k, v in aux.items()}, flush=True)
    libs = K.load_libs(LIBS, LIB_SHA)

    # ---- skor varian pada kalibrasi (cache dingin), threshold p90
    scores = {}
    for m in K.OPT:
        om = K.OptModel(m, libs, w[K.BASE[m]], aux, LOGCAP)
        scores[m] = {n: om.score(Zs[n]) for n in O.CAL_TSV}
        h, mi = om.hits()
        print("score", m, "hit_rate_cold" if om.keys is not None else "", (h / (h + mi)) if h + mi else "", flush=True)
    c1 = all(np.array_equal(scores["SNN_AE_REUSE"][n], scores["SNN_AE_B"][n]) for n in O.CAL_TSV)
    prefill = np.ascontiguousarray(Zall[::PREFILL_STRIDE], np.float32)
    c2 = {}
    for m in K.CACHED:
        om = K.OptModel(m, libs, w[K.BASE[m]], aux, LOGCAP); om.prefill(prefill)
        c2[m] = bool(np.array_equal(om.score(Zs["B2"]), scores[m]["B2"]))
    print("C1", c1, "C2", c2, flush=True)
    if not (c1 and all(c2.values())):
        raise SystemExit("C1/C2_FAIL: varian tidak eksak/deterministik; berhenti")
    agree = {}
    for m, b in (("SNN_AE_B", "SNN_AE"), ("Dense_AE_B", "Dense_AE")):
        a = np.concatenate([scores[m][n] for n in O.CAL_TSV]); r = np.concatenate([ref[f"{n}__{b}"] for n in O.CAL_TSV])
        agree[m] = {"bit_identical_frac": float(np.mean(a.view(np.uint32) == r.view(np.uint32))),
                    "max_abs_diff": float(np.max(np.abs(a - r)))}
    models = {}
    for m in K.OPT:
        allm = np.concatenate([scores[m][n] for n in O.CAL_TSV])
        th = float(np.percentile(allm, O.PCT_PRIMARY))
        models[m] = {"threshold_o4": th,
                     "threshold_grid": {f"p{p:g}": float(np.percentile(allm, p)) for p in O.PCT_GRID},
                     "calibration": O.calib_diag(cal_ts, scores[m], th)}
        print(m, f"thr={th:.6f}", "ep_cal(persist)", models[m]["calibration"]["persist"]["episodes_total"], flush=True)
    for m in ("SNN_AE", "Dense_AE"):
        models.setdefault("_runtime_ref", {})[m] = T4["models"][m]["threshold_o4"]

    stamp = time.strftime("%Y%m%d-%H%M%S")
    od = OUT / "results" / f"step8-calib-{stamp}"; od.mkdir(parents=True)
    np.savez(od / "opt_aux.npz", **aux)
    np.savez(od / "prefill_calib.npz", Z=prefill)
    np.savez_compressed(od / "calib_scores_step8.npz", **{f"{n}__{m}": scores[m][n] for m in K.OPT for n in O.CAL_TSV},
                        rq_tri_pattern_counts=rq_counts)
    res = {"design": "DESIGN_STEP8_LIVE_OPT.md", "rules": "prereg/O4_NATIVE_RULES_v1.md (tanpa perubahan)",
           "G0prime": {"n": int(n_all), "per_segment": g0, "pass": g0_pass}, "C1_reuse_bitid_calib": c1,
           "C2_prefill_invariant": c2, "build_vs_runtime_agreement": agree, "logcap": LOGCAP,
           "prefill_stride": PREFILL_STRIDE, "prefill_n": int(len(prefill)), "models": models,
           "libs_sha256": LIB_SHA, "calibration_n": {n: int(len(t)) for n, t in cal_ts.items()},
           "files_read": O.READ, "o4_ref": str(O4_RES), "script_sha256": O.sha(__file__),
           "opt_kernels_sha256": O.sha(K.__file__),
           "outputs_sha256": {f: O.sha(od / f) for f in ("opt_aux.npz", "prefill_calib.npz", "calib_scores_step8.npz")},
           "elapsed_s": round(time.time() - t_run, 1)}
    f = od / "thresholds_step8.json"; f.write_text(json.dumps(res, indent=2) + "\n")
    print("OUT", f)


if __name__ == "__main__":
    main()
