#!/usr/bin/env python3
"""
S7t (server nixfsv2, x86) — exact memoization at T = 2, 3, 5, 7 (DESIGN_S7T.md).
Models: v8.3.1 fair-benchmark pipeline (fold_models/<ds>/{SNN_AE, SNN_AE_T2, SNN_AE_T5, SNN_AE_T7, Dense_AE}).
Data: reproduced with the v8.3.1 procedure (balanced sampling, holdout split, stored CV folds, MinMaxScaler on the
train-normal part, validation-normal split); the label vector is checked against the stored y_hash (G0).
Weights are folded with s7d_export_q8.fold (SpikingLayer via AST; no training script is imported or run).
Per unit and T: G1 (native AUC vs main_results_raw), G2 (memo bit-identical to the cache-free SNN-AE, cold/prefill,
capture/random order), pattern statistics, and interleaved timing of SNN_NOCACHE, SNN_MEMO and DENSE_ZS.
Usage: python s7t_server.py --dataset <ds> [--units s0_f0,...] [--repeats 15] [--core 9] [--out results]
"""
import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

AP = argparse.ArgumentParser()
AP.add_argument("--dataset", required=True, choices=["edge_iiotset", "ciciot2023"])
AP.add_argument("--units", default="all")
AP.add_argument("--repeats", type=int, default=15)
AP.add_argument("--core", type=int, default=9)
AP.add_argument("--out", default="results")
ARGS = AP.parse_args()
HERE = Path(__file__).resolve().parent
ROOT = Path("/home/jupyteruser/nix-ext-backup/0-eksperimen-final")
V83 = ROOT / "0-snn-ae-unified-v8-3-fair-benchmark"
sys.path.insert(0, str(ROOT / "0-snn-ae-revision" / "09-rpi-native-int8"))
sys.argv = [sys.argv[0], "--dataset", ARGS.dataset]

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402
from sklearn.metrics import roc_auc_score              # noqa: E402
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer  # noqa: E402

import s7d_export_q8 as E                              # noqa: E402  (fold, SpikingLayer via AST)

DS = ARGS.dataset
CFG = json.loads((V83 / "metadata" / "config_v8_3_fair_benchmark.json").read_text())
TS = [2, 3, 5, 7]
MODEL_OF = {2: "SNN_AE_T2", 3: "SNN_AE", 5: "SNN_AE_T5", 7: "SNN_AE_T7"}
LOGCAP, KW = 16, 9
ORDER_SEED, PASS_SEED = 43, 7                          # = S7x-ij
F32P, I64P, U32P = (ctypes.POINTER(t) for t in (ctypes.c_float, ctypes.c_int64, ctypes.c_uint32))
OUT = HERE / ARGS.out / DS


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] [s7t {DS}] {m}", flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def p(a, t=F32P):
    return a.ctypes.data_as(t)


# ------------------------------------------------------------------ kernels
def load_libs():
    b = HERE / "build"
    b.mkdir(exist_ok=True)
    libs = {}
    for name, src in [("s7c", "s7c_native_copy.c"), ("t", "s7t_kernels_x86.c")]:
        so = b / (Path(src).stem + "_x86.so")
        subprocess.run(["gcc", "-O3", "-march=native", "-shared", "-fPIC", "-o", str(so), str(HERE / src)], check=True)
        libs[name] = ctypes.CDLL(str(so))
    head = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            F32P, F32P, ctypes.c_float, ctypes.c_float, F32P, F32P, ctypes.c_float, ctypes.c_float, F32P, F32P]
    libs["s7c"].snn_ae.argtypes = head + [ctypes.c_int, F32P, I64P]
    libs["s7c"].dense_ae.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                     F32P, F32P, F32P, F32P, F32P, F32P, ctypes.c_int, F32P, I64P]
    libs["t"].snn_memo_t.argtypes = head + [U32P, F32P, ctypes.c_int, F32P, I64P]
    libs["t"].snn_memo_t.restype = ctypes.c_int
    libs["t"].snn_keys_t.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, F32P, F32P,
                                     ctypes.c_float, ctypes.c_float, U32P, I64P]
    libs["t"].snn_keys_t.restype = ctypes.c_int
    return libs


class Cache:
    def __init__(self, dout):
        self.keys = np.zeros((1 << LOGCAP) * KW, np.uint32)
        self.ys = np.zeros((1 << LOGCAP) * dout, np.float32)

    def reset(self):
        self.keys[KW - 1::KW] = 0


def snn_args(w, X):
    return (p(X), len(X), w["din"], w["L"], w["dout"], w["T"], p(w["We"]), p(w["be"]), w["th_e"], w["dk_e"],
            p(w["Wd"]), p(w["bd"]), w["th_d"], w["dk_d"], p(w["Wo"]), p(w["bo"]))


def run(L, v, w, X, err, st, cache=None):
    if v == "DENSE_ZS":
        L["s7c"].dense_ae(p(X), len(X), w["din"], w["L"], w["dout"], p(w["We"]), p(w["be"]), p(w["Wd"]), p(w["bd"]),
                          p(w["Wo"]), p(w["bo"]), 1, p(err), p(st, I64P))
    elif v == "SNN_NOCACHE":
        L["s7c"].snn_ae(*snn_args(w, X), 2, p(err), p(st, I64P))
    else:
        if L["t"].snn_memo_t(*snn_args(w, X), p(cache.keys, U32P), p(cache.ys), LOGCAP, p(err), p(st, I64P)) != 0:
            raise SystemExit("snn_memo_t: invalid arguments")


def scores(L, v, w, X, Xval=None, cache=None):
    e, st = np.empty(len(X), np.float32), np.zeros(5, np.int64)
    if cache is not None:
        cache.reset()
        if Xval is not None:
            run(L, v, w, Xval, np.empty(len(Xval), np.float32), np.zeros(5, np.int64), cache)
    run(L, v, w, X, e, st, cache)
    return e, st


# ------------------------------------------------------------------ data (v8.3.1 procedure)
def load_balanced():
    """= load_balanced_data() of the v8.3.1 canonical script, plus the capture timestamp of each sample."""
    label_col, normal_cls = CFG["label_column"][DS], CFG["normal_class"][DS]
    df = pd.read_parquet(CFG["data_path"][DS])
    if "label_type" not in df.columns:
        df["label_type"] = df[label_col].astype(str)
    df_n, df_a = df[df[label_col] == normal_cls], df[df[label_col] != normal_cls]
    rng = np.random.RandomState(CFG["random_state"])
    parts = []
    for subtype in sorted(df_a["label_type"].astype(str).unique()):
        sub = df_a[df_a["label_type"].astype(str) == subtype]
        parts.append(sub.loc[rng.choice(sub.index, size=min(CFG["cap_per_subtype"], len(sub)), replace=False)])
    df_a_bal = pd.concat(parts, axis=0)
    df_n_bal = df_n.loc[rng.choice(df_n.index, size=min(len(df_a_bal), len(df_n)), replace=False)]
    comb = pd.concat([df_n_bal, df_a_bal], axis=0).sample(frac=1.0, random_state=CFG["random_state"]).reset_index(drop=True)
    y = (comb[label_col] != normal_cls).astype(int).values
    t_epoch = comb["frame.time_epoch"].astype(np.float64).values
    Xdf = comb.drop(columns=[c for c in CFG["drop_features"][DS] if c in comb.columns],
                    errors="ignore").select_dtypes(include=np.number)
    X = Xdf.replace([np.inf, -np.inf], np.nan).fillna(0).values.astype(np.float32)
    return X, y, t_epoch, list(Xdf.columns)


def train_val_split(y_tv, seed_idx, fold):              # = make_train_val_normal_split (v8.3.1)
    normal_local = np.where(y_tv == 0)[0]
    rng = np.random.RandomState(CFG["random_state"] + 1000 * seed_idx + fold)
    rng.shuffle(normal_local)
    split = int((1.0 - CFG["val_ratio"]) * len(normal_local))
    return normal_local[:split], normal_local[split:]


def make_scaler():
    """Scaler of the trained v8-3 fold models. G0 finding (18 Nov): the Edge-IIoTset models were trained with the
    QuantileTransformer of the v8-3 code (TF AUC and validation error reproduced exactly), although the stored
    config_v8_3_fair_benchmark.json says minmax; CICIoT2023 uses MinMaxScaler. G1 checks every unit."""
    if DS == "edge_iiotset":
        return QuantileTransformer(n_quantiles=1000, output_distribution="normal", random_state=CFG["random_state"],
                                   subsample=200000)
    return MinMaxScaler()


def det(s, y, thr):
    pr = s > thr
    tp, fp, fn = int((pr & (y == 1)).sum()), int((pr & (y == 0)).sum()), int((~pr & (y == 1)).sum())
    return {"auc": float(roc_auc_score(y, s)), "f1_p99": 2 * tp / (2 * tp + fp + fn) if tp else 0.0,
            "recall_p99": tp / (tp + fn) if tp + fn else 0.0, "fpr_p99": fp / max(int((y == 0).sum()), 1)}


# ------------------------------------------------------------------ main
def main():
    os.sched_setaffinity(0, {ARGS.core})
    L = load_libs()
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"kernel_sha256": sha(HERE / "s7t_kernels_x86.c"), "s7c_sha256": sha(HERE / "s7c_native_copy.c"),
            "script_sha256": sha(Path(__file__)), "nice": os.nice(0), "core": ARGS.core, "repeats": ARGS.repeats}
    log(f"start {meta} | load {os.getloadavg()}")
    X, y, t_epoch, cols = load_balanced()
    summ = json.loads((V83 / "metadata" / f"{DS}_dataset_summary.json").read_text())
    hz = np.load(V83 / "splits" / f"{DS}_holdout_eval_split.npz")
    g0 = {"n": int(len(y)), "n_expected": int(summ["balanced_total_samples"]),
          "features_equal": cols == summ["feature_columns"],
          "y_hash_equal": hashlib.sha256(np.ascontiguousarray(y).view(np.uint8)).hexdigest() == str(hz["y_hash"])}
    log(f"G0 data: {g0}")
    (OUT / "g0_data.json").write_text(json.dumps({**g0, **meta}, indent=1))
    if not (g0["features_equal"] and g0["y_hash_equal"] and g0["n"] == g0["n_expected"]):
        raise SystemExit("G0 failed: data reproduction differs from v8.3.1")
    eval_idx = hz["eval_idx"]
    Xe, ye, te_epoch = X[eval_idx], y[eval_idx], t_epoch[eval_idx]
    del X
    ref = pd.read_csv(V83 / "raw" / "main_results_raw.csv")
    ref = ref[ref.dataset == DS].set_index(["seed_idx", "fold", "job_id"])
    units = [f"s{s}_f{f}" for s in range(3) for f in range(10)] if ARGS.units == "all" else ARGS.units.split(",")
    for unit in units:
        s_idx, f_idx = int(unit[1]), int(unit.split("_f")[1])
        fo = OUT / f"{unit}_timing.csv"
        if fo.exists():
            log(f"{unit}: checkpoint exists, skipped")
            continue
        z = np.load(V83 / "splits" / f"{DS}_cv_seed{s_idx}_fold_indices.npz")
        tv, te = z[f"fold{f_idx}_trainval"], z[f"fold{f_idx}_test"]
        tr_l, va_l = train_val_split(ye[tv], s_idx, f_idx)
        sc = make_scaler().fit(Xe[tv][tr_l])
        Xval = np.ascontiguousarray(sc.transform(Xe[tv][va_l]).astype(np.float32))
        Xte = np.ascontiguousarray(sc.transform(Xe[te]).astype(np.float32))
        yte = ye[te].astype(int)
        cap = np.argsort(te_epoch[te], kind="stable")
        rnd = np.random.RandomState(ORDER_SEED).permutation(len(te))
        Xc, yc = np.ascontiguousarray(Xte[cap]), yte[cap]
        md = V83 / "fold_models" / DS
        Wd_ = E.fold(md / "Dense_AE" / f"seed{s_idx}_fold{f_idx}.keras", "Dense_AE")
        g1, g2, pat, tim = [], [], [], []
        # Dense-AE G1
        ev, _ = scores(L, "DENSE_ZS", Wd_, Xval)
        et, _ = scores(L, "DENSE_ZS", Wd_, Xte)
        m = det(et.astype(np.float64), yte, float(np.percentile(ev, 99)))
        r0 = ref.loc[(s_idx, f_idx, "Dense_AE")]
        g1.append({"unit": unit, "model": "Dense_AE", "T": 0, **m, "auc_ref": float(r0["auc"]),
                   "dAUC": m["auc"] - float(r0["auc"])})
        W = {}
        for T in TS:
            w = E.fold(md / MODEL_OF[T] / f"seed{s_idx}_fold{f_idx}.keras", "SNN_AE")
            if w["T"] != T:
                raise SystemExit(f"{unit} {MODEL_OF[T]}: T = {w['T']} in the model")
            W[T] = w
            ev, _ = scores(L, "SNN_NOCACHE", w, Xval)
            et, _ = scores(L, "SNN_NOCACHE", w, Xte)
            m = det(et.astype(np.float64), yte, float(np.percentile(ev, 99)))
            r0 = ref.loc[(s_idx, f_idx, MODEL_OF[T])]
            g1.append({"unit": unit, "model": MODEL_OF[T], "T": T, **m, "auc_ref": float(r0["auc"]),
                       "dAUC": m["auc"] - float(r0["auc"]), "th_e": w["th_e"], "dk_e": w["dk_e"],
                       "fp32_sha256": w["fp32_sha256"]})
            # G2: memo bit-identical to the cache-free SNN-AE
            for oname, idx in (("capture", cap), ("random", rnd)):
                Xo = np.ascontiguousarray(Xte[idx])
                e0, _ = scores(L, "SNN_NOCACHE", w, Xo)
                for pre in (False, True):
                    e1, _ = scores(L, "SNN_MEMO", w, Xo, Xval if pre else None, Cache(w["dout"]))
                    g2.append({"unit": unit, "T": T, "order": oname, "prefill": pre,
                               "bit_identical": bool(np.array_equal(e0, e1))})
            if not all(r["bit_identical"] for r in g2 if r["T"] == T):
                pd.DataFrame(g2).to_csv(OUT / f"{unit}_g2.csv", index=False)
                raise SystemExit(f"G2 failed: {unit} T={T}")
            # pattern statistics (capture order)
            kv, kt = np.empty(len(Xval) * T, np.uint32), np.empty(len(Xc) * T, np.uint32)
            sv, stt = np.zeros(1, np.int64), np.zeros(1, np.int64)
            L["t"].snn_keys_t(p(Xval), len(Xval), w["din"], w["L"], T, p(w["We"]), p(w["be"]), w["th_e"], w["dk_e"],
                              p(kv, U32P), p(sv, I64P))
            L["t"].snn_keys_t(p(Xc), len(Xc), w["din"], w["L"], T, p(w["We"]), p(w["be"]), w["th_e"], w["dk_e"],
                              p(kt, U32P), p(stt, I64P))
            kv2 = {r.tobytes() for r in kv.reshape(-1, T)}
            ktr = kt.reshape(-1, T)
            seen = np.fromiter((r.tobytes() in kv2 for r in ktr), bool, len(ktr))
            uniq, cnt = np.unique(ktr, axis=0, return_counts=True)
            top = np.sort(cnt)[::-1]
            pat.append({"unit": unit, "T": T, "n_test": len(ktr), "unique_test": int(len(uniq)),
                        "unique_val": int(len(kv2)), "seen_in_val": float(seen.mean()),
                        "top1000_coverage": float(top[:1000].sum() / len(ktr)),
                        "spikes_per_sample": float(stt[0] / len(ktr)), "spikes_possible": 32 * T,
                        "cache_mb": (1 << LOGCAP) * (4 * KW + 4 * w["dout"]) / 1e6})
        # timing: capture order, cache prefilled with validation-normal outside the timed region
        variants = ["DENSE_ZS"] + [f"{v}_T{T}" for T in TS for v in ("SNN_NOCACHE", "SNN_MEMO")]
        caches = {T: Cache(W[T]["dout"]) for T in TS}
        err, st = np.empty(len(Xc), np.float32), np.zeros(5, np.int64)

        def go(v):
            if v == "DENSE_ZS":
                return run(L, "DENSE_ZS", Wd_, Xc, err, st)
            kind, T = v.rsplit("_T", 1)
            T = int(T)
            c = caches[T] if kind == "SNN_MEMO" else None
            if c is not None:
                c.reset()
                run(L, "SNN_MEMO", W[T], Xval, np.empty(len(Xval), np.float32), np.zeros(5, np.int64), c)
            st[:] = 0
            t0 = time.perf_counter_ns()
            run(L, kind, W[T], Xc, err, st, c)
            return (time.perf_counter_ns() - t0) / len(Xc)

        for v in variants:                              # warm-up
            go(v)
        rng = np.random.RandomState(PASS_SEED)
        times = {v: [] for v in variants}
        hits = {v: [] for v in variants}
        for rep in range(ARGS.repeats):
            for v in rng.permutation(variants):
                if v == "DENSE_ZS":
                    st[:] = 0
                    t0 = time.perf_counter_ns()
                    run(L, "DENSE_ZS", Wd_, Xc, err, st)
                    ns = (time.perf_counter_ns() - t0) / len(Xc)
                else:
                    ns = go(v)
                times[v].append(ns)
                hits[v].append(st[0] / len(Xc) if v.startswith("SNN_MEMO") else np.nan)
        base = float(np.median(times["DENSE_ZS"]))
        for v in variants:
            T = int(v.rsplit("_T", 1)[1]) if "_T" in v else 0
            tim.append({"unit": unit, "variant": v.rsplit("_T", 1)[0] if T else v, "T": T, "n": len(Xc),
                        "ns_median": float(np.median(times[v])), "ns_p10": float(np.percentile(times[v], 10)),
                        "ns_p90": float(np.percentile(times[v], 90)), "ratio_vs_dense_zs": float(np.median(times[v])) / base,
                        "hit_rate": float(np.nanmean(hits[v])) if v.startswith("SNN_MEMO") else np.nan,
                        "loadavg_1m": os.getloadavg()[0]})
        pd.DataFrame(g1).to_csv(OUT / f"{unit}_g1.csv", index=False)
        pd.DataFrame(g2).to_csv(OUT / f"{unit}_g2.csv", index=False)
        pd.DataFrame(pat).to_csv(OUT / f"{unit}_patterns.csv", index=False)
        pd.DataFrame(tim).to_csv(fo, index=False)
        log(f"{unit}: dAUC max {max(abs(r['dAUC']) for r in g1):.2e} | G2 ok | " + " | ".join(
            f"T{r['T']} memo x{r['ratio_vs_dense_zs']:.3f} hit {r['hit_rate']:.3f}" for r in tim if r["variant"] == "SNN_MEMO")
            + f" | load {os.getloadavg()[0]:.2f}")
    log(f"done: {OUT}")


if __name__ == "__main__":
    main()
