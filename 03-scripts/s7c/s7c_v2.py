# ======== START: HEADER ========
"""
S7c v2 — DENSE-AE vs SNN-AE NATIVE C DI RASPBERRY PI 5 (R1.4, R2.9, R3.3)
Revisi Paper 1 SNN-AE — Scientific Reports (menggantikan s7c revisi pertama)

Pertanyaan: bagaimana tiga cara bacaan bobot SNN-AE (model T3) berperilaku di CPU nyata,
dibanding Dense-AE dengan optimasi yang setara?
  DENSE      : Dense-AE padat
  DENSE_ZS   : Dense-AE zero-skip aktivasi ReLU (setara T2; Albericio dkk. 2016, Han dkk. 2016)
  SNN_TENSOR : SNN-AE, spike diproses sebagai tensor padat (seperti TF)
  SNN_SPIKE  : SNN-AE, satu baris bobot per spike per time step (event-driven)
  SNN_COUNT  : SNN-AE, readout output count-based (Lee dkk., PTB, HPCA 2022)
Semua: BN dilipat ke bobot (Jacob dkk. 2018), satu thread, core dipatok, -O3.
SNN: arus input encoder dihitung sekali (loop-invariant code motion; asumsi model energi).

Alur per dataset:
  1. Ekspor bobot dari payload v2 (.keras) dan lipat BN.
  2. Verifikasi: skor seluruh test fold vs skor server (keputusan p99 >= --min_agreement);
     jumlah spike ketiga varian SNN harus identik.
  3. PMU (perf_event_open): cycles, instructions, L1D access/refill, mem access per sampel,
     dibandingkan dengan jumlah baris bobot yang dibaca (model T3).
  4. Daya FNIRSI: pendinginan + idle per varian (S7a v2), varian dijalankan >= --min_sec.
Data: subset pengukuran S7a v2 (10.000 normal + 10.000 serangan, seed 42).
Jalankan (root, folder /home/a3m-nix/snn-ae-final):
  python3 s7c_v2.py --check_only      # kompilasi + verifikasi + PMU, tanpa daya
  python3 s7c_v2.py                   # lengkap dengan FNIRSI
"""
# ======== END: HEADER ========


# ======== START: IMPORT ========
import argparse
import ctypes
import importlib.util
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

HOME = Path("/home/a3m-nix/snn-ae-final")
_spec = importlib.util.spec_from_file_location("s7a", HOME / "s7a_v2.py")
s7a = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(s7a)
base = s7a.base

import numpy as np
import pandas as pd
import tensorflow as tf
# ======== END: IMPORT ========


# ======== START: KONFIGURASI ========
SRC = HOME / "s7c_native.c"
LIB = HOME / "s7c_native.so"
RESULT = HOME / "0-revision-results-v2" / "s7c"
VARIANTS = {"DENSE": ("Dense_AE", 0), "DENSE_ZS": ("Dense_AE", 1),
            "SNN_TENSOR": ("SNN_AE", 0), "SNN_SPIKE": ("SNN_AE", 1), "SNN_COUNT": ("SNN_AE", 2)}
PMU_NAMES = ["cycles", "instructions", "l1d_access", "l1d_refill", "mem_access"]
F32P = ctypes.POINTER(ctypes.c_float)
I64P = ctypes.POINTER(ctypes.c_int64)


def log(m):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [S7c] {m}", flush=True)
# ======== END: KONFIGURASI ========


# ======== START: KOMPILASI DAN LIBRARY ========
def load_lib():
    if not LIB.exists() or LIB.stat().st_mtime < SRC.stat().st_mtime:
        cmd = ["gcc", "-O3", "-mcpu=native", "-shared", "-fPIC", "-o", str(LIB), str(SRC)]
        log("Kompilasi: " + " ".join(cmd))
        subprocess.run(cmd, check=True)
    lib = ctypes.CDLL(str(LIB))
    lib.dense_ae.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                             F32P, F32P, F32P, F32P, F32P, F32P, ctypes.c_int, F32P, I64P]
    lib.snn_ae.argtypes = [F32P, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           F32P, F32P, ctypes.c_float, ctypes.c_float,
                           F32P, F32P, ctypes.c_float, ctypes.c_float,
                           F32P, F32P, ctypes.c_int, F32P, I64P]
    lib.pmu_open.restype = ctypes.c_int
    lib.pmu_end.argtypes = [I64P]
    return lib


def ptr(a):
    return a.ctypes.data_as(F32P)
# ======== END: KOMPILASI DAN LIBRARY ========


# ======== START: EKSPOR BOBOT (LIPAT BN) ========
def c32(a):
    return np.ascontiguousarray(a, dtype=np.float32)


def export_weights(ds, model_name):
    m = tf.keras.models.load_model(s7a.PAYLOAD_DIR / ds / "models" / f"{model_name}.keras", compile=False,
                                   custom_objects={"SpikingLayer": base.SpikingLayer})
    names = [l.name for l in m.layers]
    if names[1:] != ["batch_norm", "encoder", "decoder", "output"]:
        raise SystemExit(f"{model_name}: struktur lapisan tak terduga {names}")
    bn, enc, dec, out = (m.get_layer(n) for n in ["batch_norm", "encoder", "decoder", "output"])
    g = bn.gamma.numpy().astype(np.float64) if bn.gamma is not None else 1.0
    bt = bn.beta.numpy().astype(np.float64) if bn.beta is not None else 0.0
    scale = g / np.sqrt(bn.moving_variance.numpy().astype(np.float64) + bn.epsilon)
    shift = bt - bn.moving_mean.numpy().astype(np.float64) * scale
    spk = isinstance(enc, base.SpikingLayer)
    if spk != isinstance(dec, base.SpikingLayer) or spk != (model_name == "SNN_AE"):
        raise SystemExit(f"{model_name}: kombinasi lapisan tidak sesuai")
    if spk:
        We, be = enc.w.numpy().astype(np.float64), enc.b.numpy().astype(np.float64)
        Wd, bd = dec.w.numpy().astype(np.float64), dec.b.numpy().astype(np.float64)
        if not enc.return_sequences or dec.return_sequences or enc.time_steps != dec.time_steps:
            raise SystemExit("SNN_AE: konfigurasi return_sequences/time_steps tidak sesuai")
        se, sd = np.sqrt(We.shape[0]), np.sqrt(Wd.shape[0])     # skala 1/sqrt(fan_in) di SpikingLayer
        w = {"We": c32(scale[:, None] * We / se), "be": c32((shift @ We + be) / se),
             "Wd": c32(Wd / sd), "bd": c32(bd / sd),
             "th_e": enc.threshold, "dk_e": enc.decay, "th_d": dec.threshold, "dk_d": dec.decay,
             "T": int(enc.time_steps)}
    else:
        for l in (enc, dec):
            if l.activation.__name__ != "relu":
                raise SystemExit(f"Dense_AE {l.name}: aktivasi {l.activation.__name__}")
        We, be = (v.astype(np.float64) for v in enc.get_weights())
        Wd, bd = (v.astype(np.float64) for v in dec.get_weights())
        w = {"We": c32(scale[:, None] * We), "be": c32(shift @ We + be), "Wd": c32(Wd), "bd": c32(bd)}
    if out.activation.__name__ != "linear":
        raise SystemExit(f"{model_name}: output tidak linear")
    Wo, bo = out.get_weights()
    w.update({"Wo": c32(Wo), "bo": c32(bo), "din": int(w["We"].shape[0]), "L": int(w["We"].shape[1]),
              "dout": int(Wo.shape[1])})
    del m
    tf.keras.backend.clear_session()
    return w
# ======== END: EKSPOR BOBOT (LIPAT BN) ========


# ======== START: EKSEKUSI KERNEL ========
def run_kernel(lib, variant, W, X, err, stats):
    model, mode = VARIANTS[variant]
    n = len(X)
    if model == "Dense_AE":
        lib.dense_ae(ptr(X), n, W["din"], W["L"], W["dout"], ptr(W["We"]), ptr(W["be"]), ptr(W["Wd"]),
                     ptr(W["bd"]), ptr(W["Wo"]), ptr(W["bo"]), mode, ptr(err), stats.ctypes.data_as(I64P))
    else:
        lib.snn_ae(ptr(X), n, W["din"], W["L"], W["dout"], W["T"], ptr(W["We"]), ptr(W["be"]), W["th_e"],
                   W["dk_e"], ptr(W["Wd"]), ptr(W["bd"]), W["th_d"], W["dk_d"], ptr(W["Wo"]), ptr(W["bo"]),
                   mode, ptr(err), stats.ctypes.data_as(I64P))


def score(lib, variant, W, X):
    err = np.empty(len(X), dtype=np.float32)
    stats = np.zeros(5, dtype=np.int64)
    run_kernel(lib, variant, W, X, err, stats)
    return err.astype(np.float64), stats


def activity(variant, W, stats, n):
    """Aktivitas dan jumlah baris bobot yang dibaca per sampel (bandingkan dengan model T3)."""
    din, L, dout = W["din"], W["L"], W["dout"]
    if VARIANTS[variant][0] == "Dense_AE":
        z1, z2 = stats[0] / (n * L), stats[1] / (n * L)
        zs = VARIANTS[variant][1] == 1
        rows = din + (L * (1 - z1) if zs else L) + (L * (1 - z2) if zs else L)
        words = din * L + (L * L * (1 - z1) if zs else L * L) + (L * dout * (1 - z2) if zs else L * dout)
        return {"relu_zero_enc": z1, "relu_zero_dec": z2, "weight_rows_per_sample": rows,
                "weight_words_per_sample": words}
    rows_d, rows_o = stats[4] / n, stats[3] / n
    return {"k_enc": stats[0] / (n * L), "k_dec": stats[1] / (n * L), "P_dec": stats[2] / (n * L),
            "weight_rows_per_sample": din + rows_d + rows_o,
            "weight_words_per_sample": din * L + rows_d * L + rows_o * dout}
# ======== END: EKSEKUSI KERNEL ========


# ======== START: VERIFIKASI DAN PMU ========
def verify(lib, ds, P, Ws, args):
    rows, spikes = {}, {}
    for v, (model, _) in VARIANTS.items():
        s, st = score(lib, v, Ws[model], P["Xs"])
        ref = P["ref"][model].astype(np.float64)
        thr = float(P["thr"][model][s7a.OP])
        agree = float(np.mean((s > thr) == (ref > thr)))
        det = s7a.detection_metrics(s, P["y"], P["lt"], thr)
        rows[v] = {"decision_agreement_vs_server": agree, "max_abs_score_diff": float(np.max(np.abs(s - ref))),
                   "max_rel_score_diff": float(np.max(np.abs(s - ref) / np.maximum(np.abs(ref), 1e-12))),
                   "auc_rpi": det["auc"], "f1_full": det["f1"], "fpr_full": det["fpr"],
                   **activity(v, Ws[model], st, len(s))}
        if model == "SNN_AE":
            spikes[v] = (int(st[0]), int(st[1]), int(st[2]))
        log(f"VERIFY {ds} {v}: keputusan sama={agree:.6f} max|Δ|={rows[v]['max_abs_score_diff']:.2e} "
            f"F1={det['f1']:.4f}")
        if agree < args.min_agreement:
            raise SystemExit(f"{ds} {v}: kesamaan keputusan {agree:.6f} < {args.min_agreement}")
    if len(set(spikes.values())) != 1:
        raise SystemExit(f"{ds}: jumlah spike berbeda antar varian SNN {spikes}")
    return rows


def pmu_measure(lib, P, Ws, Xm, reps):
    out = {}
    for v, (model, _) in VARIANTS.items():
        vals = []
        for _ in range(reps):
            err, st, c = np.empty(len(Xm), np.float32), np.zeros(5, np.int64), np.zeros(5, np.int64)
            lib.pmu_begin()
            run_kernel(lib, v, Ws[model], Xm, err, st)
            lib.pmu_end(c.ctypes.data_as(I64P))
            vals.append(c.copy())
        med = np.median(np.array(vals, dtype=np.float64), axis=0)
        out[v] = {f"{k}_per_sample": (float(med[i]) / len(Xm) if med[i] >= 0 else None)
                  for i, k in enumerate(PMU_NAMES)}
    return out
# ======== END: VERIFIKASI DAN PMU ========


# ======== START: PENGUKURAN DAYA ========
def power_run(lib, v, W, Xm, args, fn):
    err, st = np.empty(len(Xm), np.float32), np.zeros(5, np.int64)
    for _ in range(5):                                   # warm-up
        run_kernel(lib, v, W, Xm, err, st)
    s7a.cooldown_and_idle(fn, args)
    fn["r"].clear_readings()
    lat, t0 = [], time.perf_counter()
    while time.perf_counter() - t0 < args.min_sec:
        t1 = time.perf_counter()
        run_kernel(lib, v, W, Xm, err, st)
        lat.append((time.perf_counter() - t1) * 1000.0)
    elapsed = time.perf_counter() - t0
    r = fn["r"].get_readings()
    rate = len(r) / max(elapsed, 1e-9)
    valid = bool(fn["r"].is_alive() and fn["rate"] and rate >= 0.5 * fn["rate"] and len(r) > 0)
    board = base.calc_board_metrics(float(np.mean(r)), float(np.std(r)), len(r), fn["idle"][0], fn["idle"][1],
                                    fn["idle"][2], float(np.mean(lat)), float(np.std(lat)), len(Xm)) if r else None
    return {"power_valid": valid, "passes": len(lat), "elapsed_s": elapsed, "fnirsi_rate_hz": rate,
            "latency_us_per_sample_median": float(np.median(lat)) / len(Xm) * 1000.0,
            "board_power_metrics": board,
            "idle_measurement": {"pbus_idle_w": fn["idle"][0], **(fn.get("cool") or {})}}
# ======== END: PENGUKURAN DAYA ========


# ======== START: MAIN ========
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="all", choices=["edge_iiotset", "ciciot2023", "all"])
    ap.add_argument("--check_only", action="store_true", help="kompilasi + verifikasi + PMU, tanpa FNIRSI")
    ap.add_argument("--n_per_class", type=int, default=10_000)
    ap.add_argument("--min_sec", type=float, default=30.0)
    ap.add_argument("--pmu_reps", type=int, default=5)
    ap.add_argument("--core", type=int, default=3)
    ap.add_argument("--min_agreement", type=float, default=0.999)
    ap.add_argument("--idle_sec", type=int, default=20)
    ap.add_argument("--cool_margin", type=float, default=2.0)
    ap.add_argument("--cool_timeout", type=int, default=600)
    ap.add_argument("--fnirsi_path", default=str(HOME / "fnirsi_logger.py"))
    ap.add_argument("--max_retries", type=int, default=3)
    ap.add_argument("--force", action="store_true", help="ukur ulang daya walaupun hasil valid sudah ada")
    args = ap.parse_args()

    RESULT.mkdir(parents=True, exist_ok=True)
    os.sched_setaffinity(0, {args.core})
    lib = load_lib()
    pmu_mask = lib.pmu_open()
    log(f"PMU tersedia: {[k for i, k in enumerate(PMU_NAMES) if pmu_mask >> i & 1]} | core={args.core} | "
        f"governor={base.get_cpu_governor()} | freq={base.get_cpu_freq_mhz()} MHz")
    datasets = ["edge_iiotset", "ciciot2023"] if args.dataset == "all" else [args.dataset]
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

    rows = []
    try:
        for ds in datasets:
            s7a.preflight(ds, False)
            P = s7a.load_payload(ds)
            sub = s7a.stratified_subset(P["y"], args.n_per_class)        # = subset S7a v2
            Xm = np.ascontiguousarray(P["Xs"][sub], dtype=np.float32)
            P["Xs"] = np.ascontiguousarray(P["Xs"], dtype=np.float32)
            Ws = {m: export_weights(ds, m) for m in ["Dense_AE", "SNN_AE"]}
            ver = verify(lib, ds, P, Ws, args)
            pmu = pmu_measure(lib, P, Ws, Xm, args.pmu_reps)
            for v in VARIANTS:
                res = {"dataset": ds, "variant": v, "model": VARIANTS[v][0], "n_measure": int(len(Xm)),
                       "core": args.core, "governor": base.get_cpu_governor(), **ver[v], **pmu[v]}
                jp = RESULT / f"s7c_{ds}_{v}.json"
                old = json.loads(jp.read_text()) if jp.exists() else {}
                if not args.check_only and old.get("power_valid") and not args.force:
                    log(f"SKIP daya {ds} {v}: hasil valid sudah ada")
                    rows.append(old)
                    continue
                if not args.check_only:
                    for attempt in range(args.max_retries + 1):
                        if fn["r"] is None or not fn["r"].is_alive():
                            start_fnirsi()
                        pr = power_run(lib, v, Ws[VARIANTS[v][0]], Xm, args, fn)
                        if pr["power_valid"] or attempt == args.max_retries:
                            break
                        log(f"[RETRY {attempt + 1}] {ds} {v}: FNIRSI tidak valid")
                        fn["r"].stop(); fn["r"] = None; time.sleep(5)
                    b = pr.pop("board_power_metrics") or {}
                    res.update(pr)
                    res.update({k: b.get(k) for k in ["pbus_idle_w", "pbus_inference_w", "p_delta_w",
                                                      "board_energy_delta_mj_per_sample",
                                                      "board_energy_active_mj_per_sample", "throughput_sps"]})
                    log(f"{ds} {v}: {res['latency_us_per_sample_median']:.3f} us/sampel | "
                        f"ΔP={res.get('p_delta_w')} W | E_delta={res.get('board_energy_delta_mj_per_sample')} mJ")
                (RESULT / f"s7c_{ds}_{v}.json").write_text(json.dumps(base.sanitize_for_json(res), indent=2))
                rows.append(res)
    finally:
        if fn["r"]:
            fn["r"].stop()
    df = pd.json_normalize(rows)
    out = RESULT / f"s7c_summary_{'check' if args.check_only else 'power'}_{datetime.now():%Y%m%d_%H%M}.csv"
    df.to_csv(out, index=False)
    cols = [c for c in ["dataset", "variant", "decision_agreement_vs_server", "weight_words_per_sample",
                        "instructions_per_sample", "l1d_access_per_sample", "latency_us_per_sample_median",
                        "p_delta_w", "board_energy_delta_mj_per_sample", "power_valid"] if c in df]
    print(df[cols].round(4).to_string(index=False))
    log(f"Selesai | {out}")
    if not args.check_only and not all(r.get("power_valid") for r in rows):
        log("Ada varian dengan daya tidak valid. Perbaiki FNIRSI lalu jalankan ulang (resume).")
        raise SystemExit(3)


if __name__ == "__main__":
    main()
# ======== END: MAIN ========
