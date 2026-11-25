#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7i RPi — optimasi lanjutan SNN-AE + cache (DESIGN_S7I_OPT.md). Memakai s7g_rpi.py (diimpor, tidak diubah).
Tambahan:
  - SNN_MEMOV3_{cap}  : snn_memo_v3 (jalur miss NEON), wajib bit-identik dengan SNN_COUNT.
  - DENSE_AQV3{b}_{cap}: dense_aq_memo_v3 (jalur miss NEON, simetris), wajib bit-identik dengan DENSE_AQ{b} (s7f).
  - kapasitas cache 2^16, 2^18, 2^20 untuk kedua famili v3; v2 pada 2^16 sebagai jangkar ke S7g.
Fase: check (bit-identik), latency (seluruh grid, capture & acak, urutan varian diacak). Tanpa FNIRSI.
"""
# ======== END: HEADER ========
import ctypes
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "s7g"))
import s7g_rpi as G  # noqa: E402

F = G.F
CAPS3 = [16, 18, 20]
G.GRID = (["DENSE", "DENSE_ZS", "SNN_COUNT", "DENSE_AQV22_16", "DENSE_AQV23_16", "SNN_MEMOV2_16"]
          + [f"DENSE_AQV3{b}_{c}" for b in (2, 3) for c in CAPS3] + [f"SNN_MEMOV3_{c}" for c in CAPS3])
_load_libs, _run = G.load_libs, G.run


def load_libs():
    s7c, memo, g = _load_libs()
    so = HERE / "build" / "s7i_kernels.so"
    so.parent.mkdir(exist_ok=True)
    subprocess.run(["gcc", "-O3", "-mcpu=native", "-shared", "-fPIC", "-o", str(so), str(HERE / "s7i_kernels.c")],
                   check=True)
    k = ctypes.CDLL(str(so))
    k.snn_memo_v3.argtypes, k.snn_memo_v3.restype = g.snn_memo_v2.argtypes, ctypes.c_int
    k.dense_aq_memo_v3.argtypes, k.dense_aq_memo_v3.restype = g.dense_aq_memo_v2.argtypes, ctypes.c_int
    G._s7i = k
    return s7c, memo, g


def run(libs, v, W, X, err, st, cache=None):
    k, p = G._s7i, F.p
    if v.startswith("DENSE_AQV3"):
        d, b = W["Dense_AE"], int(v[10])
        rc = k.dense_aq_memo_v3(p(X), len(X), d["din"], d["L"], d["dout"], p(d["We"]), p(d["be"]), p(d["Wd"]),
                                p(d["bd"]), p(d["Wo"]), p(d["bo"]), p(d[f"delta{b}"]), b, p(cache.keys, F.U32P),
                                p(cache.ys), cache.logcap, p(err), p(st, F.I64P))
    elif v.startswith("SNN_MEMOV3"):
        w = W["SNN_AE"]
        rc = k.snn_memo_v3(p(X), len(X), w["din"], w["L"], w["dout"], w["T"], p(w["We"]), p(w["be"]), w["th_e"],
                           w["dk_e"], p(w["Wd"]), p(w["bd"]), w["th_d"], w["dk_d"], p(w["Wo"]), p(w["bo"]),
                           p(cache.keys, F.U32P), p(cache.ys), cache.logcap, p(err), p(st, F.I64P))
    else:
        return _run(libs, v, W, X, err, st, cache)
    if rc != 0:
        raise SystemExit(f"{v}: argumen kernel tidak valid")


def phase_check(libs, pkg, units, res, args):
    rows = []
    for u in units:
        W, S, Xval = G.load_unit(pkg, u)
        X = S["X"][S["order_capture"]].copy()
        ref = np.empty(len(X), np.float32)
        run(libs, "SNN_COUNT", W, X, ref, np.zeros(5, np.int64))
        row = {"unit": u}
        for c in CAPS3:
            for pf in (False, True):
                cc = G.make_cache(libs, f"SNN_MEMOV3_{c}", W, Xval, prefill=pf)
                e = np.empty(len(X), np.float32)
                run(libs, f"SNN_MEMOV3_{c}", W, X, e, np.zeros(5, np.int64), cc)
                row[f"bitid_SNN_MEMOV3_{c}_{'val' if pf else 'cold'}"] = bool(np.array_equal(e, ref))
        for b in (2, 3):
            r = G.scores(libs, f"DENSE_AQ{b}_16", W, X, Xval)
            for c in CAPS3:
                row[f"bitid_DENSE_AQV3{b}_{c}_vs_AQ{b}"] = bool(np.array_equal(G.scores(libs, f"DENSE_AQV3{b}_{c}", W, X, Xval), r))
        row["pass"] = all(v for kk, v in row.items() if kk != "unit")
        rows.append(row)
        G.log(f"[S7i] CHECK {args.dataset} {u}: pass={row['pass']} {row}")
    out = {"dataset": args.dataset, "system": F.sys_info(), "rows": rows, "pass": all(r["pass"] for r in rows)}
    (res / f"check_{args.dataset}.json").write_text(G.json.dumps(out, indent=2))
    if not out["pass"]:
        raise SystemExit(3)


G.load_libs, G.run, G.phase_check = load_libs, run, phase_check

if __name__ == "__main__":
    if "--result" not in sys.argv:
        sys.argv += ["--result", str(HERE.parent / "0-revision-results-v2" / "s7i")]
    G.main()
