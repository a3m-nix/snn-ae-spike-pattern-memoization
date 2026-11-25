#!/usr/bin/env python3
"""Analisis S7p (DESIGN_S7P_POWER.md §3; Addendum 01–03): ΔE per unit-ronde, aturan dominasi S7g §4, sensitivitas
E_aktif dan idle rendah. Keluaran: 0-revision-results-v2/s7p/RESULTS_S7P_auto.md dan s7p_power_long.csv."""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

R = Path("/home/a3m-nix/snn-ae-final/0-revision-results-v2")
OUT = R / "s7p"
OUT.mkdir(exist_ok=True)
lines = []


def P(s=""):
    print(s); lines.append(s)


# ---------- akurasi 30 unit (server) ----------
a1 = pd.read_csv(R / "s7g/server_accuracy/acc30_long.csv").rename(columns={"f1": "f1_p99"})
a2 = pd.read_csv(R / "s7x_ij/results/accuracy_long.csv").rename(columns={"model": "variant"})
acc = pd.concat([a1[["dataset", "unit", "variant", "auc", "f1_p99"]],
                 a2[a2.variant.isin(["SNN_RQC", "SNN_RQT"])][["dataset", "unit", "variant", "auc", "f1_p99"]]])
acc = acc.groupby(["dataset", "variant"])[["auc", "f1_p99"]].median()
MAP = {"DENSE": "Dense_AE_FP32", "DENSE_ZS": "Dense_AE_FP32", "SNN_COUNT": "SNN_AE_FP32",
       "SNN_MEMOV2_16": "SNN_AE_FP32", "SNN_MEMOV3_16": "SNN_AE_FP32", "SNN_RQC_16": "SNN_RQC", "SNN_RQT_16": "SNN_RQT",
       "DENSE_AQV22_16": "Dense_AQ2", "DENSE_AQV32_16": "Dense_AQ2", "DENSE_AQV23_16": "Dense_AQ3",
       "DENSE_AQV33_16": "Dense_AQ3", "DENSE_Q8": "Dense_AE_Q8", "DENSE_Q8_ZS": "Dense_AE_Q8", "SNN_Q8": "SNN_AE_Q8",
       "SNN_Q8_MEMO_16": "SNN_AE_Q8"}


# ---------- data daya ----------
def load(sub, block, unit=None):
    rows = []
    for f in glob.glob(str(R / sub / "power" / "*.json")):
        d = json.load(open(f))
        rows.append({"block": block, "dataset": d["dataset"], "unit": d.get("unit") or unit, "round": d["round"],
                     "variant": d["variant"], "order": d.get("order") or "capture", "valid": d["power_valid"],
                     "time": d["system"]["time"], "idle_W": d.get("pbus_idle_w"), "infer_W": d.get("pbus_inference_w"),
                     "dE_nJ": d["board_energy_delta_mj_per_sample"] * 1e6,
                     "Eact_nJ": d["board_energy_active_mj_per_sample"] * 1e6,
                     "lat_us": d["latency_us_per_sample_median"], "rate_hz": d.get("fnirsi_rate_hz")})
    return pd.DataFrame(rows)


g0 = load("s7g", "S7g")
g0 = g0[g0.order == "capture"]
gm = load("s7g_more", "S7g-more")
j = load("s7j", "S7j")
h = load("s7h", "S7h", unit="s0_f0")
p = pd.concat([g0, gm, j, h], ignore_index=True)
p["time"] = pd.to_datetime(p["time"])
# cara baca FNIRSI: stream logger tunggal untuk S7g-more dan S7h ciciot2023 (Addendum 03), selain itu pipe langsung
p["reader"] = np.where((p.block == "S7g-more") | ((p.block == "S7h") & (p.dataset == "ciciot2023")), "stream", "pipe")
p.loc[p.block == "S7g", "reader"] = "pipe (29 Okt)"
p.to_csv(OUT / "s7p_power_long.csv", index=False)

P("# Hasil analisis S7p (otomatis)\n")
P(f"Kondisi: {len(p)}; valid: {int(p.valid.sum())}.\n")
P(p.groupby(["block", "dataset", "reader"]).agg(n=("valid", "size"), valid=("valid", "sum"),
                                                idle_med=("idle_W", "median"), idle_min=("idle_W", "min"),
                                                idle_low=("idle_W", lambda s: int((s < 3.6).sum())),
                                                rate_med=("rate_hz", "median")).round(3).to_markdown())


def table(df, title):
    P(f"\n## {title}\n")
    t = df.groupby(["dataset", "variant"]).agg(n=("dE_nJ", "size"), dE_nJ=("dE_nJ", "median"),
                                               Eact_nJ=("Eact_nJ", "median"), lat_us=("lat_us", "median"))
    P(t.round(3).to_markdown())


def dominance(df, ds, snn, dense, metric, emetric="dE_nJ", drop_low=False):
    q = df[df.dataset == ds]
    if drop_low:
        q = q[q.idle_W >= 3.6]
    q = q.pivot_table(index=["unit", "round"], columns="variant", values=emetric)
    pair = q[[snn, dense]].dropna()
    n, k = len(pair), int((pair[snn] < pair[dense]).sum())
    need = int(np.ceil(8 / 9 * n))
    a_s, a_d = acc.loc[(ds, MAP[snn]), metric], acc.loc[(ds, MAP[dense]), metric]
    rel = ("SNN mendominasi" if a_s >= a_d and k >= need else
           "Dense mendominasi" if a_d >= a_s and n - k >= need else "trade-off/tidak tegas")
    return {"snn": snn, "dense": dense, "metric": metric, "acc_snn": round(a_s, 4), "acc_dense": round(a_d, 4),
            "ratio": round(float((pair[snn] / pair[dense]).median()), 3), "snn_cheaper": f"{k}/{n}", "need": need,
            "relation": rel}


def dom_block(df, title, snns, denses):
    P(f"\n## {title}: dominasi (aturan S7g §4)\n")
    for em, dl in [("dE_nJ", False), ("Eact_nJ", False), ("dE_nJ", True)]:
        rows = [dominance(df, ds, s, d, m, em, dl) for ds in ["edge_iiotset", "ciciot2023"] for s in snns
                for d in denses for m in ["auc", "f1_p99"]]
        lab = {("dE_nJ", False): "ΔE (primer)", ("Eact_nJ", False): "E_aktif (sensitivitas)",
               ("dE_nJ", True): "ΔE tanpa idle < 3,6 W (sensitivitas)"}[(em, dl)]
        P(f"\n### {lab}\n")
        t = pd.DataFrame(rows)
        t.insert(0, "dataset", [ds for ds in ["edge_iiotset", "ciciot2023"] for _ in snns for _ in denses for _ in "ab"])
        P(t.to_markdown(index=False))


g9 = pd.concat([g0, gm])
table(g9, "S7g 9 unit (s0–s2 × f0–f2), urutan capture")
dom_block(g9, "S7g 9 unit", ["SNN_MEMOV2_16"], ["DENSE_ZS", "DENSE_AQV22_16", "DENSE_AQV23_16"])
dom_block(gm, "S7g-more saja (6 unit, stream)", ["SNN_MEMOV2_16"], ["DENSE_ZS", "DENSE_AQV22_16", "DENSE_AQV23_16"])
table(j, "S7j (s0–s2_f0)")
dom_block(j, "S7j", ["SNN_MEMOV3_16", "SNN_RQC_16", "SNN_RQT_16"], ["DENSE_ZS", "DENSE_AQV32_16", "DENSE_AQV33_16"])
table(h, "S7h (s0_f0, FP32 + INT8)")

P("\n## Artefak idle rendah: ΔE relatif terhadap median varian (per blok × dataset)\n")
p["rel"] = p.dE_nJ / p.groupby(["block", "dataset", "variant"]).dE_nJ.transform("median")
p["low"] = p.idle_W < 3.6
P(p.groupby(["block", "dataset", "low"]).rel.agg(["size", "median"]).round(3).to_markdown())
P(f"\nKorelasi idle_W vs ΔE relatif (semua): {p[['idle_W', 'rel']].corr().iloc[0, 1]:.2f}")

(OUT / "RESULTS_S7P_auto.md").write_text("\n".join(lines) + "\n")
