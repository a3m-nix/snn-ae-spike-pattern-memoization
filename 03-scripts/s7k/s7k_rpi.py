#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7k RPi — mekanisme reuse (K2), penghitung CPU (K3), dan memori (K4). Rancangan: DESIGN_S7K.md.
Memakai tumpukan s7j_rpi -> s7i_rpi -> s7g_rpi -> s7f_rpi apa adanya (kernel, cache, prefill validation, PMU).
Fase:
  check : G2 (total spike dan hit rate simulasi dari kunci = statistik kernel) dan G3 (skor dengan PMU = tanpa PMU).
  k2    : pola kunci (unik, sudah muncul di validation, cakupan top-k, spike per sampel) untuk 3 unit;
          hit rate, waktu, dan statistik kernel per kelas trafik untuk s0_f0 (label dari test_raw.parquet).
  k3    : PMU (cycles, instructions, L1D access/refill, mem access) per varian, 3 unit, urutan capture.
  k4    : RSS proses per kapasitas cache (s0_f0) dan hit rate/waktu untuk kapasitas 2^12, 2^14, 2^16 (3 unit).
"""
# ======== END: HEADER ========
import argparse
import ctypes
import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
HOME = HERE.parent
sys.path.insert(0, str(HOME / "s7j"))
import s7j_rpi as J  # noqa: E402  (mengganti G.run/G.load_unit/G.make_cache dengan versi S7j)

G, F = J.G, J.F
V8 = ["DENSE", "DENSE_ZS", "SNN_COUNT", "DENSE_AQV32_16", "DENSE_AQV33_16", "SNN_MEMOV3_16", "SNN_RQC_16",
      "SNN_RQT_16"]
CACHED = [v for v in V8 if v.startswith(("DENSE_AQ", "SNN_MEMO", "SNN_RQ"))]
PMU_NAMES = ["cycles", "instructions", "l1d_access", "l1d_refill", "mem_access"]
TOPK = [10, 100, 1000]
STAT_NAMES = ["hit", "miss", "spikes_enc", "wd_rows", "wo_rows"]


def log(m):
    F.log("[S7k] " + m)


# ======== START: KUNCI ========
def load_keys_lib():
    so = HERE / "build" / "s7k_keys.so"
    so.parent.mkdir(exist_ok=True)
    subprocess.run(["gcc", "-O3", "-mcpu=native", "-shared", "-fPIC", "-o", str(so), str(HERE / "s7k_keys.c")],
                   check=True)
    k = ctypes.CDLL(str(so))
    k.snn_keys.argtypes = [F.F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, F.F32P, F.F32P,
                           ctypes.c_float, ctypes.c_float, F.U32P]
    k.snn_keys.restype = ctypes.c_int
    return k


def masks_of(K, W, X):
    w = W["SNN_AE"]
    m = np.empty(len(X) * 3, np.uint32)
    if K.snn_keys(F.p(X), len(X), w["din"], w["L"], w["T"], F.p(w["We"]), F.p(w["be"]), w["th_e"], w["dk_e"],
                  F.p(m, F.U32P)) != 0:
        raise SystemExit("snn_keys: argumen tidak valid")
    return m.reshape(-1, 3)


def keys_of(m, mode):
    """mode: E (eksak: 3 mask), C (COUNT: lo, hi), T (TRI: lo&~hi, hi). Rumus = s7j_kernels.c."""
    if mode == "E":
        return m.copy()
    lo = m[:, 0] ^ m[:, 1] ^ m[:, 2]
    hi = (m[:, 0] & m[:, 1]) | (m[:, 0] & m[:, 2]) | (m[:, 1] & m[:, 2])
    k0 = lo if mode == "C" else (lo & ~hi)
    return np.stack([k0, hi, np.zeros_like(hi)], axis=1).astype(np.uint32)


def slots_of(k, logcap):                                     # = slot_of() di s7f_memo.c (aritmetika uint32)
    with np.errstate(over="ignore"):
        h = (k[:, 0] * np.uint32(0x9E3779B1)) ^ (k[:, 1] * np.uint32(0x85EBCA77)) ^ (k[:, 2] * np.uint32(0xC2B2AE3D))
        h ^= h >> np.uint32(15)
        h = h * np.uint32(0x2C1B3C6D)
        h ^= h >> np.uint32(12)
    return (h >> np.uint32(32 - logcap)).astype(np.int64)


def simulate_hits(kval, ktest, logcap):
    """Cache direct-mapped: isi dengan validation, lalu hitung hit pada test (= semantik kernel)."""
    tab = {}
    for sl, kk in zip(slots_of(kval, logcap).tolist(), map(tuple, kval.tolist())):
        tab[sl] = kk
    hits = 0
    for sl, kk in zip(slots_of(ktest, logcap).tolist(), map(tuple, ktest.tolist())):
        if tab.get(sl) == kk:
            hits += 1
        else:
            tab[sl] = kk
    return hits
# ======== END: KUNCI ========


def stream(S):
    return np.ascontiguousarray(S["X"][S["order_capture"]])


def run_stats(libs, v, W, X, cache):
    err, st = np.empty(len(X), np.float32), np.zeros(5, np.int64)
    if cache is not None:
        cache.restore()
    G.run(libs, v, W, X, err, st, cache)
    return err, st


def rss_kb():
    for ln in Path("/proc/self/status").read_text().splitlines():
        if ln.startswith("VmRSS:"):
            return int(ln.split()[1])
    return -1


# ======== START: FASE ========
def phase_check(libs, K, pkg, units, res, args):
    rows = []
    pmu_mask = libs[0].pmu_open()
    for u in units:
        W, S, Xval = G.load_unit(pkg, u)
        X = stream(S)
        mv, mt = masks_of(K, W, Xval), masks_of(K, W, X)
        row = {"dataset": args.dataset, "unit": u, "n_test": len(X)}
        caches = {v: G.make_cache(libs, v, W, Xval) for v in CACHED}
        for v, mode in [("SNN_MEMOV3_16", "E"), ("SNN_RQC_16", "C"), ("SNN_RQT_16", "T")]:
            _, st = run_stats(libs, v, W, X, caches[v])
            sim = simulate_hits(keys_of(mv, mode), keys_of(mt, mode), 16)
            spk = int(np.unpackbits(mt.view(np.uint8)).sum())
            row[f"G2_{v}_spikes_equal"] = bool(st[2] == spk)
            row[f"G2_{v}_hits_equal"] = bool(st[0] == sim)
            row[f"{v}_hits_kernel"], row[f"{v}_hits_sim"] = int(st[0]), int(sim)
        for v in V8:
            e0, _ = run_stats(libs, v, W, X, caches.get(v))
            if caches.get(v) is not None:
                caches[v].restore()
            e1, st = np.empty(len(X), np.float32), np.zeros(5, np.int64)
            c = np.zeros(5, np.int64)
            libs[0].pmu_begin()
            G.run(libs, v, W, X, e1, st, caches.get(v))
            libs[0].pmu_end(c.ctypes.data_as(F.I64P))
            row[f"G3_{v}_bitid_with_pmu"] = bool(np.array_equal(e0, e1))
        row["pass"] = all(val for kk, val in row.items() if kk.startswith(("G2_", "G3_")))
        rows.append(row)
        log(f"CHECK {args.dataset} {u}: pass={row['pass']} | " +
            " ".join(f"{k}={v}" for k, v in row.items() if k.endswith(("_kernel", "_sim"))))
    out = {"dataset": args.dataset, "system": F.sys_info(), "pmu_mask": pmu_mask,
           "pmu_available": [k for i, k in enumerate(PMU_NAMES) if pmu_mask >> i & 1], "rows": rows,
           "pass": all(r["pass"] for r in rows)}
    (res / f"check_{args.dataset}.json").write_text(json.dumps(out, indent=2))
    if not out["pass"]:
        raise SystemExit(3)


def labels_s0f0(dataset, S):
    import pyarrow.parquet as pq
    t = pq.read_table(HOME / "0-revision-payload" / dataset / "test_raw.parquet",
                      columns=["sample_id", "label_type"]).to_pandas().set_index("sample_id")
    lab = t.loc[S["sample_ids"], "label_type"].to_numpy()
    if not np.array_equal(lab != "normal", S["y"].astype(bool)):
        raise SystemExit("label_type tidak konsisten dengan y")
    return lab


def key_metrics(kv, kt):
    uv = {tuple(r) for r in kv.tolist()}
    tt = [tuple(r) for r in kt.tolist()]
    cnt = pd.Series(tt).value_counts()
    out = {"unique_val": len(uv), "unique_test": int(len(cnt)), "test_seen_in_val": float(np.mean([t in uv for t in tt]))}
    for k in TOPK:
        out[f"top{k}_coverage"] = float(cnt.iloc[:k].sum() / len(tt))
    return out


def phase_k2(libs, K, pkg, units, res, args):
    rows, crow = [], []
    for u in units:
        W, S, Xval = G.load_unit(pkg, u)
        X = stream(S)
        mv, mt = masks_of(K, W, Xval), masks_of(K, W, X)
        spk = np.unpackbits(mt.view(np.uint8), axis=1).sum(axis=1)
        for mode, name in [("E", "exact"), ("C", "count"), ("T", "tri")]:
            rows.append({"dataset": args.dataset, "unit": u, "key": name, "n_val": len(Xval), "n_test": len(X),
                         "spikes_per_sample_mean": float(spk.mean()), "spikes_per_sample_median": float(np.median(spk)),
                         **key_metrics(keys_of(mv, mode), keys_of(mt, mode))})
        log(f"K2 {args.dataset} {u}: " + " | ".join(f"{r['key']} unik {r['unique_test']} seen {r['test_seen_in_val']:.3f}"
                                                   for r in rows[-3:]))
        if u != "s0_f0":
            continue
        lab_c = labels_s0f0(args.dataset, S)[S["order_capture"]]
        caches = {v: G.make_cache(libs, v, W, Xval) for v in CACHED}
        for cls in sorted(set(lab_c.tolist())):
            idx = np.where(lab_c == cls)[0]
            Xc = np.ascontiguousarray(X[idx])
            km = {name: key_metrics(keys_of(mv, mode), keys_of(mt[idx], mode))
                  for mode, name in [("E", "exact"), ("C", "count"), ("T", "tri")]}
            for v in V8:                                       # warm-up
                run_stats(libs, v, W, Xc, caches.get(v))
            rng = np.random.RandomState(13)
            t, stt = {v: [] for v in V8}, {v: None for v in V8}
            for _ in range(args.repeats):
                for v in rng.permutation(V8):
                    c = caches.get(v)
                    if c is not None:
                        c.restore()
                    err, st = np.empty(len(Xc), np.float32), np.zeros(5, np.int64)
                    t0 = time.perf_counter_ns()
                    G.run(libs, v, W, Xc, err, st, c)
                    t[v].append((time.perf_counter_ns() - t0) / len(Xc))
                    stt[v] = st.copy()
            for v in V8:
                crow.append({"dataset": args.dataset, "unit": u, "class": cls, "n": len(Xc), "variant": v,
                             "ns_median": float(np.median(t[v])),
                             "hit_rate": float(stt[v][0] / len(Xc)) if v in CACHED else np.nan,
                             **{f"{k}_per_sample": float(stt[v][i] / len(Xc)) for i, k in enumerate(STAT_NAMES)},
                             **{f"{name}_{mk}": mv_ for name, d in km.items() for mk, mv_ in d.items()}})
            log(f"K2 kelas {cls} (n={len(Xc)}): " + " ".join(
                f"{v}={np.median(t[v]):.0f}ns" for v in ("DENSE_ZS", "SNN_MEMOV3_16", "SNN_RQT_16", "DENSE_AQV33_16")))
    pd.DataFrame(rows).to_csv(res / f"k2_keys_{args.dataset}.csv", index=False)
    pd.DataFrame(crow).to_csv(res / f"k2_class_{args.dataset}.csv", index=False)


def phase_k3(libs, K, pkg, units, res, args):
    rows = []
    mask = libs[0].pmu_open()
    for u in units:
        W, S, Xval = G.load_unit(pkg, u)
        X = stream(S)
        caches = {v: G.make_cache(libs, v, W, Xval) for v in CACHED}
        for v in V8:
            run_stats(libs, v, W, X, caches.get(v))            # warm-up
            vals, st_last = [], None
            for _ in range(args.pmu_reps):
                c = caches.get(v)
                if c is not None:
                    c.restore()
                err, st, pc = np.empty(len(X), np.float32), np.zeros(5, np.int64), np.zeros(5, np.int64)
                libs[0].pmu_begin()
                G.run(libs, v, W, X, err, st, c)
                libs[0].pmu_end(pc.ctypes.data_as(F.I64P))
                vals.append(pc.copy()); st_last = st.copy()
            med = np.median(np.array(vals, np.float64), axis=0)
            r = {"dataset": args.dataset, "unit": u, "variant": v, "n": len(X)}
            for i, k in enumerate(PMU_NAMES):
                r[f"{k}_per_sample"] = float(med[i] / len(X)) if mask >> i & 1 and med[i] >= 0 else np.nan
            if r["cycles_per_sample"] == r["cycles_per_sample"] and r["instructions_per_sample"] > 0:
                r["ipc"] = r["instructions_per_sample"] / r["cycles_per_sample"]
                r["l1d_refill_per_kinstr"] = 1000 * r["l1d_refill_per_sample"] / r["instructions_per_sample"]
            r.update({f"{k}_per_sample_kernel": float(st_last[i] / len(X)) for i, k in enumerate(STAT_NAMES)})
            r.update(F.sys_info())
            rows.append(r)
        log(f"K3 {args.dataset} {u}: " + " ".join(f"{r['variant']}={r['cycles_per_sample']:.0f}cyc"
                                                  for r in rows if r["unit"] == u))
    pd.DataFrame(rows).to_csv(res / f"k3_pmu_{args.dataset}.csv", index=False)


def phase_k4(libs, K, pkg, units, res, args):
    rows, caprows = [], []
    W, S, Xval = G.load_unit(pkg, "s0_f0")
    wbytes = {m: int(sum(v.nbytes for v in W[m].values() if isinstance(v, np.ndarray) and v.dtype == np.float32))
              for m in ("SNN_AE", "Dense_AE")}
    for v0 in ("SNN_MEMOV3", "SNN_RQT", "DENSE_AQV33"):
        for lc in (12, 14, 16, 18, 20):
            v = f"{v0}_{lc}"
            gc.collect(); time.sleep(0.2)
            r0 = rss_kb()
            c = F.Cache(lc, W["SNN_AE"]["dout"])
            r1 = rss_kb()
            G.run(libs, v, W, Xval, np.empty(len(Xval), np.float32), np.zeros(5, np.int64), c)
            r2 = rss_kb()
            rows.append({"dataset": args.dataset, "unit": "s0_f0", "variant": v0, "logcap": lc,
                         "analytic_bytes": int(c.keys.nbytes + c.ys.nbytes), "rss_before_kb": r0,
                         "rss_after_alloc_kb": r1, "rss_after_prefill_kb": r2,
                         "valid_slots_after_prefill": int(c.keys[3::4].sum()),
                         "weights_bytes_snn": wbytes["SNN_AE"], "weights_bytes_dense": wbytes["Dense_AE"]})
            del c
    for u in units:
        W, S, Xval = G.load_unit(pkg, u)
        X = stream(S)
        grid = [f"{v0}_{lc}" for v0 in ("SNN_MEMOV3", "SNN_RQC", "SNN_RQT", "DENSE_AQV32", "DENSE_AQV33")
                for lc in (12, 14, 16)] + ["DENSE_ZS"]
        caches = {v: G.make_cache(libs, v, W, Xval) for v in grid if v != "DENSE_ZS"}
        for v in grid:
            run_stats(libs, v, W, X, caches.get(v))
        rng = np.random.RandomState(17)
        t, h = {v: [] for v in grid}, {v: [] for v in grid}
        for _ in range(args.repeats):
            for v in rng.permutation(grid):
                c = caches.get(v)
                if c is not None:
                    c.restore()
                err, st = np.empty(len(X), np.float32), np.zeros(5, np.int64)
                t0 = time.perf_counter_ns()
                G.run(libs, v, W, X, err, st, c)
                t[v].append((time.perf_counter_ns() - t0) / len(X))
                h[v].append(st[0] / len(X))
        base = float(np.median(t["DENSE_ZS"]))
        for v in grid:
            caprows.append({"dataset": args.dataset, "unit": u, "variant": v, "ns_median": float(np.median(t[v])),
                            "ratio_vs_dense_zs": float(np.median(t[v])) / base,
                            "hit_rate": float(np.mean(h[v])) if v != "DENSE_ZS" else np.nan, **F.sys_info()})
        log(f"K4 {args.dataset} {u}: " + " ".join(f"{v}={np.median(t[v]) / base:.3f}/{np.mean(h[v]):.3f}"
                                                  for v in grid if v != "DENSE_ZS"))
    pd.DataFrame(rows).to_csv(res / f"k4_memory_{args.dataset}.csv", index=False)
    pd.DataFrame(caprows).to_csv(res / f"k4_capacity_{args.dataset}.csv", index=False)
# ======== END: FASE ========


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["edge_iiotset", "ciciot2023"])
    ap.add_argument("--phase", required=True, choices=["check", "k2", "k3", "k4"])
    ap.add_argument("--pkg", default=str(HOME / "s7f" / "rpi_package"))
    ap.add_argument("--result", default=str(HOME / "0-revision-results-v2" / "s7k"))
    ap.add_argument("--units", default="s0_f0,s1_f0,s2_f0")
    ap.add_argument("--core", type=int, default=3)
    ap.add_argument("--repeats", type=int, default=15)
    ap.add_argument("--pmu_reps", type=int, default=5)
    args = ap.parse_args()
    os.sched_setaffinity(0, {args.core})
    pkg, res = Path(args.pkg) / args.dataset, Path(args.result)
    res.mkdir(parents=True, exist_ok=True)
    F.verify_package(pkg)
    libs, K = G.load_libs(), load_keys_lib()
    units = args.units.split(",")
    log(f"{args.dataset} fase={args.phase} unit={units} core={args.core} {F.sys_info()}")
    {"check": phase_check, "k2": phase_k2, "k3": phase_k3, "k4": phase_k4}[args.phase](libs, K, pkg, units, res, args)
    log(f"fase {args.phase} selesai")


if __name__ == "__main__":
    main()
