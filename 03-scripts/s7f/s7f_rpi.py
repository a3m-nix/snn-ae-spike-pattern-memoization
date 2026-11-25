#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7f RPi — memoization eksak kode spike SNN-AE vs Dense-AE di Raspberry Pi 5 (PREREG_s7f_memo.md bagian 5).

Fase (dipanggil berurutan oleh run_scheduled.sh; tiap fase dapat dilanjutkan bila terputus):
  check   : kompilasi; di perangkat ini SNN_MEMO harus bit-identik dengan SNN_COUNT (seluruh test fold,
            cold & val), dan keputusan SNN_COUNT / DENSE >= --min_agreement terhadap skor Keras server.
  latency : 30 pass per varian, urutan varian diacak; urutan stream capture & acak; isi awal cache
            di luar waktu terukur; PMU (cycles, instructions, L1D) dari s7c_native.c.
  power   : FNIRSI, protokol s7c v2 / s7a v2 (pendinginan + idle per kondisi, jendela >= --min_sec),
            --rounds ronde dengan urutan kondisi diacak. Untuk SNN_MEMO, cache DIPULIHKAN dari snapshot
            isi awal sebelum tiap pass DI DALAM jendela daya (biaya pemulihan ikut terhitung).
Varian: DENSE, DENSE_ZS, SNN_COUNT (s7c_native.c), SNN_MEMO_12_val, SNN_MEMO_14_val (s7f_memo.c).
Satu thread, core dipatok. Fungsi daya diimpor dari s7a_v2.py / rpi5_fnirsi_attack_autov2.py (tidak diubah).

Contoh (root, folder /home/a3m-nix/snn-ae-final/s7f):
  python3 s7f_rpi.py --dataset edge_iiotset --phase check
"""
# ======== END: HEADER ========

# ======== START: IMPORT + KONFIGURASI ========
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
HOME = Path("/home/a3m-nix/snn-ae-final")
VARIANTS = ["DENSE", "DENSE_ZS", "SNN_COUNT", "SNN_MEMO_12_val", "SNN_MEMO_14_val"]
CHECK_CAPS = [12, 14]
MODELS = ["Dense_AE", "SNN_AE"]
F32P, I64P, U32P = (ctypes.POINTER(t) for t in (ctypes.c_float, ctypes.c_int64, ctypes.c_uint32))
PMU_NAMES = ["cycles", "instructions", "l1d_access", "l1d_refill", "mem_access"]


def log(m):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [S7f] {m}", flush=True)


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sys_info():
    rd = lambda p: Path(p).read_text().strip() if Path(p).exists() else None
    t = rd("/sys/class/thermal/thermal_zone0/temp")
    f = rd("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq")
    return {"time": datetime.now().isoformat(), "machine": platform.machine(), "loadavg": rd("/proc/loadavg"),
            "governor": rd("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
            "freq_mhz": float(f) / 1000 if f else None, "temp_c": float(t) / 1000 if t else None}
# ======== END: IMPORT + KONFIGURASI ========


# ======== START: KOMPILASI ========
def load_libs():
    out = HERE / "build"
    out.mkdir(exist_ok=True)
    arch = "-mcpu=native" if platform.machine() == "aarch64" else "-march=native"
    libs = []
    for src in ["s7c_native_copy.c", "s7f_memo.c"]:
        so = out / (Path(src).stem + ".so")
        subprocess.run(["gcc", "-O3", arch, "-shared", "-fPIC", "-o", str(so), str(HERE / src)], check=True)
        libs.append(ctypes.CDLL(str(so)))
    s7c, memo = libs
    s7c.dense_ae.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             F32P, F32P, F32P, F32P, F32P, F32P, ctypes.c_int, F32P, I64P]
    s7c.snn_ae.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           F32P, F32P, ctypes.c_float, ctypes.c_float, F32P, F32P, ctypes.c_float, ctypes.c_float,
                           F32P, F32P, ctypes.c_int, F32P, I64P]
    memo.snn_memo.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                              F32P, F32P, ctypes.c_float, ctypes.c_float, F32P, F32P, ctypes.c_float, ctypes.c_float,
                              F32P, F32P, U32P, F32P, ctypes.c_int, F32P, I64P]
    memo.snn_memo.restype = ctypes.c_int
    s7c.pmu_open.restype = ctypes.c_int
    s7c.pmu_end.argtypes = [I64P]
    return s7c, memo
# ======== END: KOMPILASI ========


# ======== START: PAKET DATA ========
def load_unit(pkg, unit):
    wz, sz = np.load(pkg / f"weights_{unit}.npz"), np.load(pkg / f"stream_{unit}.npz")
    W = {}
    for m in MODELS:
        w = {k.split("__", 1)[1]: wz[k] for k in wz.files if k.startswith(m + "__")}
        for k in ["th_e", "dk_e", "th_d", "dk_d"]:
            if k in w:
                w[k] = float(w[k])
        for k in ["T", "din", "L", "dout"]:
            if k in w:
                w[k] = int(w[k])
        w["din"], w["L"], w["dout"] = int(w["We"].shape[0]), int(w["We"].shape[1]), int(w["Wo"].shape[1])
        W[m] = {k: (np.ascontiguousarray(v, np.float32) if isinstance(v, np.ndarray) and v.dtype.kind == "f" else v)
                for k, v in w.items()}
    S = {k: sz[k] for k in sz.files}
    S["X"] = np.ascontiguousarray(S["X"], np.float32)
    Xval = np.ascontiguousarray(np.load(pkg / f"val_{unit}.npz")["X"], np.float32)
    return W, S, Xval


def verify_package(pkg):
    man = json.loads((pkg / "manifest.json").read_text())
    bad = [f for f, h in man["files_sha256"].items() if sha_file(pkg / f) != h]
    if bad:
        raise SystemExit(f"paket rusak: {bad}")
    for src, h in man["sources_sha256"].items():
        local = HERE / ("s7c_native_copy.c" if src == "s7c_native.c" else src)
        if sha_file(local) != h:
            raise SystemExit(f"sumber {src} berbeda dari yang dipakai ekspor")
    if (HOME / "s7c_native.c").exists() and sha_file(HOME / "s7c_native.c") != man["sources_sha256"]["s7c_native.c"]:
        raise SystemExit("s7c_native.c di RPi berbeda dari salinan S7f")
    return man
# ======== END: PAKET DATA ========


# ======== START: KERNEL ========
def p(a, t=F32P):
    return a.ctypes.data_as(t)


class Cache:
    def __init__(self, logcap, dout):
        self.logcap = logcap
        self.keys = np.zeros((1 << logcap) * 4, dtype=np.uint32)
        self.ys = np.zeros((1 << logcap) * dout, dtype=np.float32)
        self.snap = None

    def reset(self):
        self.keys[3::4] = 0

    def take_snapshot(self):
        self.snap = (self.keys.copy(), self.ys.copy())

    def restore(self):
        np.copyto(self.keys, self.snap[0])
        np.copyto(self.ys, self.snap[1])


def run(libs, variant, W, X, err, stats, cache=None):
    s7c, memo = libs
    n = len(X)
    if variant in ("DENSE", "DENSE_ZS"):
        d = W["Dense_AE"]
        s7c.dense_ae(p(X), n, d["din"], d["L"], d["dout"], p(d["We"]), p(d["be"]), p(d["Wd"]), p(d["bd"]),
                     p(d["Wo"]), p(d["bo"]), int(variant == "DENSE_ZS"), p(err), p(stats, I64P))
        return
    w = W["SNN_AE"]
    args = (p(X), n, w["din"], w["L"], w["dout"], w["T"], p(w["We"]), p(w["be"]), w["th_e"], w["dk_e"],
            p(w["Wd"]), p(w["bd"]), w["th_d"], w["dk_d"], p(w["Wo"]), p(w["bo"]))
    if variant == "SNN_COUNT":
        s7c.snn_ae(*args, 2, p(err), p(stats, I64P))
    elif memo.snn_memo(*args, p(cache.keys, U32P), p(cache.ys), cache.logcap, p(err), p(stats, I64P)) != 0:
        raise SystemExit("snn_memo: argumen tidak valid")


def make_cache(libs, variant, W, Xval):
    if not variant.startswith("SNN_MEMO"):
        return None
    _, _, lc, mode = variant.split("_")
    c = Cache(int(lc), W["SNN_AE"]["dout"])
    if mode == "val":
        run(libs, variant, W, Xval, np.empty(len(Xval), np.float32), np.zeros(5, np.int64), c)
    c.take_snapshot()
    return c
# ======== END: KERNEL ========


# ======== START: FASE CHECK ========
def phase_check(libs, pkg, units, res, args):
    rows = []
    for unit in units:
        W, S, Xval = load_unit(pkg, unit)
        X = S["X"]
        ref, st = np.empty(len(X), np.float32), np.zeros(5, np.int64)
        run(libs, "SNN_COUNT", W, X, ref, st)
        row = {"unit": unit, "n_test": int(len(X))}
        for lc in CHECK_CAPS:
            for mode in ("cold", "val"):
                v = f"SNN_MEMO_{lc}_{mode}"
                c = make_cache(libs, v, W, Xval)
                e = np.empty(len(X), np.float32)
                run(libs, v, W, X, e, np.zeros(5, np.int64), c)
                row[f"bit_identical_{v}"] = bool(np.array_equal(e, ref))
        dz = np.empty(len(X), np.float32)
        run(libs, "DENSE", W, X, dz, np.zeros(5, np.int64))
        for m, s in [("SNN_AE", ref), ("Dense_AE", dz)]:
            thr = float(S[f"{m}__thr_p99"])
            row[f"agree_keras_{m}"] = float(np.mean((s > thr) == (S[f"{m}__keras_test"] > thr)))
            row[f"max_abs_diff_keras_{m}"] = float(np.max(np.abs(s.astype(np.float64) - S[f"{m}__keras_test"])))
        row["pass"] = bool(all(v for k, v in row.items() if k.startswith("bit_identical"))
                           and all(row[f"agree_keras_{m}"] >= args.min_agreement for m in MODELS))
        rows.append(row)
        log(f"CHECK {unit}: pass={row['pass']} | " + " ".join(f"{k}={v}" for k, v in row.items()
                                                               if k.startswith(("bit_", "agree_"))))
    out = {"dataset": args.dataset, "system": sys_info(), "rows": rows, "pass": all(r["pass"] for r in rows)}
    (res / f"check_{args.dataset}.json").write_text(json.dumps(out, indent=2))
    if not out["pass"]:
        raise SystemExit(3)
# ======== END: FASE CHECK ========


# ======== START: FASE LATENCY + PMU ========
def phase_latency(libs, pkg, units, res, args):
    pmu_mask = libs[0].pmu_open()
    rows = []
    for unit in units:
        jp = res / f"latency_{args.dataset}_{unit}.csv"
        if jp.exists():
            log(f"SKIP latency {unit}: sudah ada")
            continue
        W, S, Xval = load_unit(pkg, unit)
        caches = {v: make_cache(libs, v, W, Xval) for v in VARIANTS}
        urows = []
        for oname in ["capture", "random"]:
            Xm = np.ascontiguousarray(S["X"][S[f"order_{oname}"]])
            err, st = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
            for v in VARIANTS:                              # warm-up
                if caches[v] is not None:
                    caches[v].restore()
                run(libs, v, W, Xm, err, st, caches[v])
            rng = np.random.RandomState(7)
            times, hits = {v: [] for v in VARIANTS}, {v: [] for v in VARIANTS}
            for _ in range(args.repeats):
                for v in rng.permutation(VARIANTS):
                    if caches[v] is not None:
                        caches[v].restore()                 # di luar waktu terukur
                    st[:] = 0
                    t0 = time.perf_counter_ns()
                    run(libs, v, W, Xm, err, st, caches[v])
                    times[v].append((time.perf_counter_ns() - t0) / len(Xm))
                    if caches[v] is not None:
                        hits[v].append(st[0] / len(Xm))
            pmu = {}
            for v in VARIANTS:
                vals = []
                for _ in range(5):
                    if caches[v] is not None:
                        caches[v].restore()
                    c = np.zeros(5, np.int64)
                    libs[0].pmu_begin()
                    run(libs, v, W, Xm, err, st, caches[v])
                    libs[0].pmu_end(c.ctypes.data_as(I64P))
                    vals.append(c.copy())
                med = np.median(np.array(vals, dtype=np.float64), axis=0)
                pmu[v] = {f"{k}_per_sample": (float(med[i]) / len(Xm) if med[i] >= 0 else None)
                          for i, k in enumerate(PMU_NAMES)}
            base = float(np.median(times["DENSE_ZS"]))
            for v in VARIANTS:
                urows.append({"dataset": args.dataset, "unit": unit, "order": oname, "variant": v, "n": len(Xm),
                              "ns_per_sample_median": float(np.median(times[v])),
                              "ns_per_sample_p10": float(np.percentile(times[v], 10)),
                              "ns_per_sample_p90": float(np.percentile(times[v], 90)),
                              "ratio_vs_dense_zs": float(np.median(times[v])) / base,
                              "hit_rate": float(np.mean(hits[v])) if hits[v] else np.nan, **pmu[v], **sys_info()})
            log(f"LATENCY {unit} {oname}: DENSE_ZS={base:.0f} ns | " + " | ".join(
                f"{v} x{np.median(times[v]) / base:.3f}" for v in VARIANTS if v != "DENSE_ZS"))
        pd.DataFrame(urows).to_csv(jp, index=False)
        rows += urows
    log(f"PMU tersedia: {[k for i, k in enumerate(PMU_NAMES) if pmu_mask >> i & 1]}")
# ======== END: FASE LATENCY + PMU ========


# ======== START: FASE POWER (FNIRSI) ========
def power_modules():
    spec = importlib.util.spec_from_file_location("s7a", HOME / "s7a_v2.py")
    s7a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(s7a)                            # memuat juga base (rpi5_fnirsi_attack_autov2.py)
    return s7a, s7a.base


def phase_power(libs, pkg, units, res, args):
    s7a, base = power_modules()
    pdir = res / "power"
    pdir.mkdir(exist_ok=True)
    data = {u: load_unit(pkg, u) for u in units}
    fn = {"r": None, "idle": (base.PBUS_IDLE_DEFAULT, 0.0, 0), "rate": None}

    def start_fnirsi():                                     # = s7c_v2.main.start_fnirsi
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

    def one(unit, v):
        W, S, Xval = data[unit]
        Xm = np.ascontiguousarray(S["X"][S["order_capture"]])
        c = make_cache(libs, v, W, Xval)
        err, st = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
        for _ in range(5):                                  # warm-up
            if c is not None:
                c.restore()
            run(libs, v, W, Xm, err, st, c)
        s7a.cooldown_and_idle(fn, args)
        fn["r"].clear_readings()
        lat, rest, t0 = [], [], time.perf_counter()
        while time.perf_counter() - t0 < args.min_sec:
            t1 = time.perf_counter()
            if c is not None:
                c.restore()                                 # DI DALAM jendela: ikut terhitung
                rest.append((time.perf_counter() - t1) * 1000.0)
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
                "restore_ms_median": float(np.median(rest)) if rest else 0.0,
                "board_power_metrics": board, "idle_measurement": {"pbus_idle_w": fn["idle"][0], **(fn.get("cool") or {})}}

    try:
        for rnd in range(1, args.rounds + 1):
            conds = [(u, v) for u in units for v in VARIANTS]
            for i in np.random.RandomState(100 + rnd).permutation(len(conds)):
                unit, v = conds[i]
                jp = pdir / f"r{rnd:02d}_{args.dataset}_{unit}_{v}.json"
                if jp.exists() and json.loads(jp.read_text()).get("power_valid"):
                    log(f"SKIP power r{rnd} {unit} {v}")
                    continue
                for attempt in range(args.max_retries + 1):
                    if fn["r"] is None or not fn["r"].is_alive():
                        start_fnirsi()
                    pr = one(unit, v)
                    if pr["power_valid"] or attempt == args.max_retries:
                        break
                    log(f"[RETRY {attempt + 1}] r{rnd} {unit} {v}: FNIRSI tidak valid")
                    fn["r"].stop(); fn["r"] = None; time.sleep(5)
                b = pr.pop("board_power_metrics") or {}
                pr.update({"round": rnd, "dataset": args.dataset, "unit": unit, "variant": v, "system": sys_info(),
                           **{k: b.get(k) for k in ["pbus_idle_w", "pbus_inference_w", "p_delta_w",
                                                    "board_energy_delta_mj_per_sample",
                                                    "board_energy_active_mj_per_sample", "throughput_sps"]}})
                jp.write_text(json.dumps(base.sanitize_for_json(pr), indent=2))
                log(f"POWER r{rnd} {unit} {v}: {pr['latency_us_per_sample_median']:.3f} us | "
                    f"E_delta={pr.get('board_energy_delta_mj_per_sample')} mJ | valid={pr['power_valid']}")
    finally:
        if fn["r"]:
            fn["r"].stop()
# ======== END: FASE POWER ========


# ======== START: MAIN ========
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=["edge_iiotset", "ciciot2023"])
    ap.add_argument("--phase", required=True, choices=["check", "latency", "power"])
    ap.add_argument("--pkg", default=str(HERE / "rpi_package"))
    ap.add_argument("--result", default=str(HOME / "0-revision-results-v2" / "s7f"))
    ap.add_argument("--units", default="s0_f0,s1_f0,s2_f0")
    ap.add_argument("--core", type=int, default=3)
    ap.add_argument("--repeats", type=int, default=30)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--min_sec", type=float, default=30.0)
    ap.add_argument("--min_agreement", type=float, default=0.999)
    ap.add_argument("--idle_sec", type=int, default=20)
    ap.add_argument("--cool_margin", type=float, default=2.0)
    ap.add_argument("--cool_timeout", type=int, default=600)
    ap.add_argument("--fnirsi_path", default=str(HOME / "fnirsi_logger.py"))
    ap.add_argument("--max_retries", type=int, default=3)
    args = ap.parse_args()
    os.sched_setaffinity(0, {args.core})
    pkg = Path(args.pkg) / args.dataset
    res = Path(args.result)
    res.mkdir(parents=True, exist_ok=True)
    verify_package(pkg)
    libs = load_libs()
    units = args.units.split(",")
    log(f"{args.dataset} fase={args.phase} | unit={units} | core={args.core} | {sys_info()}")
    {"check": phase_check, "latency": phase_latency, "power": phase_power}[args.phase](libs, pkg, units, res, args)
    log(f"fase {args.phase} selesai | {res}")


if __name__ == "__main__":
    main()
# ======== END: MAIN ========
