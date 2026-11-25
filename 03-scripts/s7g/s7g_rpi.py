#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7g RPi — trade-off akurasi vs biaya SNN-AE dan Dense-AE di Raspberry Pi 5 (DESIGN_S7G_TRADEOFF.md).
Memakai paket, kernel, dan protokol daya S7f (s7f_rpi.py diimpor, tidak diubah), ditambah:
  - Dense-AE terkuantisasi + cache (DENSE_AQ{b}_{cap}, kernel dense_aq_memo dari s7f_memo.c), simetris dengan SNN;
  - SNN_MEMOV2_{cap}: snn_memo dengan LIF encoder NEON tanpa cabang (s7g_kernels.c), wajib bit-identik.
Fase:
  check    : SNN_MEMO dan SNN_MEMOV2 (cap 12/14/16, cold & val) bit-identik dengan SNN_COUNT; DENSE_AQ deterministik.
  accuracy : AUC, AP, F1@p99(val), recall pada FPR 0,1/0,5/1/5 % untuk SNN, DENSE, DENSE_AQ2, DENSE_AQ3.
  latency  : seluruh grid, urutan capture & acak, --repeats pass, urutan varian diacak.
  power    : FNIRSI untuk --variants (protokol S7f: pendinginan, idle, jendela >= 30 s, restore cache di dalam jendela).
Satu thread, core dipatok. Hasil: 0-revision-results-v2/s7g/.
"""
# ======== END: HEADER ========
import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "s7f"))
import s7f_rpi as F  # noqa: E402

CAPS = [12, 14, 16]
GRID = (["DENSE", "DENSE_ZS"] + [f"DENSE_AQ{b}_{c}" for b in (2, 3) for c in CAPS]
        + [f"DENSE_AQV2{b}_{c}" for b in (2, 3) for c in CAPS] + ["SNN_COUNT"]
        + [f"SNN_MEMO_{c}" for c in CAPS] + [f"SNN_MEMOV2_{c}" for c in CAPS])
FPRS = [0.001, 0.005, 0.01, 0.05]


def log(m):
    F.log("[S7g] " + m)


# ======== START: KERNEL ========
def load_libs():
    s7c, memo = F.load_libs()
    so = HERE / "build" / "s7g_kernels.so"
    so.parent.mkdir(exist_ok=True)
    subprocess.run(["gcc", "-O3", "-mcpu=native", "-shared", "-fPIC", "-o", str(so), str(HERE / "s7g_kernels.c")],
                   check=True)
    g = ctypes.CDLL(str(so))
    g.snn_memo_v2.argtypes = memo.snn_memo.argtypes
    g.snn_memo_v2.restype = ctypes.c_int
    g.dense_aq_memo_v2.argtypes = [F.F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   F.F32P, F.F32P, F.F32P, F.F32P, F.F32P, F.F32P, F.F32P, ctypes.c_int,
                                   F.U32P, F.F32P, ctypes.c_int, F.F32P, F.I64P]
    g.dense_aq_memo_v2.restype = ctypes.c_int
    memo.dense_aq_memo.argtypes = [F.F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   F.F32P, F.F32P, F.F32P, F.F32P, F.F32P, F.F32P, F.F32P, ctypes.c_int,
                                   F.U32P, F.F32P, ctypes.c_int, F.F32P, F.I64P]
    memo.dense_aq_memo.restype = ctypes.c_int
    return s7c, memo, g


def aq_delta(W, Xval, b):
    d = W["Dense_AE"]
    h1 = np.maximum(Xval.astype(np.float64) @ d["We"] + d["be"], 0)
    return np.ascontiguousarray(np.maximum(np.percentile(h1, 99.9, axis=0) / ((1 << b) - 1), 1e-6), np.float32)


def run(libs, v, W, X, err, st, cache=None):
    s7c, memo, g = libs
    p = F.p
    if v in ("DENSE", "DENSE_ZS", "SNN_COUNT"):
        return F.run((s7c, memo), v, W, X, err, st)
    if v.startswith("DENSE_AQ"):
        d = W["Dense_AE"]
        b = int(v[10]) if v.startswith("DENSE_AQV2") else int(v[8])
        fq = g.dense_aq_memo_v2 if v.startswith("DENSE_AQV2") else memo.dense_aq_memo
        rc = fq(p(X), len(X), d["din"], d["L"], d["dout"], p(d["We"]), p(d["be"]), p(d["Wd"]),
                                p(d["bd"]), p(d["Wo"]), p(d["bo"]), p(d[f"delta{b}"]), b, p(cache.keys, F.U32P),
                                p(cache.ys), cache.logcap, p(err), p(st, F.I64P))
    else:
        w = W["SNN_AE"]
        fn = g.snn_memo_v2 if v.startswith("SNN_MEMOV2") else memo.snn_memo
        rc = fn(p(X), len(X), w["din"], w["L"], w["dout"], w["T"], p(w["We"]), p(w["be"]), w["th_e"], w["dk_e"],
                p(w["Wd"]), p(w["bd"]), w["th_d"], w["dk_d"], p(w["Wo"]), p(w["bo"]),
                p(cache.keys, F.U32P), p(cache.ys), cache.logcap, p(err), p(st, F.I64P))
    if rc != 0:
        raise SystemExit(f"{v}: argumen kernel tidak valid")


def make_cache(libs, v, W, Xval, prefill=True):
    if not (v.startswith("DENSE_AQ") or v.startswith("SNN_MEMO")):
        return None
    c = F.Cache(int(v.rsplit("_", 1)[1]), W["SNN_AE"]["dout"])
    if prefill:
        run(libs, v, W, Xval, np.empty(len(Xval), np.float32), np.zeros(5, np.int64), c)
    c.take_snapshot()
    return c


def load_unit(pkg, unit):
    W, S, Xval = F.load_unit(pkg, unit)
    for b in (2, 3):
        W["Dense_AE"][f"delta{b}"] = aq_delta(W, Xval, b)
    return W, S, Xval


def scores(libs, v, W, X, Xval):
    c = make_cache(libs, v, W, Xval)
    e = np.empty(len(X), np.float32)
    run(libs, v, W, X, e, np.zeros(5, np.int64), c)
    return e
# ======== END: KERNEL ========


# ======== START: FASE ========
def phase_check(libs, pkg, units, res, args):
    rows = []
    for u in units:
        W, S, Xval = load_unit(pkg, u)
        X = S["X"][S["order_capture"]].copy()
        ref = np.empty(len(X), np.float32)
        run(libs, "SNN_COUNT", W, X, ref, np.zeros(5, np.int64))
        row = {"unit": u}
        for v in [f"SNN_MEMO_{c}" for c in CAPS] + [f"SNN_MEMOV2_{c}" for c in CAPS]:
            for pf in (False, True):
                c = make_cache(libs, v, W, Xval, prefill=pf)
                e = np.empty(len(X), np.float32)
                run(libs, v, W, X, e, np.zeros(5, np.int64), c)
                row[f"bitid_{v}_{'val' if pf else 'cold'}"] = bool(np.array_equal(e, ref))
        for b in (2, 3):
            a = [scores(libs, f"DENSE_AQ{b}_{c}", W, X, Xval) for c in CAPS]
            a += [scores(libs, f"DENSE_AQV2{b}_{c}", W, X, Xval) for c in CAPS]
            row[f"aq{b}_cap_and_v2_invariant"] = bool(all(np.array_equal(a[0], z) for z in a[1:]))
        row["pass"] = all(v for k, v in row.items() if k != "unit")
        rows.append(row)
        log(f"CHECK {args.dataset} {u}: pass={row['pass']}")
    out = {"dataset": args.dataset, "system": F.sys_info(), "rows": rows, "pass": all(r["pass"] for r in rows)}
    (res / f"check_{args.dataset}.json").write_text(json.dumps(out, indent=2))
    if not out["pass"]:
        raise SystemExit(3)


def det_metrics(s, y, thr):
    pr = s > thr
    tp, fp = int((pr & (y == 1)).sum()), int((pr & (y == 0)).sum())
    fn = int((~pr & (y == 1)).sum())
    fpr, tpr, _ = roc_curve(y, s)
    out = {"auc": float(roc_auc_score(y, s)), "ap": float(average_precision_score(y, s)),
           "f1_p99": 2 * tp / (2 * tp + fp + fn) if tp else 0.0,
           "recall_p99": tp / (tp + fn) if tp + fn else 0.0,
           "fpr_p99": fp / max(int((y == 0).sum()), 1)}
    for a in FPRS:
        out[f"recall_at_fpr_{a}"] = float(np.interp(a, fpr, tpr))
    return out


def phase_accuracy(libs, pkg, units, res, args):
    rows = []
    for u in units:
        W, S, Xval = load_unit(pkg, u)
        X, y = S["X"], S["y"].astype(int)
        for name, v in [("SNN_AE", "SNN_COUNT"), ("DENSE", "DENSE"), ("DENSE_AQ2", "DENSE_AQ2_14"),
                        ("DENSE_AQ3", "DENSE_AQ3_14")]:
            sv, st = scores(libs, v, W, Xval, Xval), scores(libs, v, W, X, Xval)
            rows.append({"dataset": args.dataset, "unit": u, "model": name,
                         **det_metrics(st.astype(np.float64), y, float(np.percentile(sv, 99)))})
    pd.DataFrame(rows).to_csv(res / f"accuracy_{args.dataset}.csv", index=False)
    log(f"ACCURACY {args.dataset}: {len(rows)} baris")


def phase_latency(libs, pkg, units, res, args):
    for u in units:
        jp = res / f"latency_{args.dataset}_{u}.csv"
        if jp.exists():
            log(f"SKIP latency {u}")
            continue
        W, S, Xval = load_unit(pkg, u)
        caches = {v: make_cache(libs, v, W, Xval) for v in GRID}
        rows = []
        for oname in ("capture", "random"):
            Xm = np.ascontiguousarray(S["X"][S[f"order_{oname}"]])
            err, st = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
            for v in GRID:
                if caches[v] is not None:
                    caches[v].restore()
                run(libs, v, W, Xm, err, st, caches[v])
            rng = np.random.RandomState(11)
            t, h = {v: [] for v in GRID}, {v: [] for v in GRID}
            for _ in range(args.repeats):
                for v in rng.permutation(GRID):
                    if caches[v] is not None:
                        caches[v].restore()
                    st[:] = 0
                    t0 = time.perf_counter_ns()
                    run(libs, v, W, Xm, err, st, caches[v])
                    t[v].append((time.perf_counter_ns() - t0) / len(Xm))
                    if caches[v] is not None:
                        h[v].append(st[0] / len(Xm))
            base = float(np.median(t["DENSE_ZS"]))
            for v in GRID:
                rows.append({"dataset": args.dataset, "unit": u, "order": oname, "variant": v, "n": len(Xm),
                             "ns_median": float(np.median(t[v])), "ns_p10": float(np.percentile(t[v], 10)),
                             "ns_p90": float(np.percentile(t[v], 90)), "ratio_vs_dense_zs": float(np.median(t[v])) / base,
                             "hit_rate": float(np.mean(h[v])) if h[v] else np.nan, **F.sys_info()})
            log(f"LATENCY {u} {oname}: ZS={base:.0f} ns | " + " ".join(
                f"{v}={np.median(t[v]) / base:.3f}" for v in GRID if v != "DENSE_ZS"))
        pd.DataFrame(rows).to_csv(jp, index=False)


def phase_power(libs, pkg, units, res, args):
    variants = args.variants.split(",")
    assert all(v in GRID for v in variants), variants
    s7a, base = F.power_modules()
    pdir = res / "power"
    pdir.mkdir(exist_ok=True)
    data = {u: load_unit(pkg, u) for u in units}
    fn = {"r": None, "idle": (base.PBUS_IDLE_DEFAULT, 0.0, 0), "rate": None}

    def start_fnirsi():
        if fn["r"]:
            try:
                fn["r"].stop()
            except Exception:
                pass
        rdr = base.FNIRSIReader(logger_path=args.fnirsi_path)
        rdr.start(); time.sleep(2)
        if not rdr.is_alive():
            raise RuntimeError("fnirsi_logger.py tidak berjalan")
        fn["idle"] = base.measure_idle_power(rdr, duration_sec=args.idle_sec)
        fn["rate"] = fn["idle"][2] / float(args.idle_sec); fn["r"] = rdr
        if fn.get("t_ref") is None:
            fn["t_ref"] = base.get_cpu_temp()

    def one(u, v, oname):
        W, S, Xval = data[u]
        Xm = np.ascontiguousarray(S["X"][S[f"order_{oname}"]])
        c = make_cache(libs, v, W, Xval)
        err, st = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
        for _ in range(5):
            if c is not None:
                c.restore()
            run(libs, v, W, Xm, err, st, c)
        s7a.cooldown_and_idle(fn, args)
        fn["r"].clear_readings()
        lat, t0 = [], time.perf_counter()
        while time.perf_counter() - t0 < args.min_sec:
            t1 = time.perf_counter()
            if c is not None:
                c.restore()                                 # di dalam jendela: ikut terhitung
            run(libs, v, W, Xm, err, st, c)
            lat.append((time.perf_counter() - t1) * 1000.0)
        elapsed = time.perf_counter() - t0
        r = fn["r"].get_readings()
        rate = len(r) / max(elapsed, 1e-9)
        valid = bool(fn["r"].is_alive() and fn["rate"] and rate >= 0.5 * fn["rate"] and len(r) > 0)
        board = base.calc_board_metrics(float(np.mean(r)), float(np.std(r)), len(r), fn["idle"][0], fn["idle"][1],
                                        fn["idle"][2], float(np.mean(lat)), float(np.std(lat)), len(Xm)) if r else None
        return {"power_valid": valid, "passes": len(lat), "elapsed_s": elapsed, "fnirsi_rate_hz": rate,
                "n_per_pass": int(len(Xm)), "latency_us_per_sample_median": float(np.median(lat)) / len(Xm) * 1000.0,
                "board_power_metrics": board, "idle_measurement": {"pbus_idle_w": fn["idle"][0], **(fn.get("cool") or {})}}

    orders = args.orders.split(",")
    try:
        for rnd in range(1, args.rounds + 1):
            conds = [(u, v, o) for u in units for v in variants for o in orders]
            for i in np.random.RandomState(500 + rnd).permutation(len(conds)):
                u, v, o = conds[i]
                jp = pdir / f"r{rnd:02d}_{args.dataset}_{u}_{v}_{o}.json"
                if jp.exists() and json.loads(jp.read_text()).get("power_valid"):
                    continue
                for attempt in range(args.max_retries + 1):
                    if fn["r"] is None or not fn["r"].is_alive():
                        start_fnirsi()
                    pr = one(u, v, o)
                    if pr["power_valid"] or attempt == args.max_retries:
                        break
                    log(f"[RETRY {attempt + 1}] r{rnd} {u} {v} {o}")
                    fn["r"].stop(); fn["r"] = None; time.sleep(5)
                b = pr.pop("board_power_metrics") or {}
                pr.update({"round": rnd, "dataset": args.dataset, "unit": u, "variant": v, "order": o,
                           "system": F.sys_info(),
                           **{k: b.get(k) for k in ["pbus_idle_w", "pbus_inference_w", "p_delta_w",
                                                    "board_energy_delta_mj_per_sample",
                                                    "board_energy_active_mj_per_sample", "throughput_sps"]}})
                jp.write_text(json.dumps(base.sanitize_for_json(pr), indent=2))
                log(f"POWER r{rnd} {u} {v} {o}: {pr['latency_us_per_sample_median']:.3f} us | "
                    f"dE={pr.get('board_energy_delta_mj_per_sample')} mJ | valid={pr['power_valid']}")
    finally:
        if fn["r"]:
            fn["r"].stop()
# ======== END: FASE ========


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["edge_iiotset", "ciciot2023"])
    ap.add_argument("--phase", required=True, choices=["check", "accuracy", "latency", "power"])
    ap.add_argument("--pkg", default=str(HERE.parent / "s7f" / "rpi_package"))
    ap.add_argument("--result", default=str(HERE.parent / "0-revision-results-v2" / "s7g"))
    ap.add_argument("--units", default="s0_f0,s1_f0,s2_f0")
    ap.add_argument("--core", type=int, default=3)
    ap.add_argument("--repeats", type=int, default=15)
    ap.add_argument("--variants", default="DENSE_ZS,SNN_MEMO_14")
    ap.add_argument("--orders", default="capture")
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--min_sec", type=float, default=30.0)
    ap.add_argument("--idle_sec", type=int, default=20)
    ap.add_argument("--cool_margin", type=float, default=2.0)
    ap.add_argument("--cool_timeout", type=int, default=600)
    ap.add_argument("--fnirsi_path", default=str(HERE.parent / "fnirsi_logger.py"))
    ap.add_argument("--max_retries", type=int, default=3)
    args = ap.parse_args()
    os.sched_setaffinity(0, {args.core})
    pkg, res = Path(args.pkg) / args.dataset, Path(args.result)
    res.mkdir(parents=True, exist_ok=True)
    F.verify_package(pkg)
    libs = load_libs()
    units = args.units.split(",")
    log(f"{args.dataset} fase={args.phase} unit={units} {F.sys_info()}")
    {"check": phase_check, "accuracy": phase_accuracy, "latency": phase_latency,
     "power": phase_power}[args.phase](libs, pkg, units, res, args)
    log(f"fase {args.phase} selesai")


if __name__ == "__main__":
    main()
