#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7j RPi — SNN-AE + cache dengan kunci kode spike terkuantisasi (DESIGN_S7J_RQ.md). Memakai s7i_rpi/s7g_rpi (diimpor).
  SNN_RQC_{cap}: kunci = jumlah spike per neuron (0..3);   SNN_RQT_{cap}: kunci = min(jumlah, 2).
  Dekoder diberi pola spike kanonik per kelas (pola tersering di validasi, per neuron, per unit).
Fase: check (deterministik, tak bergantung cap & isi awal cache), accuracy (3 unit), latency (grid v3 + RQ).
"""
# ======== END: HEADER ========
import ctypes
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "s7i"))
import s7i_rpi as I  # noqa: E402

G, F = I.G, I.F
CAPS = [16, 18, 20]
G.GRID = (["DENSE_ZS"] + [f"SNN_MEMOV3_{c}" for c in CAPS] + [f"DENSE_AQV3{b}_{c}" for b in (2, 3) for c in CAPS]
          + [f"SNN_RQ{m}_{c}" for m in "CT" for c in CAPS])
_load_libs, _run, _load_unit = G.load_libs, G.run, G.load_unit
DEFAULT = {"C": {0: 0, 1: 4, 2: 6, 3: 7}, "T": {0: 0, 1: 4, 2: 6}}


def load_libs():
    libs = _load_libs()
    so = HERE / "build" / "s7j_kernels.so"
    so.parent.mkdir(exist_ok=True)
    subprocess.run(["gcc", "-O3", "-mcpu=native", "-shared", "-fPIC", "-o", str(so), str(HERE / "s7j_kernels.c")],
                   check=True)
    k = ctypes.CDLL(str(so))
    a = list(G._s7i.snn_memo_v3.argtypes)
    k.snn_rq_memo.argtypes = a[:16] + [F.U32P, ctypes.c_int] + a[16:]
    k.snn_rq_memo.restype = ctypes.c_int
    G._s7j = k
    return libs


def rq_table(w, Xval, m):
    """R[k*3+t]: mask neuron yang pola kanoniknya untuk kelas k berisi spike pada time step t."""
    ce = Xval.astype(np.float32) @ w["We"] + w["be"]
    u, P = np.zeros_like(ce), np.zeros(ce.shape, np.int64)
    for t in range(3):
        u = w["dk_e"] * u + ce
        sp = u > w["th_e"]
        u = np.where(sp, u - w["th_e"], u)
        P |= sp.astype(np.int64) << t
    c = np.vectorize(lambda z: bin(z).count("1"))(P)
    if m == "T":
        c = np.minimum(c, 2)
    R = np.zeros(12, np.uint32)
    for j in range(32):
        for k in DEFAULT[m]:
            src = P[c[:, j] == k, j]
            rep = int(np.bincount(src, minlength=8).argmax()) if len(src) else DEFAULT[m][k]
            for t in range(3):
                if (rep >> t) & 1:
                    R[k * 3 + t] |= np.uint32(1 << j)
    return R


def load_unit(pkg, unit):
    W, S, Xval = _load_unit(pkg, unit)
    for m in "CT":
        W["SNN_AE"][f"R{m}"] = rq_table(W["SNN_AE"], Xval, m)
    return W, S, Xval


def run(libs, v, W, X, err, st, cache=None):
    if not v.startswith("SNN_RQ"):
        return _run(libs, v, W, X, err, st, cache)
    w, p, m = W["SNN_AE"], F.p, v[6]
    rc = G._s7j.snn_rq_memo(p(X), len(X), w["din"], w["L"], w["dout"], w["T"], p(w["We"]), p(w["be"]), w["th_e"],
                            w["dk_e"], p(w["Wd"]), p(w["bd"]), w["th_d"], w["dk_d"], p(w["Wo"]), p(w["bo"]),
                            p(w[f"R{m}"], F.U32P), 0 if m == "C" else 1,
                            p(cache.keys, F.U32P), p(cache.ys), cache.logcap, p(err), p(st, F.I64P))
    if rc != 0:
        raise SystemExit(f"{v}: argumen kernel tidak valid")


def make_cache(libs, v, W, Xval, prefill=True):
    if not v.startswith("SNN_RQ"):
        return _make_cache(libs, v, W, Xval, prefill)
    c = F.Cache(int(v.rsplit("_", 1)[1]), W["SNN_AE"]["dout"])
    if prefill:
        run(libs, v, W, Xval, np.empty(len(Xval), np.float32), np.zeros(5, np.int64), c)
    c.take_snapshot()
    return c


def phase_check(libs, pkg, units, res, args):
    rows = []
    for u in units:
        W, S, Xval = load_unit(pkg, u)
        X = S["X"][S["order_capture"]].copy()
        row = {"unit": u}
        for m in "CT":
            outs = []
            for c in CAPS:
                for pf in (False, True):
                    cc = make_cache(libs, f"SNN_RQ{m}_{c}", W, Xval, prefill=pf)
                    e = np.empty(len(X), np.float32)
                    run(libs, f"SNN_RQ{m}_{c}", W, X, e, np.zeros(5, np.int64), cc)
                    outs.append(e)
            row[f"RQ{m}_invariant_cap_and_prefill"] = bool(all(np.array_equal(outs[0], z) for z in outs[1:]))
            row[f"RQ{m}_finite"] = bool(np.isfinite(outs[0]).all())
        row["pass"] = all(v for kk, v in row.items() if kk != "unit")
        rows.append(row)
        G.log(f"[S7j] CHECK {args.dataset} {u}: {row}")
    out = {"dataset": args.dataset, "system": F.sys_info(), "rows": rows, "pass": all(r["pass"] for r in rows)}
    (res / f"check_{args.dataset}.json").write_text(G.json.dumps(out, indent=2))
    if not out["pass"]:
        raise SystemExit(3)


def phase_accuracy(libs, pkg, units, res, args):
    rows = []
    for u in units:
        W, S, Xval = load_unit(pkg, u)
        X, y = S["X"], S["y"].astype(int)
        for name, v in [("SNN_AE", "SNN_COUNT"), ("SNN_RQC", "SNN_RQC_16"), ("SNN_RQT", "SNN_RQT_16"),
                        ("DENSE", "DENSE"), ("DENSE_AQ2", "DENSE_AQV32_16"), ("DENSE_AQ3", "DENSE_AQV33_16")]:
            sv, st = G.scores(libs, v, W, Xval, Xval), G.scores(libs, v, W, X, Xval)
            rows.append({"dataset": args.dataset, "unit": u, "model": name,
                         **G.det_metrics(st.astype(np.float64), y, float(np.percentile(sv, 99)))})
    pd.DataFrame(rows).to_csv(res / f"accuracy_{args.dataset}.csv", index=False)
    G.log(f"[S7j] ACCURACY {args.dataset}: " + "; ".join(
        f"{r['model']} {r['auc']:.4f}/{r['f1_p99']:.4f}" for r in rows if r["unit"] == units[0]))


_make_cache = G.make_cache
G.load_libs, G.run, G.load_unit, G.make_cache = load_libs, run, load_unit, make_cache
G.phase_check, G.phase_accuracy = phase_check, phase_accuracy

if __name__ == "__main__":
    if "--result" not in sys.argv:
        sys.argv += ["--result", str(HERE.parent / "0-revision-results-v2" / "s7j")]
    G.main()
