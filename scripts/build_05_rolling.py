"""
build_05_rolling.py -- rolling-window dispersion proxy.
L1 REAL. 72h window, 24h step. Sources: same funding files as build_03.
Outputs: results/rolling_v50.json + tables/tab_rolling_extended.tex.
"""
import json, math
from pathlib import Path
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
DATA = BUNDLE.parent / "datawang"
RES = BUNDLE / "results"; TAB = BUNDLE / "tables"

W_MS = 72*3600*1000
STEP_MS = 24*3600*1000

def load_series(fp, kind):
    j = json.load(open(fp, encoding="utf-8"))
    if kind=="deribit":
        return sorted([(int(r["timestamp"]), float(r["interest_1h"])) for r in j])
    if kind=="bybit":
        rows = j.get("list", j) if isinstance(j,dict) else j
        return sorted([(int(x["fundingRateTimestamp"]), float(x["fundingRate"])) for x in rows])
    if kind=="binance":
        return sorted([(int(x["fundingTime"]), float(x["fundingRate"])) for x in j])
    return []

sources = []
for ccy in ("BTC","ETH"):
    fp = DATA/"raw_deribit"/f"funding_perp_{ccy}.json"
    if fp.exists(): sources.append((f"deribit_{ccy}", load_series(fp, "deribit")))
for sym in ("BTCUSDT","ETHUSDT","SOLUSDT"):
    fp = DATA/"raw_bybit"/f"funding_history_{sym}.json"
    if fp.exists(): sources.append((f"bybit_{sym.replace('USDT','')}", load_series(fp, "bybit")))
for sym in ("BTCUSDT","ETHUSDT","SOLUSDT"):
    fp = DATA/"raw_binance"/f"funding_{sym}.json"
    if fp.exists(): sources.append((f"binance_{sym.replace('USDT','')}", load_series(fp, "binance")))

rolling = {}
for name, series in sources:
    if len(series)<10: continue
    ts_arr = np.array([s[0] for s in series])
    r_arr = np.array([s[1] for s in series])
    t0, t1 = ts_arr[0], ts_arr[-1]
    wins = []
    t = t0
    while t + W_MS <= t1:
        mask = (ts_arr>=t) & (ts_arr<t+W_MS)
        r_in = r_arr[mask]
        if len(r_in)>=3:
            theta = float(np.std(r_in))
            if theta>0:
                wins.append(dict(ts_start=int(t), n=len(r_in), theta=theta))
        t += STEP_MS
    rolling[name] = wins

# summary
theta_star_ref = 0.26
summary = {}
for name, wins in rolling.items():
    a = np.array([w["theta"] for w in wins if w["theta"]>0])
    if len(a)<5: continue
    la = np.log(a)
    summary[name] = dict(
        n=len(a),
        median=float(np.median(a)), p10=float(np.percentile(a,10)), p90=float(np.percentile(a,90)),
        stationarity_proxy=float(np.std(np.diff(la))/np.std(la)) if np.std(la)>0 else 0.0,
        regime="sticky" if float(np.median(a))<theta_star_ref else "dispersed",
    )

(RES/"rolling_v50.json").write_text(
    json.dumps(dict(rolling=rolling, summary=summary),
               indent=2, ensure_ascii=False), encoding="utf-8")

lines = [
    r"\begin{tabular}{@{}lrrrrrl@{}}", r"\toprule",
    r"Panel & \#Wins & Median $\theta$ & $\theta_{p10}$ & $\theta_{p90}$ & $\sigma(\Delta\!\log\theta)/\sigma(\log\theta)$ & Regime \\",
    r"\midrule",
]
for name in sorted(summary.keys()):
    s = summary[name]
    label = name.replace("_","-").replace("binance","Binance").replace("bybit","Bybit").replace("deribit","Deribit")
    lines.append(
        f"{label} & {s['n']} & {s['median']:.4e} & {s['p10']:.4e} & "
        f"{s['p90']:.4e} & {s['stationarity_proxy']:.2f} & \\emph{{{s['regime']}}} \\\\"
    )
lines += [
    r"\midrule",
    f"Reference threshold $\\theta^{{*}} \\approx {theta_star_ref}$ & \\multicolumn{{6}}{{c}}{{(at $\\delta \\approx 0.07$)}} \\\\",
    r"\bottomrule", r"\end{tabular}",
]
(TAB/"tab_rolling_extended.tex").write_text("\n".join(lines), encoding="utf-8")

total = sum(s["n"] for s in summary.values())
print(f"Total rolling windows: {total}")
for k,v in summary.items(): print(f"  {k}: n={v['n']}, med={v['median']:.4e}, regime={v['regime']}")
print(f"WROTE {RES/'rolling_v50.json'}")
