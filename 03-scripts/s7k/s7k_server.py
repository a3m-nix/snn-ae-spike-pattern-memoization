#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7k K1 (server nixfsv2) — deteksi per jenis serangan untuk varian optimasi, 30 unit per dataset (DESIGN_S7K.md §3).
Kernel, data unit, skor, threshold p99, dan metrik memakai modul s7x_ij.py (salinan tidak diubah dari 13-s7x-ij,
sha dicatat) beserta berkas C-nya, sehingga skor identik dengan S7x-ij. Label subtipe: kolom label_type
02-splits/full/<ds>/sample.parquet pada indeks test unit (E.unit_data). s3_final_eval.py tidak di-import (s7d_export_q8
hanya mengekstrak kelas SpikingLayer lewat AST, sama seperti S7x-ij).
Pemakaian: python s7k_server.py <dataset> [--units a,b] [--core 9]
"""
# ======== END: HEADER ========
import argparse
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("dataset", choices=["edge_iiotset", "ciciot2023"])
ap.add_argument("--units", default="all")
ap.add_argument("--core", type=int, default=9)
ap.add_argument("--out", default="results")
A = ap.parse_args()
sys.path.insert(0, str(HERE))
sys.argv = [str(HERE / "s7x_ij.py"), "--dataset", A.dataset, "--phase", "accuracy"]
import s7x_ij as X  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402

VARIANTS = ["SNN_EXACT", "SNN_RQC_16", "SNN_RQT_16", "DENSE_ZS", "DENSE_AQV33_16", "DENSE_AQV32_16"]
BASE = {"SNN_EXACT": "SNN_EXACT", "SNN_RQC_16": "SNN_EXACT", "SNN_RQT_16": "SNN_EXACT",
        "DENSE_ZS": "DENSE_ZS", "DENSE_AQV33_16": "DENSE_ZS", "DENSE_AQV32_16": "DENSE_ZS"}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] [s7k-K1 {A.dataset}] {m}", flush=True)


def main():
    os.sched_setaffinity(0, {A.core})
    L = X.load_libs()
    log(f"core {A.core} | nice {os.nice(0)} | kernel sha {X.sha(HERE / 's7x_ij_kernels_x86.c')[:12]}… | "
        f"s7x_ij.py sha {X.sha(HERE / 's7x_ij.py')[:12]}… | load {os.getloadavg()}")
    Xall, y, _ = X.E.load_all()
    t = pq.read_table(X.E.S1 / "sample.parquet", columns=["source_file", "source_row", "label_type"]).to_pandas()
    src = {"source_file": t.source_file.values, "source_row": t.source_row.values}
    lab_all = t.label_type.astype(str).values
    del t
    units = sorted(u.name for u in X.E.UNITS_DIR.iterdir() if u.is_dir() and u.name.startswith("s"))
    if A.units != "all":
        units = A.units.split(",")
    elif len(units) != 30:
        raise SystemExit(f"jumlah unit {len(units)} != 30")
    out = HERE / A.out / A.dataset
    out.mkdir(parents=True, exist_ok=True)
    for unit in units:
        fo, fs = out / f"{unit}_overall.csv", out / f"{unit}_subtype.csv"
        if fo.exists() and fs.exists():
            log(f"{unit}: checkpoint ada, dilewati")
            continue
        Xval, Xte, yte, W, orders, ident = X.unit_setup(Xall, y, src, unit)
        _, _, te = X.E.unit_data(Xall, y, unit)
        lab = lab_all[te]
        if len(lab) != len(yte) or not np.array_equal(lab != "normal", yte.astype(bool)):
            raise SystemExit(f"{unit}: label_type tidak konsisten dengan y (G0)")
        dec, overall, sub = {}, [], []
        for v in VARIANTS:
            sv = X.scores(L, v, W, Xval, Xval)
            st = X.scores(L, v, W, Xte, Xval).astype(np.float64)
            thr = float(np.percentile(sv, 99))
            m = X.det_metrics(st, yte, thr)
            dec[v] = st > thr
            overall.append({"dataset": A.dataset, "unit": unit, "variant": v, **m, "n_test": len(yte)})
            nrm = lab == "normal"
            for s in sorted(set(lab.tolist())):
                msk = lab == s
                r = {"dataset": A.dataset, "unit": unit, "variant": v, "subtype": s, "n": int(msk.sum()),
                     "positive_rate": float(dec[v][msk].mean())}
                if s != "normal":
                    yy = np.r_[np.zeros(nrm.sum()), np.ones(msk.sum())]
                    r["auc_vs_normal"] = float(roc_auc_score(yy, np.r_[st[nrm], st[msk]]))
                b = BASE[v]
                r["base"] = b
                r["decision_change_rate"] = float((dec[v][msk] != dec[b][msk]).mean())
                sub.append(r)
        pd.DataFrame(overall).to_csv(fo, index=False)
        pd.DataFrame(sub).to_csv(fs, index=False)
        log(f"{unit}: " + "; ".join(f"{r['variant']} {r['auc']:.4f}/{r['f1_p99']:.4f}" for r in overall) +
            f" | load {os.getloadavg()[0]:.2f}")
    log(f"selesai: {out}")


if __name__ == "__main__":
    main()
