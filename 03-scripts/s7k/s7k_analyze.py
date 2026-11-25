#!/usr/bin/env python3
"""S7k — analisis sekali jalan (DESIGN_S7K.md). Masukan: hasil server (K1) dan hasil Pi (K2–K4).
Keluaran: 0-revision-results-v2/s7k/RESULTS_S7K_auto.md + CSV ringkasan."""
from pathlib import Path

import numpy as np
import pandas as pd

HOME = Path(__file__).resolve().parent.parent
R = HOME / "0-revision-results-v2" / "s7k"
SRV = R / "server" / "results"
XIJ = HOME / "0-revision-results-v2" / "s7x_ij"
DS = ["edge_iiotset", "ciciot2023"]
RNG = np.random.default_rng(42)
lines = ["# S7k — hasil analisis otomatis", ""]


def boot_ci(x, n=10000):
    x = np.asarray(x, float)
    b = np.median(RNG.choice(x, (n, len(x)), replace=True), axis=1)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def table(df, cols=None, fmt="{:.4f}"):
    cols = cols or list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df[cols].iterrows():
        out.append("| " + " | ".join(fmt.format(v) if isinstance(v, (float, np.floating)) else str(v)
                                     for v in r.values) + " |")
    return out


# ------------------------------------------------------------------ K1
lines += ["## K1 — deteksi per jenis serangan (server, 30 unit)", ""]
k1rows, g1 = [], []
for ds in DS:
    sub = pd.concat([pd.read_csv(f) for f in sorted((SRV / ds).glob("*_subtype.csv"))])
    ovr = pd.concat([pd.read_csv(f) for f in sorted((SRV / ds).glob("*_overall.csv"))])
    nunit = sub.unit.nunique()
    # G1: SNN identik dengan S7x-ij; Dense dibandingkan dengan acc30_long (deskriptif, toleransi 1e-3)
    ref = pd.read_csv(XIJ / "results" / "accuracy_long.csv")
    ref = ref[ref.dataset == ds]
    for v, m in [("SNN_EXACT", "SNN_EXACT"), ("SNN_RQC_16", "SNN_RQC"), ("SNN_RQT_16", "SNN_RQT")]:
        a = ovr[ovr.variant == v].set_index("unit"); b = ref[ref.model == m].set_index("unit")
        d_auc = float((a.auc - b.auc).abs().max()); d_f1 = float((a.f1_p99 - b.f1_p99).abs().max())
        g1.append({"dataset": ds, "variant": v, "ref": "S7x-ij accuracy_long", "max_abs_dAUC": d_auc,
                   "max_abs_dF1": d_f1, "pass": d_auc <= 1e-12 and d_f1 <= 1e-12})
    acc30 = pd.read_csv(XIJ / "inputs" / "acc30_long.csv")
    acc30 = acc30[acc30.dataset == ds]
    for v, m in [("DENSE_ZS", "Dense_AE_FP32"), ("DENSE_AQV33_16", "Dense_AQ3"), ("DENSE_AQV32_16", "Dense_AQ2")]:
        a = ovr[ovr.variant == v].set_index("unit"); b = acc30[acc30.variant == m].set_index("unit")
        d_auc = float((a.auc - b.auc).abs().max()); d_f1 = float((a.f1_p99 - b.f1).abs().max())
        g1.append({"dataset": ds, "variant": v, "ref": "acc30_long (deskriptif)", "max_abs_dAUC": d_auc,
                   "max_abs_dF1": d_f1, "pass": d_auc <= 1e-3 and d_f1 <= 1e-3})
    piv = sub.pivot_table(index=["unit", "subtype"], columns="variant", values="positive_rate")
    chg = sub.pivot_table(index=["unit", "subtype"], columns="variant", values="decision_change_rate")
    auc = sub.pivot_table(index=["unit", "subtype"], columns="variant", values="auc_vs_normal")
    for v in sub.variant.unique():
        base = sub[sub.variant == v].base.iloc[0]
        for s in sorted(sub.subtype.unique()):
            x = piv.xs(s, level="subtype")
            d = (x[v] - x[base]).values
            base_med = float(np.median(x[base]))
            r = {"dataset": ds, "variant": v, "base": base, "subtype": s, "units": nunit,
                 "rate_median": float(np.median(x[v])), "base_median": base_med,
                 "delta_median": float(np.median(d)), "n_units_drop_gt_0.05": int((d < -0.05).sum()),
                 "n_units_rise_gt_0.05": int((d > 0.05).sum()),
                 "decision_change_median": float(np.median(chg.xs(s, level="subtype")[v]))}
            r["delta_ci_lo"], r["delta_ci_hi"] = boot_ci(d) if v != base else (0.0, 0.0)
            if s != "normal":
                r["auc_vs_normal_median"] = float(np.median(auc.xs(s, level="subtype")[v]))
            if s == "normal":
                r["flag"] = "FPR"
            elif base_med < 0.20:
                r["flag"] = "lantai"
            elif r["delta_median"] < -0.05 and r["n_units_drop_gt_0.05"] >= 24:
                r["flag"] = "turun konsisten"
            elif r["delta_median"] > 0.05 and r["n_units_rise_gt_0.05"] >= 24:
                r["flag"] = "naik konsisten"
            else:
                r["flag"] = "–"
            k1rows.append(r)
K1 = pd.DataFrame(k1rows)
K1.to_csv(R / "k1_subtype_summary.csv", index=False)
G1 = pd.DataFrame(g1)
G1.to_csv(R / "g1_check.csv", index=False)
lines += ["### Gerbang G1", ""] + table(G1, fmt="{:.2e}") + [""]
for ds in DS:
    lines += [f"### {ds}: recall per subtipe (median 30 unit; Δ terhadap model dasar)", ""]
    k = K1[(K1.dataset == ds) & (K1.variant != K1.base)].copy()
    k["Δ [CI95]"] = k.apply(lambda r: f"{r.delta_median:+.3f} [{r.delta_ci_lo:+.3f}; {r.delta_ci_hi:+.3f}]", axis=1)
    lines += table(k, ["variant", "subtype", "base_median", "rate_median", "Δ [CI95]", "n_units_drop_gt_0.05",
                       "decision_change_median", "flag"], fmt="{:.3f}") + [""]

# ------------------------------------------------------------------ K2–K4 (Pi)
for name, pat, keys in [("K2 pola kunci", "k2_keys_{}.csv", ["key"]),
                        ("K3 PMU", "k3_pmu_{}.csv", ["variant"]),
                        ("K4 kapasitas", "k4_capacity_{}.csv", ["variant"])]:
    lines += [f"## {name} (Pi, median 3 unit)", ""]
    for ds in DS:
        f = R / pat.format(ds)
        if not f.exists():
            lines += [f"{ds}: berkas tidak ada", ""]
            continue
        d = pd.read_csv(f)
        num = [c for c in d.columns if d[c].dtype.kind == "f" and c not in ("freq_mhz", "temp_c")]
        g = d.groupby(keys)[num].median().reset_index()
        g.to_csv(R / f"summary_{pat.split('_{}')[0]}_{ds}.csv", index=False)
        lines += [f"### {ds}", ""] + table(g, keys + [c for c in num if not c.endswith("_kernel")][:10], "{:.3f}") + [""]
for ds in DS:
    f = R / f"k2_class_{ds}.csv"
    if f.exists():
        d = pd.read_csv(f)
        lines += [f"## K2 per kelas trafik, s0_f0 ({ds})", ""]
        lines += table(d[d.variant.isin(["DENSE_ZS", "SNN_MEMOV3_16", "SNN_RQT_16", "DENSE_AQV33_16"])],
                       ["class", "n", "variant", "ns_median", "hit_rate", "spikes_enc_per_sample", "exact_unique_test",
                        "exact_test_seen_in_val"], "{:.3f}") + [""]
    f = R / f"k4_memory_{ds}.csv"
    if f.exists():
        lines += [f"## K4 memori, s0_f0 ({ds})", ""] + table(pd.read_csv(f), fmt="{:.0f}") + [""]
(R / "RESULTS_S7K_auto.md").write_text("\n".join(lines))
print("ok:", R / "RESULTS_S7K_auto.md", "| G1 pass:", bool(G1["pass"].all()))
