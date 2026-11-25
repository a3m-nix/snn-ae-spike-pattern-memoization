#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7x-ij (server x86) — konfirmasi n = 30 unit per dataset untuk S7i (jalur miss vektor, v3) dan S7j (kunci cache
kode spike terkuantisasi, RQ). Rancangan: DESIGN.md (dikunci dengan hash sebelum fase accuracy dan timing).

Fase:
  check    : 60 unit, urutan {capture, acak}, isi awal {cold, validation}.
             - snn_memo_v3 bit-identik dengan SNN_COUNT; stats = snn_memo skalar (cap 2^16).
             - dense_aq_memo_v3 (b = 2, 3) bit-identik dengan dense_aq_memo; stats identik (cap 2^16).
             - snn_rq_memo (COUNT, TRI) bit-identik dengan snn_rq_ref (skalar tanpa cache) pada cap 2^16/2^18/2^20,
               sehingga invarian terhadap kapasitas dan isi awal cache; skor berhingga.
             Satu kombinasi gagal = berhenti (exit 2). Tanpa waktu, tanpa metrik deteksi.
  accuracy : SNN_EXACT (SNN_COUNT), SNN_RQC, SNN_RQT per unit: AUC, AP, F1/recall/FPR @p99(val), recall@FPR.
  timing   : DENSE_ZS, DENSE_AQV32_16, DENSE_AQV33_16, SNN_MEMOV3_16, SNN_RQC_16, SNN_RQT_16 (protokol S7x).
Pola kanonik RQ (rq_table) = s7j_rpi.py: pola tersering per neuron per kelas di validation-normal, per unit.
Helper data + lipat BN = 09-rpi-native-int8/s7d_export_q8.py (s3_final_eval.py tidak di-import).
"""
# ======== END: HEADER ========

# ======== START: ARGUMEN + IMPORT ========
import argparse
import ctypes
import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

AP = argparse.ArgumentParser()
AP.add_argument("--dataset", required=True, choices=["edge_iiotset", "ciciot2023"])
AP.add_argument("--phase", required=True, choices=["check", "accuracy", "timing"])
AP.add_argument("--units", default="all")
AP.add_argument("--repeats", type=int, default=30)
AP.add_argument("--core", type=int, default=9)
ARGS = AP.parse_args()
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "09-rpi-native-int8"))
sys.argv = [sys.argv[0], "--dataset", ARGS.dataset]      # argumen untuk modul helper

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

import s7d_export_q8 as E                               # helper: data, lipat BN, SpikingLayer

DS = ARGS.dataset
F32P, I64P, U32P = (ctypes.POINTER(t) for t in (ctypes.c_float, ctypes.c_int64, ctypes.c_uint32))
LOGCAP = 16
RQ_CAPS = [16, 18, 20]
AQ_BITS = [2, 3]
FPRS = [0.001, 0.005, 0.01, 0.05]
CFLAGS = ["gcc", "-O3", "-march=native", "-shared", "-fPIC"]   # = flag S7f/S7x server
VARIANTS = ["DENSE_ZS", "DENSE_AQV32_16", "DENSE_AQV33_16", "SNN_MEMOV3_16", "SNN_RQC_16", "SNN_RQT_16"]
ORDER_SEED, PASS_SEED = 43, 7                           # = S7f / S7x
DEFAULT = {"C": {0: 0, 1: 4, 2: 6, 3: 7}, "T": {0: 0, 1: 4, 2: 6}}   # = s7j_rpi.py


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] [s7x-ij-{ARGS.phase}] {m}", flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
# ======== END: ARGUMEN + IMPORT ========


# ======== START: KOMPILASI ========
def build(src, so):
    subprocess.run(CFLAGS + ["-o", str(so), str(src)], check=True)
    return ctypes.CDLL(str(so))


def load_libs():
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    L = {"s7c": build(HERE / "s7c_native_copy.c", out / "s7c_native_x86.so"),
         "memo": build(HERE / "s7f_memo.c", out / "s7f_memo_x86.so"),
         "v3": build(HERE / "s7x_ij_kernels_x86.c", out / "s7x_ij_kernels_x86.so"),
         "ref": build(HERE / "s7x_ij_ref.c", out / "s7x_ij_ref.so")}
    L["s7c"].dense_ae.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                  F32P, F32P, F32P, F32P, F32P, F32P, ctypes.c_int, F32P, I64P]
    snn_head = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                F32P, F32P, ctypes.c_float, ctypes.c_float, F32P, F32P, ctypes.c_float, ctypes.c_float, F32P, F32P]
    L["s7c"].snn_ae.argtypes = snn_head + [ctypes.c_int, F32P, I64P]
    cache_tail = [U32P, F32P, ctypes.c_int, F32P, I64P]
    aq_t = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            F32P, F32P, F32P, F32P, F32P, F32P, F32P, ctypes.c_int] + cache_tail
    for f, t in [(L["memo"].snn_memo, snn_head + cache_tail), (L["v3"].snn_memo_v3, snn_head + cache_tail),
                 (L["memo"].dense_aq_memo, aq_t), (L["v3"].dense_aq_memo_v3, aq_t),
                 (L["v3"].snn_rq_memo, snn_head + [U32P, ctypes.c_int] + cache_tail),
                 (L["ref"].snn_rq_ref, snn_head + [U32P, ctypes.c_int, F32P, U32P])]:
        f.argtypes, f.restype = t, ctypes.c_int
    return L
# ======== END: KOMPILASI ========


# ======== START: PEMANGGILAN KERNEL ========
def p(a, t=F32P):
    return a.ctypes.data_as(t)


class Cache:
    def __init__(self, logcap, dout):
        self.logcap = logcap
        self.keys = np.zeros((1 << logcap) * 4, dtype=np.uint32)
        self.ys = np.zeros((1 << logcap) * dout, dtype=np.float32)

    def reset(self):
        self.keys[3::4] = 0


def snn_args(w, X):
    return (p(X), len(X), w["din"], w["L"], w["dout"], w["T"], p(w["We"]), p(w["be"]), w["th_e"], w["dk_e"],
            p(w["Wd"]), p(w["bd"]), w["th_d"], w["dk_d"], p(w["Wo"]), p(w["bo"]))


def run(L, kernel, W, X, err, stats, cache=None, arg=None):
    """kernel: DENSE_ZS | SNN_COUNT | snn_memo | snn_memo_v3 | dense_aq_memo | dense_aq_memo_v3 (arg = bits)
               | snn_rq_memo (arg = 'C'/'T')"""
    n = len(X)
    if kernel == "DENSE_ZS":
        d = W["Dense_AE"]
        L["s7c"].dense_ae(p(X), n, d["din"], d["L"], d["dout"], p(d["We"]), p(d["be"]), p(d["Wd"]), p(d["bd"]),
                          p(d["Wo"]), p(d["bo"]), 1, p(err), p(stats, I64P))
        return
    if kernel.startswith("dense_aq_memo"):
        d = W["Dense_AE"]
        f = L["v3"].dense_aq_memo_v3 if kernel.endswith("_v3") else L["memo"].dense_aq_memo
        rc = f(p(X), n, d["din"], d["L"], d["dout"], p(d["We"]), p(d["be"]), p(d["Wd"]), p(d["bd"]),
               p(d["Wo"]), p(d["bo"]), p(d[f"delta{arg}"]), arg,
               p(cache.keys, U32P), p(cache.ys), cache.logcap, p(err), p(stats, I64P))
    elif kernel == "SNN_COUNT":
        L["s7c"].snn_ae(*snn_args(W["SNN_AE"], X), 2, p(err), p(stats, I64P))
        return
    elif kernel == "snn_rq_memo":
        w = W["SNN_AE"]
        rc = L["v3"].snn_rq_memo(*snn_args(w, X), p(w[f"R{arg}"], U32P), 0 if arg == "C" else 1,
                                 p(cache.keys, U32P), p(cache.ys), cache.logcap, p(err), p(stats, I64P))
    else:
        f = L["v3"].snn_memo_v3 if kernel.endswith("_v3") else L["memo"].snn_memo
        rc = f(*snn_args(W["SNN_AE"], X), p(cache.keys, U32P), p(cache.ys), cache.logcap, p(err), p(stats, I64P))
    if rc != 0:
        raise SystemExit(f"{kernel}: argumen tidak valid")


def rq_ref(L, W, X, m):
    w, e = W["SNN_AE"], np.empty(len(X), np.float32)
    keys = np.empty(2 * len(X), np.uint32)
    if L["ref"].snn_rq_ref(*snn_args(w, X), p(w[f"R{m}"], U32P), 0 if m == "C" else 1, p(e), p(keys, U32P)) != 0:
        raise SystemExit("snn_rq_ref: argumen tidak valid")
    return e, keys


VARIANT_KERNEL = {"DENSE_ZS": ("DENSE_ZS", None), "DENSE_AQV32_16": ("dense_aq_memo_v3", 2),
                  "DENSE_AQV33_16": ("dense_aq_memo_v3", 3), "SNN_MEMOV3_16": ("snn_memo_v3", None),
                  "SNN_RQC_16": ("snn_rq_memo", "C"), "SNN_RQT_16": ("snn_rq_memo", "T"),
                  "SNN_EXACT": ("SNN_COUNT", None)}


def prefill(L, kernel, W, Xval, cache, arg=None):
    cache.reset()
    run(L, kernel, W, Xval, np.empty(len(Xval), np.float32), np.zeros(5, np.int64), cache, arg)
# ======== END: PEMANGGILAN KERNEL ========


# ======== START: DATA UNIT ========
def rq_table(w, Xval, m):
    """= s7j_rpi.rq_table. R[k*3+t]: mask neuron yang pola kanoniknya untuk kelas k berisi spike pada time step t."""
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
    n_default = 0
    for j in range(32):
        for k in DEFAULT[m]:
            src = P[c[:, j] == k, j]
            if len(src):
                rep = int(np.bincount(src, minlength=8).argmax())
            else:
                rep, n_default = DEFAULT[m][k], n_default + 1
            for t in range(3):
                if (rep >> t) & 1:
                    R[k * 3 + t] |= np.uint32(1 << j)
    return R, n_default


def unit_setup(X, y, src, unit):
    Xval, Xte, te = E.unit_data(X, y, unit)
    W = {m: E.fold(E.UNITS_DIR / unit / m / "model.keras", m) for m in E.MODELS}
    h1v = np.maximum(Xval.astype(np.float64) @ W["Dense_AE"]["We"] + W["Dense_AE"]["be"], 0)
    for b in AQ_BITS:                                       # bin DENSE_AQ dari validation-normal (= S7f/S7x)
        q = np.percentile(h1v, 99.9, axis=0) / ((1 << b) - 1)
        W["Dense_AE"][f"delta{b}"] = np.ascontiguousarray(np.maximum(q, 1e-6), np.float32)
    ident = {"snn_fp32_sha256": W["SNN_AE"]["fp32_sha256"], "dense_fp32_sha256": W["Dense_AE"]["fp32_sha256"],
             "delta_sha256": hashlib.sha256(b"".join(W["Dense_AE"][f"delta{b}"].tobytes() for b in AQ_BITS)).hexdigest(),
             "n_val": len(Xval), "n_test": len(Xte)}
    for m in "CT":
        R, nd = rq_table(W["SNN_AE"], Xval, m)
        W["SNN_AE"][f"R{m}"] = R
        ident[f"R{m}_hex"] = " ".join(f"{int(r):08x}" for r in R)
        ident[f"R{m}_n_default"] = nd
    orders = {"capture": np.lexsort((src["source_row"][te], src["source_file"][te])),
              "random": np.random.RandomState(ORDER_SEED).permutation(len(te))}
    return Xval, Xte, y[te].astype(int), W, orders, ident
# ======== END: DATA UNIT ========


# ======== START: FASE CHECK ========
def check_unit(L, Xval, Xte, W, orders, ident, unit):
    dout = W["SNN_AE"]["dout"]
    ref, st = np.empty(len(Xte), np.float32), np.zeros(5, np.int64)
    run(L, "SNN_COUNT", W, Xte, ref, st)
    rq = {m: rq_ref(L, W, Xte, m) for m in "CT"}
    rows = []

    def add(oname, mode, cap, variant, reference, ok_err, ok_stats, s, n):
        r = {"dataset": DS, "unit": unit, "order": oname, "prefill": mode, "logcap": cap, "variant": variant,
             "reference": reference, "err_bit_identical": bool(ok_err), "stats_identical": bool(ok_stats),
             "hits": int(s[0]), "misses": int(s[1]), "n": n}
        r.update(ident)
        rows.append(r)

    for oname, idx in orders.items():
        Xm = np.ascontiguousarray(Xte[idx])
        for mode in ("cold", "val"):
            pairs = [("SNN_MEMOV3_16", "snn_memo", "snn_memo_v3", None, ref[idx], "SNN_COUNT (s7c)")]
            pairs += [(f"DENSE_AQV3{b}_16", "dense_aq_memo", "dense_aq_memo_v3", b, None, f"dense_aq_memo b={b} (s7f)")
                      for b in AQ_BITS]
            for variant, k_old, k_new, arg, target, refname in pairs:
                out = {}
                for kern in (k_old, k_new):
                    c = Cache(LOGCAP, dout)
                    if mode == "val":
                        prefill(L, kern, W, Xval, c, arg)
                    e, s = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
                    run(L, kern, W, Xm, e, s, c, arg)
                    out[kern] = (e, s)
                tgt = target if target is not None else out[k_old][0]
                add(oname, mode, LOGCAP, variant, refname, np.array_equal(out[k_new][0], tgt),
                    np.array_equal(out[k_new][1], out[k_old][1]), out[k_new][1], len(Xm))
            for m in "CT":
                for cap in RQ_CAPS:
                    c = Cache(cap, dout)
                    if mode == "val":
                        prefill(L, "snn_rq_memo", W, Xval, c, m)
                    e, s = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
                    run(L, "snn_rq_memo", W, Xm, e, s, c, m)
                    ok = np.array_equal(e, rq[m][0][idx]) and np.isfinite(e).all()
                    add(oname, mode, cap, f"SNN_RQ{m}_{cap}", "snn_rq_ref (skalar, tanpa cache)", ok, True, s, len(Xm))
                    del c
    kc = {m: len(np.unique(rq[m][1].reshape(-1, 2).view(np.uint64))) for m in "CT"}
    for r in rows:
        r["rqc_unique_keys_test"], r["rqt_unique_keys_test"] = kc["C"], kc["T"]
    return rows
# ======== END: FASE CHECK ========


# ======== START: FASE ACCURACY ========
def det_metrics(s, y, thr):                             # = s7g_rpi.det_metrics
    pr = s > thr
    tp, fp = int((pr & (y == 1)).sum()), int((pr & (y == 0)).sum())
    fn = int((~pr & (y == 1)).sum())
    fpr, tpr, _ = roc_curve(y, s)
    out = {"auc": float(roc_auc_score(y, s)), "ap": float(average_precision_score(y, s)),
           "f1_p99": 2 * tp / (2 * tp + fp + fn) if tp else 0.0,
           "recall_p99": tp / (tp + fn) if tp + fn else 0.0,
           "fpr_p99": fp / max(int((y == 0).sum()), 1), "threshold_p99": float(thr)}
    for a in FPRS:
        out[f"recall_at_fpr_{a}"] = float(np.interp(a, fpr, tpr))
    return out


def scores(L, variant, W, X, Xval):                     # = s7g_rpi.scores: cache 2^16 terisi validation
    kern, arg = VARIANT_KERNEL[variant]
    e, s = np.empty(len(X), np.float32), np.zeros(5, np.int64)
    c = None
    if kern != "SNN_COUNT":
        c = Cache(LOGCAP, W["SNN_AE"]["dout"])
        prefill(L, kern, W, Xval, c, arg)
    run(L, kern, W, X, e, s, c, arg)
    return e


def accuracy_unit(L, Xval, Xte, yte, W, ident, unit):
    rows = []
    for name, v in [("SNN_EXACT", "SNN_EXACT"), ("SNN_RQC", "SNN_RQC_16"), ("SNN_RQT", "SNN_RQT_16")]:
        sv, st = scores(L, v, W, Xval, Xval), scores(L, v, W, Xte, Xval)
        rows.append({"dataset": DS, "unit": unit, "model": name,
                     **det_metrics(st.astype(np.float64), yte, float(np.percentile(sv, 99))),
                     "R_hex": ident.get(f"R{name[-1]}_hex", "") if name != "SNN_EXACT" else "",
                     "R_n_default": ident.get(f"R{name[-1]}_n_default", "") if name != "SNN_EXACT" else ""})
    return rows
# ======== END: FASE ACCURACY ========


# ======== START: FASE TIMING ========
def timing_unit(L, Xval, Xte, W, orders, ident, unit):
    dout = W["SNN_AE"]["dout"]
    summ, raw = [], []
    for oname, idx in orders.items():
        Xm = np.ascontiguousarray(Xte[idx])
        caches = {v: Cache(LOGCAP, dout) for v in VARIANTS if v != "DENSE_ZS"}
        err, st = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
        for v in VARIANTS:                                  # warm-up (tidak dicatat)
            kern, arg = VARIANT_KERNEL[v]
            c = caches.get(v)
            if c is not None:
                prefill(L, kern, W, Xval, c, arg)
            run(L, kern, W, Xm, err, st, c, arg)
        rng = np.random.RandomState(PASS_SEED)
        times, hits = {v: [] for v in VARIANTS}, {v: [] for v in VARIANTS}
        for rep in range(ARGS.repeats):
            for pos, v in enumerate(rng.permutation(VARIANTS)):
                kern, arg = VARIANT_KERNEL[v]
                c = caches.get(v)
                if c is not None:
                    prefill(L, kern, W, Xval, c, arg)       # di luar waktu terukur
                st[:] = 0
                t0 = time.perf_counter_ns()
                run(L, kern, W, Xm, err, st, c, arg)
                ns = (time.perf_counter_ns() - t0) / len(Xm)
                times[v].append(ns)
                hr = st[0] / len(Xm) if c is not None else np.nan
                hits[v].append(hr)
                raw.append({"dataset": DS, "unit": unit, "order": oname, "pass": rep, "pos_in_pass": pos,
                            "variant": v, "ns_per_sample": ns, "hit_rate": hr})
        for v in VARIANTS:
            summ.append({"dataset": DS, "unit": unit, "order": oname, "variant": v, "n": len(Xm),
                         "ns_per_sample_median": float(np.median(times[v])),
                         "ns_per_sample_p10": float(np.percentile(times[v], 10)),
                         "ns_per_sample_p90": float(np.percentile(times[v], 90)),
                         "hit_rate": float(np.mean(hits[v])) if v != "DENSE_ZS" else np.nan,
                         "loadavg_1m": os.getloadavg()[0],
                         **{k: ident[k] for k in ("snn_fp32_sha256", "dense_fp32_sha256", "delta_sha256", "n_test")}})
        base = np.median(times["DENSE_ZS"])
        log(f"{unit} {oname}: DENSE_ZS={base:.0f} ns | " + " | ".join(
            f"{v} x{np.median(times[v]) / base:.3f}" for v in VARIANTS[1:]) + f" | load {os.getloadavg()[0]:.2f}")
    return summ, raw
# ======== END: FASE TIMING ========


# ======== START: MAIN ========
def guard_locked():
    want = (HERE / "logs" / "design_sha256.txt").read_text().split()[0]
    if sha(HERE / "DESIGN.md") != want:
        raise SystemExit("DESIGN.md tidak cocok dengan logs/design_sha256.txt — dibatalkan")
    for ds in ("edge_iiotset", "ciciot2023"):
        fs = sorted((HERE / "results" / "check" / ds).glob("*_check.csv"))
        if len(fs) != 30:
            raise SystemExit(f"check {ds}: {len(fs)} berkas, bukan 30 — dibatalkan")
        c = pd.concat([pd.read_csv(f) for f in fs])
        if not (c.err_bit_identical.all() and c.stats_identical.all()):
            raise SystemExit(f"check {ds}: ada yang gagal — dibatalkan")
    log(f"guard OK: DESIGN.md sha {want[:12]}…, check 60/60 lolos")


def main():
    os.sched_setaffinity(0, {ARGS.core})
    if ARGS.phase != "check":
        guard_locked()
    L = load_libs()
    log(f"core {ARGS.core} | nice {os.nice(0)} | kernel sha {sha(HERE / 's7x_ij_kernels_x86.c')[:12]}… | "
        f"load {os.getloadavg()}")
    X, y, _ = E.load_all()
    t = pq.read_table(E.S1 / "sample.parquet", columns=["source_file", "source_row"]).to_pandas()
    src = {"source_file": t.source_file.values, "source_row": t.source_row.values}
    del t
    units = sorted(u.name for u in E.UNITS_DIR.iterdir() if u.is_dir() and u.name.startswith("s"))
    if ARGS.units != "all":
        units = ARGS.units.split(",")
    elif len(units) != 30:
        raise SystemExit(f"jumlah unit {len(units)} != 30")
    out = HERE / "results" / ARGS.phase / DS
    out.mkdir(parents=True, exist_ok=True)
    for unit in units:
        f = out / f"{unit}_{ARGS.phase}.csv"
        if f.exists():
            log(f"{unit}: checkpoint ada, dilewati")
            continue
        Xval, Xte, yte, W, orders, ident = unit_setup(X, y, src, unit)
        if ARGS.phase == "check":
            df = pd.DataFrame(check_unit(L, Xval, Xte, W, orders, ident, unit))
            ok = bool(df.err_bit_identical.all() and df.stats_identical.all())
            df.to_csv(f if ok else out / f"{unit}_check_FAILED.csv", index=False)
            log(f"{unit}: check {'LOLOS' if ok else 'GAGAL'} ({len(df)} kombinasi; kunci unik RQC "
                f"{df.rqc_unique_keys_test.iloc[0]}, RQT {df.rqt_unique_keys_test.iloc[0]})")
            if not ok:
                print(df.loc[~(df.err_bit_identical & df.stats_identical),
                             ["order", "prefill", "logcap", "variant", "err_bit_identical", "stats_identical"]].to_string(),
                      flush=True)
                sys.exit(2)
        elif ARGS.phase == "accuracy":
            rows = accuracy_unit(L, Xval, Xte, yte, W, ident, unit)
            pd.DataFrame(rows).to_csv(f, index=False)
            log(f"{unit}: " + "; ".join(f"{r['model']} {r['auc']:.4f}/{r['f1_p99']:.4f}" for r in rows))
        else:
            summ, raw = timing_unit(L, Xval, Xte, W, orders, ident, unit)
            pd.DataFrame(raw).to_csv(out / f"{unit}_raw.csv", index=False)
            pd.DataFrame(summ).to_csv(f, index=False)
    log(f"selesai: {out}")


if __name__ == "__main__":
    main()
# ======== END: MAIN ========
