#!/usr/bin/env python3
"""S7t — one-shot analysis (DESIGN_S7T.md §6). Input: results/<ds>/*_{g1,g2,patterns,timing}.csv.
Output: RESULTS_S7T_auto.md, s7t_summary.csv, s7t_tests.csv (next to this script, under results/)."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
DS = ["edge_iiotset", "ciciot2023"]
TS = [2, 3, 5, 7]


def load(kind):
    return pd.concat([pd.read_csv(f).assign(dataset=ds) for ds in DS for f in sorted((RES / ds).glob(f"*_{kind}.csv"))])


g1, g2, pat, tim = load("g1"), load("g2"), load("patterns"), load("timing")
lines = ["# S7t — automatic analysis", ""]
# gates
g1_ok = bool((g1.dAUC.abs() <= 1e-3).all())
g2_ok = bool(g2.bit_identical.all())
lines += [f"- Units: {g1.groupby('dataset').unit.nunique().to_dict()}",
          f"- G1 max |dAUC| native vs main_results_raw: {g1.dAUC.abs().max():.2e} (pass = {g1_ok})",
          f"- G2 bit-identical: {int(g2.bit_identical.sum())}/{len(g2)} (pass = {g2_ok})", ""]
# Q2 tests: log ratio memo/dense_zs over 30 units, Wilcoxon two-sided, Holm over 8 tests
memo = tim[tim.variant == "SNN_MEMO"].copy()
noc = tim[tim.variant == "SNN_NOCACHE"].set_index(["dataset", "unit", "T"])
rows = []
for ds in DS:
    for T in TS:
        m = memo[(memo.dataset == ds) & (memo["T"] == T)].sort_values("unit")
        lr = np.log(m.ratio_vs_dense_zs.values)
        st = wilcoxon(lr, alternative="two-sided")
        nc = noc.loc[[(ds, u, T) for u in m.unit]]
        rows.append({"dataset": ds, "T": T, "n_units": len(m),
                     "ratio_median": float(np.median(m.ratio_vs_dense_zs)),
                     "ratio_p10": float(np.percentile(m.ratio_vs_dense_zs, 10)),
                     "ratio_p90": float(np.percentile(m.ratio_vs_dense_zs, 90)),
                     "units_faster": int((m.ratio_vs_dense_zs < 1).sum()),
                     "speedup_vs_nocache_median": float(np.median(nc.ns_median.values / m.ns_median.values)),
                     "hit_rate_median": float(np.median(m.hit_rate)), "p_raw": float(st.pvalue)})
tests = pd.DataFrame(rows)
order = np.argsort(tests.p_raw.values)
k = len(tests)
adj = np.empty(k)
run = 0.0
for rank, i in enumerate(order):
    run = max(run, min(1.0, (k - rank) * tests.p_raw.values[i]))
    adj[i] = run
tests["p_holm"] = adj
tests["statement"] = np.where((tests.p_holm < 0.05) & (tests.ratio_median < 1), "memo faster",
                              np.where((tests.p_holm < 0.05) & (tests.ratio_median > 1), "Dense-AE faster",
                                       "not significantly different"))
RES.mkdir(exist_ok=True)
tests.to_csv(RES / "s7t_tests.csv", index=False)
# Q1 descriptive
q1 = pat.groupby(["dataset", "T"]).agg(unique_test=("unique_test", "median"), seen_in_val=("seen_in_val", "median"),
                                      top1000=("top1000_coverage", "median"),
                                      spikes=("spikes_per_sample", "median"), possible=("spikes_possible", "first"),
                                      n_test=("n_test", "median")).reset_index()
acc = g1[g1.model != "Dense_AE"].groupby(["dataset", "T"]).agg(auc=("auc", "median"), f1_p99=("f1_p99", "median"),
                                                                f1_mean=("f1_p99", "mean")).reset_index()
summ = q1.merge(acc, on=["dataset", "T"]).merge(tests, on=["dataset", "T"])
summ.to_csv(RES / "s7t_summary.csv", index=False)


def md(df, cols, fmt="{:.4f}"):
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df[cols].iterrows():
        out.append("| " + " | ".join(fmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in r) + " |")
    return out


lines += ["## Q2 — memo / Dense-AE zero-skip (capture order; Wilcoxon, Holm over 8 tests)", ""]
lines += md(tests, ["dataset", "T", "n_units", "ratio_median", "ratio_p10", "ratio_p90", "units_faster",
                    "speedup_vs_nocache_median", "hit_rate_median", "p_raw", "p_holm", "statement"]) + [""]
lines += ["## Q1 — patterns (median over units) and accuracy context", ""]
lines += md(summ, ["dataset", "T", "unique_test", "n_test", "seen_in_val", "top1000", "spikes", "possible",
                   "auc", "f1_p99", "f1_mean"]) + [""]
(RES / "RESULTS_S7T_auto.md").write_text("\n".join(lines))
print("\n".join(lines))
