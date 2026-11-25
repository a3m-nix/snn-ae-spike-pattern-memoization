#!/usr/bin/env python3
# ======== START: HEADER ========
"""
S7x-ij ANALISIS (server) — sesuai DESIGN.md bagian 3 dan 5 (tanpa model, tanpa TF).
Input : results/{check,accuracy,timing}/<ds>/<unit>_*.csv, inputs/acc30_long.csv
Output: results/accuracy_delta.csv, accuracy_long.csv, crosscheck_acc30.csv, stats_primary.csv, stats_secondary.csv,
        descriptive.csv, timing_long.csv, check_long.csv, RESULTS_auto.md
d = t_Dense − t_SNN (positif = SNN lebih cepat); rasio r = t_SNN / t_Dense (< 1 = SNN lebih cepat).
Jalankan: /home/jupyteruser/jupyter_env/bin/python -I analyze_s7x_ij.py
"""
# ======== END: HEADER ========

# ======== START: IMPORT + KONFIGURASI ========
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, wilcoxon

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
DATASETS = ["edge_iiotset", "ciciot2023"]
ORDERS = ["capture", "random"]
SNNS = ["SNN_MEMOV3_16", "SNN_RQC_16", "SNN_RQT_16"]
DENSES = ["DENSE_ZS", "DENSE_AQV32_16", "DENSE_AQV33_16"]
N_BOOT, SEED, ALPHA = 10_000, 42, 0.05
TH_AUC, TH_F1 = -0.005, -0.01
PI = {"edge_iiotset": {"DENSE_AQV32_16": 0.403, "DENSE_AQV33_16": 0.474, "SNN_MEMOV3_16": 0.465,
                       "SNN_RQC_16": 0.417, "SNN_RQT_16": 0.377},
      "ciciot2023": {"DENSE_AQV32_16": 0.433, "DENSE_AQV33_16": 0.501, "SNN_MEMOV3_16": 0.412,
                     "SNN_RQC_16": 0.383, "SNN_RQT_16": 0.368}}          # RESULTS_S7I_S7J.md, 3 unit, capture
# ======== END: IMPORT + KONFIGURASI ========


# ======== START: STATISTIK ========
def holm(p):
    p = np.asarray(p, float)
    adj, run = np.empty_like(p), 0.0
    for r, i in enumerate(np.argsort(p)):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def rank_biserial(d):
    d = d[d != 0]
    if not len(d):
        return 0.0
    r = rankdata(np.abs(d))
    return float((r[d > 0].sum() - r[d < 0].sum()) / r.sum())


def boot_median(x):
    rng = np.random.RandomState(SEED)
    b = np.median(x[rng.randint(0, len(x), size=(N_BOOT, len(x)))], axis=1)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def wil(d):
    return float(wilcoxon(d, zero_method="wilcox", alternative="two-sided").pvalue) if np.any(d != 0) else 1.0


def paired(T, ds, order, a, b):
    """a = varian yang diuji (SNN), b = pembanding; rasio a/b."""
    g = T[(T.dataset == ds) & (T.order == order) & T.variant.isin([a, b])]
    w = g.pivot(index="unit", columns="variant", values="ns_per_sample_median").dropna()
    d = (w[b] - w[a]).to_numpy()
    ratio = (w[a] / w[b]).to_numpy()
    lo, hi = boot_median(ratio)
    return {"dataset": ds, "order": order, "variant": a, "comparator": b, "n_units": int(len(d)),
            "median_ns_variant": float(w[a].median()), "median_ns_comparator": float(w[b].median()),
            "median_ratio": float(np.median(ratio)), "ratio_ci95_low": lo, "ratio_ci95_high": hi,
            "min_ratio": float(ratio.min()), "max_ratio": float(ratio.max()),
            "units_variant_faster": int(np.sum(d > 0)), "rank_biserial_r": rank_biserial(d), "p": wil(d)}


def family(rows, faster, slower):
    S = pd.DataFrame(rows)
    S["p_holm"] = holm(S.p)
    S["verdict"] = np.where(S.p_holm >= ALPHA, "tidak terbukti berbeda",
                            np.where(S.median_ratio < 1, faster, slower))
    return S
# ======== END: STATISTIK ========


# ======== START: AKURASI ========
def accuracy(A):
    rows = []
    for ds in DATASETS:
        ex = A[(A.dataset == ds) & (A.model == "SNN_EXACT")].set_index("unit")
        for m in ["SNN_RQC", "SNN_RQT"]:
            rq = A[(A.dataset == ds) & (A.model == m)].set_index("unit").loc[ex.index]
            r = {"dataset": ds, "model": m, "n_units": len(ex)}
            for met in ["auc", "f1_p99", "ap", "recall_at_fpr_0.01"]:
                d = (rq[met] - ex[met]).to_numpy()
                lo, hi = boot_median(d)
                r.update({f"d_{met}_median": float(np.median(d)), f"d_{met}_ci95_low": lo, f"d_{met}_ci95_high": hi,
                          f"d_{met}_min": float(d.min()), f"d_{met}_p10": float(np.percentile(d, 10)),
                          f"d_{met}_p25": float(np.percentile(d, 25)), f"d_{met}_p75": float(np.percentile(d, 75)),
                          f"d_{met}_max": float(d.max()), f"d_{met}_wilcoxon_p": wil(d)})
            dauc, df1 = (rq.auc - ex.auc), (rq.f1_p99 - ex.f1_p99)
            r["units_dauc_below_-0.005"] = int((dauc < TH_AUC).sum())
            r["units_df1_below_-0.01"] = int((df1 < TH_F1).sum())
            r["worst_unit_df1"] = str(df1.idxmin())
            r["worst_df1"] = float(df1.min())
            r["worst_unit_dauc"] = str(dauc.idxmin())
            r["worst_dauc"] = float(dauc.min())
            r["median_auc_exact"], r["median_auc_rq"] = float(ex.auc.median()), float(rq.auc.median())
            r["median_f1_exact"], r["median_f1_rq"] = float(ex.f1_p99.median()), float(rq.f1_p99.median())
            ok = r["d_auc_median"] >= TH_AUC and r["d_f1_p99_median"] >= TH_F1
            robust = ok and r["d_auc_ci95_low"] >= TH_AUC and r["d_f1_p99_ci95_low"] >= TH_F1
            r["feasible"] = bool(ok)
            r["verdict"] = "layak kokoh" if robust else ("layak (tidak kokoh)" if ok else "tidak layak")
            rows.append(r)
    return pd.DataFrame(rows)


def crosscheck(A):
    k = pd.read_csv(HERE / "inputs" / "acc30_long.csv")
    k = k[k.variant == "SNN_AE_FP32"][["dataset", "unit", "auc", "f1"]]
    e = A[A.model == "SNN_EXACT"][["dataset", "unit", "auc", "f1_p99"]]
    m = e.merge(k, on=["dataset", "unit"], suffixes=("_kernel", "_keras"))
    m["d_auc"], m["d_f1"] = m.auc_kernel - m.auc_keras, m.f1_p99 - m.f1
    return m
# ======== END: AKURASI ========


# ======== START: MAIN ========
def load(phase, suffix):
    return pd.concat([pd.read_csv(p) for ds in DATASETS
                      for p in sorted((RES / phase / ds).glob(f"*_{suffix}.csv"))], ignore_index=True)


def main():
    C, A, T = load("check", "check"), load("accuracy", "accuracy"), load("timing", "timing")
    for name, df in (("check", C), ("accuracy", A), ("timing", T)):
        for ds in DATASETS:
            n = df[df.dataset == ds].unit.nunique()
            if n != 30:
                raise SystemExit(f"{name} {ds}: {n} unit, bukan 30")
    correct = bool(C.err_bit_identical.all() and C.stats_identical.all())
    if not correct:
        raise SystemExit("check tidak lolos semua — analisis dihentikan")
    D_acc = accuracy(A)
    X = crosscheck(A)
    feas = {(r.dataset, r.model + "_16"): r.feasible for r in D_acc.itertuples()}
    S1 = family([paired(T, ds, o, s, c) for ds in DATASETS for o in ORDERS for s in SNNS for c in DENSES],
                "SNN lebih cepat", "Dense lebih cepat")
    S1["accuracy_feasible"] = [feas.get((r.dataset, r.variant), True) for r in S1.itertuples()]
    S1["efficiency_claim_allowed"] = S1.accuracy_feasible & (S1.verdict == "SNN lebih cepat")
    S2 = family([paired(T, ds, o, s, "SNN_MEMOV3_16") for ds in DATASETS for o in ORDERS
                 for s in ["SNN_RQC_16", "SNN_RQT_16"]], "RQ lebih cepat", "MEMOV3 lebih cepat")
    base = T[T.variant == "DENSE_ZS"][["dataset", "unit", "order", "ns_per_sample_median"]].rename(
        columns={"ns_per_sample_median": "ns_dense_zs"})
    T = T.merge(base, on=["dataset", "unit", "order"])
    T["ratio_vs_dense_zs"] = T.ns_per_sample_median / T.ns_dense_zs
    T["spread_p90_p10_rel"] = (T.ns_per_sample_p90 - T.ns_per_sample_p10) / T.ns_per_sample_median
    D = (T.groupby(["dataset", "order", "variant"])
         .agg(median_ns=("ns_per_sample_median", "median"), median_ratio_vs_dense_zs=("ratio_vs_dense_zs", "median"),
              min_ratio=("ratio_vs_dense_zs", "min"), max_ratio=("ratio_vs_dense_zs", "max"),
              median_hit_rate=("hit_rate", "median"), median_rel_spread=("spread_p90_p10_rel", "median"),
              max_loadavg=("loadavg_1m", "max")).reset_index())
    D["pi_ratio_vs_dense_zs"] = [PI[r.dataset].get(r.variant) if r.order == "capture" else np.nan
                                 for r in D.itertuples()]
    for name, df in [("accuracy_delta", D_acc), ("accuracy_long", A), ("crosscheck_acc30", X),
                     ("stats_primary", S1), ("stats_secondary", S2), ("descriptive", D),
                     ("timing_long", T), ("check_long", C)]:
        df.to_csv(RES / f"{name}.csv", index=False)
    acols = ["dataset", "model", "median_auc_exact", "median_auc_rq", "d_auc_median", "d_auc_ci95_low", "d_auc_min",
             "median_f1_exact", "median_f1_rq", "d_f1_p99_median", "d_f1_p99_ci95_low", "d_f1_p99_p10", "d_f1_p99_min",
             "units_dauc_below_-0.005", "units_df1_below_-0.01", "worst_unit_df1", "verdict"]
    scols = ["dataset", "order", "variant", "comparator", "median_ratio", "ratio_ci95_low", "ratio_ci95_high",
             "units_variant_faster", "rank_biserial_r", "p_holm", "verdict"]
    md = ["## Bagian otomatis (analyze_s7x_ij.py)", "",
          f"**Kebenaran:** check {len(C)} kombinasi pada 60 unit lolos semua: **{correct}**", "",
          "### Akurasi RQ vs SNN eksak (Δ = RQ − eksak, per unit, n = 30)", "",
          D_acc[acols].to_markdown(index=False, floatfmt=".4g"), "",
          "Cek silang SNN_EXACT (kernel) vs acc30 SNN_AE_FP32 (Keras): median |ΔAUC| "
          + ", ".join(f"{ds} {X[X.dataset == ds].d_auc.abs().median():.2e}" for ds in DATASETS)
          + "; median |ΔF1| " + ", ".join(f"{ds} {X[X.dataset == ds].d_f1.abs().median():.2e}" for ds in DATASETS), "",
          "### Latensi — famili primer (SNN vs Dense; Holm atas 36)", "",
          S1[scols + ["accuracy_feasible"]].to_markdown(index=False, floatfmt=".4g"), "",
          "### Latensi — famili sekunder (RQ vs MEMOV3; Holm atas 8)", "",
          S2[scols].to_markdown(index=False, floatfmt=".4g"), "",
          "### Deskriptif (median per unit; rasio terhadap DENSE_ZS; kolom Pi = S7i/S7j, 3 unit, capture)", "",
          D.to_markdown(index=False, floatfmt=".4g"), ""]
    (RES / "RESULTS_auto.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
# ======== END: MAIN ========
