"""
build_06_benchmark.py -- tercile RMSE benchmark by |dlog theta|.
L2 PROXY. Uses events_v50.json only.
Outputs: results/benchmark_v50.json + tables/tab_benchmark_summary.tex.
"""
import json, math
from pathlib import Path
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
RES = BUNDLE / "results"; TAB = BUNDLE / "tables"

events = json.load(open(RES/"events_v50.json", encoding="utf-8"))
valid = [e for e in events if math.isfinite(e.get("dlog_theta",float('nan')))
         and math.isfinite(e.get("log_rmse",float('nan')))]

mag = np.array([abs(e["dlog_theta"]) for e in valid])
q_lo, q_hi = float(np.percentile(mag,33)), float(np.percentile(mag,66))

groups = {"low":[], "mid":[], "high":[]}
for e, m in zip(valid, mag):
    if m<=q_lo: groups["low"].append(e)
    elif m>=q_hi: groups["high"].append(e)
    else: groups["mid"].append(e)

results = {}
for name, es in groups.items():
    rmse = np.array([math.exp(e["log_rmse"]) for e in es])
    if len(rmse)==0: continue
    results[name] = dict(
        n=len(es), rmse_mean=float(np.mean(rmse)),
        rmse_median=float(np.median(rmse)), rmse_std=float(np.std(rmse)),
    )

(RES/"benchmark_v50.json").write_text(
    json.dumps(dict(quantiles=dict(q33=q_lo, q66=q_hi), results=results),
               indent=2, ensure_ascii=False), encoding="utf-8")

low_base = results.get("low",{}).get("rmse_median",0) or 1
lines = [
    r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
    r"$|\Delta\!\log\theta|$ tercile & $n$ & Median RMSE proxy (bp) & Mean RMSE proxy (bp) & Relative to low tercile \\",
    r"\midrule",
]
tags = {"low":r"Low ($|\Delta|$ small)", "mid":"Mid", "high":r"High ($|\Delta|$ large)"}
for name in ("low","mid","high"):
    v = results.get(name)
    if not v: continue
    rel = v["rmse_median"]/low_base if low_base>0 else 1
    lines.append(f"{tags[name]} & {v['n']} & {v['rmse_median']:.3f} & "
                 f"{v['rmse_mean']:.3f} & {rel:.3f} \\\\")
lines += [
    r"\midrule",
    r"Ratio high/low & \multicolumn{4}{c}{" +
        f"{results['high']['rmse_median']/low_base:.3f}" + r"} \\",
    r"\bottomrule", r"\end{tabular}",
]
(TAB/"tab_benchmark_summary.tex").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps(results, indent=2))
print(f"WROTE {RES/'benchmark_v50.json'}")
