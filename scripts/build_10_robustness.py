"""
build_10_robustness.py -- RR-3: robustness of beta_FE across
(MIN_RUN, cooldown) grid. Verifies sign stability.
Grid: MIN_RUN in {4,6,8,10} x cooldown in {24h,48h,96h} = 12 specs.
Outputs: results/robustness_v50.json + tables/tab_robustness.tex.
"""
import json, math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
DATA = BUNDLE.parent / "datawang"
RES = BUNDLE / "results"; TAB = BUNDLE / "tables"

def load_deribit(fp):
    j = json.load(open(fp, encoding="utf-8"))
    return sorted([(int(r["timestamp"]), float(r["interest_1h"])) for r in j if "interest_1h" in r])

def load_bybit(fp):
    j = json.load(open(fp, encoding="utf-8"))
    rows = j.get("list", j) if isinstance(j, dict) else j
    out = []
    for x in rows:
        try:
            ts = int(x.get("fundingRateTimestamp", 0))
            r = float(x.get("fundingRate", 0))
            out.append((ts, r))
        except Exception: continue
    return sorted(out)

def load_binance(fp):
    j = json.load(open(fp, encoding="utf-8"))
    out = []
    for x in j:
        try:
            out.append((int(x.get("fundingTime", 0)), float(x.get("fundingRate", 0))))
        except Exception: continue
    return sorted(out)

sources = []
for ccy in ("BTC","ETH"):
    fp = DATA/"raw_deribit"/f"funding_perp_{ccy}.json"
    if fp.exists(): sources.append((f"deribit_{ccy}", load_deribit(fp)))
for sym in ("BTCUSDT","ETHUSDT","SOLUSDT"):
    fp = DATA/"raw_bybit"/f"funding_history_{sym}.json"
    if fp.exists(): sources.append((f"bybit_{sym.replace('USDT','')}", load_bybit(fp)))
for sym in ("BTCUSDT","ETHUSDT","SOLUSDT"):
    fp = DATA/"raw_binance"/f"funding_{sym}.json"
    if fp.exists(): sources.append((f"binance_{sym.replace('USDT','')}", load_binance(fp)))

def detect(series, min_run, cooldown_ms):
    events = []
    if len(series) < min_run + 2: return events
    ts_arr = [s[0] for s in series]
    r_arr = [s[1] for s in series]
    last_evt = -1
    i = min_run
    while i < len(series):
        pre = r_arr[i-min_run:i]
        post = r_arr[i]
        sign_pre = 1 if all(p>0 for p in pre) else (-1 if all(p<0 for p in pre) else 0)
        if sign_pre == 0: i += 1; continue
        sign_post = 1 if post>0 else (-1 if post<0 else 0)
        if sign_post == 0 or sign_post == sign_pre: i += 1; continue
        if last_evt >= 0 and ts_arr[i] - ts_arr[last_evt] < cooldown_ms: i += 1; continue
        window = 24*3600*1000
        pre_win = [r for (t,r) in series if ts_arr[i]-window <= t < ts_arr[i]]
        post_win = [r for (t,r) in series if ts_arr[i] <= t <= ts_arr[i]+window]
        if len(pre_win) < 3 or len(post_win) < 3: i += 1; continue
        theta_pre = float(np.std(pre_win)) or 1e-9
        theta_post = float(np.std(post_win)) or 1e-9
        rmse = abs(float(np.mean(post_win)) - float(np.mean(pre_win))) * 1e4
        if rmse <= 0: i += 1; continue
        events.append(dict(
            venue_ccy=None,
            dlog_theta=math.log(theta_post/theta_pre),
            log_rmse=math.log(rmse),
        ))
        last_evt = i
        i += 1
    return events

def fit(events):
    E = [e for e in events if math.isfinite(e["dlog_theta"]) and math.isfinite(e["log_rmse"])]
    n = len(E)
    if n < 10: return None
    x = np.array([e["dlog_theta"] for e in E])
    y = np.array([e["log_rmse"] for e in E])
    venues = sorted(set(e["venue_ccy"] for e in E))
    D = np.zeros((n, len(venues)))
    for i,e in enumerate(E):
        D[i, venues.index(e["venue_ccy"])] = 1.0
    Xfe = np.column_stack([D, x])
    beta_fe = np.linalg.lstsq(Xfe, y, rcond=None)[0][-1]
    Xols = np.column_stack([np.ones(n), x])
    beta_ols = np.linalg.lstsq(Xols, y, rcond=None)[0][1]
    # block bootstrap CI FE
    rng = np.random.default_rng(20260814)
    B, BLOCK = 1000, 3
    bfe = np.empty(B)
    n_blocks = int(np.ceil(n/BLOCK))
    for b in range(B):
        starts = rng.integers(0, max(1, n-BLOCK+1), size=n_blocks)
        idx = np.concatenate([np.arange(s, s+BLOCK) for s in starts])[:n]
        Db = D[idx]
        Xfb = np.column_stack([Db, x[idx]])
        bfe[b] = np.linalg.lstsq(Xfb, y[idx], rcond=None)[0][-1]
    return dict(
        n=n, beta_ols=float(beta_ols), beta_fe=float(beta_fe),
        ci_fe_lo=float(np.percentile(bfe, 2.5)),
        ci_fe_hi=float(np.percentile(bfe, 97.5)),
    )

GRID_RUN = [4, 6, 8, 10]
GRID_CD = [24, 48, 96]
grid = {}
for mr in GRID_RUN:
    for cd_h in GRID_CD:
        all_e = []
        for name, series in sources:
            for e in detect(series, mr, cd_h*3600*1000):
                e["venue_ccy"] = name
                all_e.append(e)
        r = fit(all_e)
        if r:
            r["min_run"] = mr; r["cooldown_h"] = cd_h
            grid[f"mr{mr}_cd{cd_h}"] = r

(RES/"robustness_v50.json").write_text(
    json.dumps(grid, indent=2, ensure_ascii=False), encoding="utf-8")

# Table: rows = MIN_RUN, cols = cooldown; cells = n, beta_FE (CI)
lines = [
    r"\begin{tabular}{@{}lccc@{}}", r"\toprule",
    r"MIN\_RUN $\backslash$ cooldown & 24h & 48h & 96h \\",
    r"\midrule",
]
for mr in GRID_RUN:
    cells = []
    for cd in GRID_CD:
        r = grid.get(f"mr{mr}_cd{cd}")
        if r:
            cells.append(f"$n={r['n']}$; $\\hat\\beta_{{\\rm FE}}={r['beta_fe']:.3f}$ [{r['ci_fe_lo']:.2f}, {r['ci_fe_hi']:.2f}]")
        else:
            cells.append("---")
    lines.append(f"MIN\\_RUN$={mr}$ & " + " & ".join(cells) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
(TAB/"tab_robustness.tex").write_text("\n".join(lines), encoding="utf-8")

# Sign stability check
signs_neg = sum(1 for r in grid.values() if r["beta_fe"] < 0)
sig_neg = sum(1 for r in grid.values() if r["ci_fe_hi"] < 0)
print(f"12 specifications: {signs_neg} with beta_FE < 0, {sig_neg} with 95% CI upper bound < 0")
for k, r in grid.items():
    print(f"  {k}: n={r['n']}, beta_FE={r['beta_fe']:.3f}, CI=[{r['ci_fe_lo']:.2f},{r['ci_fe_hi']:.2f}]")
print(f"WROTE {RES/'robustness_v50.json'}")
