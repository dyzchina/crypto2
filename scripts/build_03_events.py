"""
build_03_events.py -- sign-flip event identification.
L1 REAL. Sources: funding_perp_{BTC,ETH}.json (Deribit),
                  funding_history_{BTCUSDT,ETHUSDT,SOLUSDT}.json (Bybit),
                  funding_{BTCUSDT,ETHUSDT,SOLUSDT}.json (Binance).
Rule: sign-flip after >= min_run same-sign obs, min_gap_ms cooldown.
Outputs: results/events_v50.json + tables/tab_events_summary.tex +
         tables/tab_funding.tex + tables/tab_stable.tex.
"""
import json, math
from pathlib import Path
from datetime import datetime, timezone
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
DATA = BUNDLE.parent / "datawang"
RES = BUNDLE / "results"
TAB = BUNDLE / "tables"

MIN_RUN = 6
COOLDOWN_MS = 48 * 3600 * 1000

def load_deribit(fp):
    j = json.load(open(fp, encoding="utf-8"))
    return [(int(r["timestamp"]), float(r["interest_1h"])) for r in j if "interest_1h" in r]

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
            ts = int(x.get("fundingTime", 0))
            r = float(x.get("fundingRate", 0))
            out.append((ts, r))
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

def detect(series):
    """series = [(ts_ms, rate)] sorted."""
    events = []
    if len(series)<MIN_RUN+2: return events
    ts_arr = [s[0] for s in series]
    r_arr = [s[1] for s in series]
    last_evt = -1
    i = MIN_RUN
    while i < len(series):
        pre = r_arr[i-MIN_RUN:i]
        post = r_arr[i]
        sign_pre = 1 if all(p>0 for p in pre) else (-1 if all(p<0 for p in pre) else 0)
        if sign_pre==0: i+=1; continue
        sign_post = 1 if post>0 else (-1 if post<0 else 0)
        if sign_post==0 or sign_post==sign_pre: i+=1; continue
        if last_evt>=0 and ts_arr[i]-ts_arr[last_evt] < COOLDOWN_MS: i+=1; continue
        # window
        window = 24*3600*1000
        pre_win = [r for (t,r) in series if ts_arr[i]-window <= t < ts_arr[i]]
        post_win = [r for (t,r) in series if ts_arr[i] <= t <= ts_arr[i]+window]
        if len(pre_win)<3 or len(post_win)<3: i+=1; continue
        theta_pre = float(np.std(pre_win)) or 1e-9
        theta_post = float(np.std(post_win)) or 1e-9
        rate_pre = float(np.mean(pre_win))
        rate_post = float(np.mean(post_win))
        rmse = abs(rate_post - rate_pre) * 1e4  # bp
        if rmse<=0: i+=1; continue
        events.append(dict(
            ts_ms=ts_arr[i],
            iso=datetime.fromtimestamp(ts_arr[i]/1000, tz=timezone.utc).isoformat(),
            run_len_pre=MIN_RUN, sign_pre=sign_pre,
            rate_pre_bp=round(rate_pre*1e4,4),
            rate_post_bp=round(rate_post*1e4,4),
            theta_pre_proxy=theta_pre, theta_post_proxy=theta_post,
            dlog_theta=math.log(theta_post/theta_pre),
            rmse_proxy_bp=round(rmse,4),
            log_rmse=math.log(rmse),
        ))
        last_evt = i
        i += 1
    return events

all_events = []
per_source = {}
for name, series in sources:
    es = detect(series)
    for e in es: e["venue_ccy"] = name
    all_events.extend(es)
    per_source[name] = dict(n_obs=len(series), n_events=len(es))

# drop those with degenerate windows
valid = [e for e in all_events if e.get("dlog_theta") is not None and math.isfinite(e["dlog_theta"])]

(RES / "events_v50.json").write_text(
    json.dumps(valid, indent=2, ensure_ascii=False), encoding="utf-8")

# --- tab_events_summary.tex ---
by_src = {}
for e in valid:
    by_src.setdefault(e["venue_ccy"], []).append(e)
lines = [
    r"\begin{tabular}{@{}lrrr@{}}", r"\toprule",
    r"Panel & $n_{\rm events}$ & Mean $|\Delta\!\log\theta|$ & Median $|\Delta\!\log\theta|$ \\",
    r"\midrule",
]
for name in sorted(by_src.keys()):
    es = by_src[name]
    d = [abs(e["dlog_theta"]) for e in es]
    label = name.replace("_","-").replace("binance","Binance").replace("bybit","Bybit").replace("deribit","Deribit")
    lines.append(f"{label} & {len(es)} & {np.mean(d):.3f} & {np.median(d):.3f} \\\\")
lines += [r"\midrule", f"Total & {len(valid)} & --- & --- \\\\", r"\bottomrule", r"\end{tabular}"]
(TAB / "tab_events_summary.tex").write_text("\n".join(lines), encoding="utf-8")

# --- tab_funding.tex ---
funding_stats = {}
for name, series in sources:
    rates = [r for _,r in series]
    if rates:
        funding_stats[name] = dict(
            n=len(rates),
            mean_bp=float(np.mean(rates))*1e4,
            std_bp=float(np.std(rates))*1e4,
            abs_max_bp=max(abs(x) for x in rates)*1e4,
        )
lines = [
    r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
    r"Panel & $n_{\rm obs}$ & Mean (bp) & Std (bp) & $|\!\max\!|$ (bp) \\",
    r"\midrule",
]
for name, s in sorted(funding_stats.items()):
    label = name.replace("_","-").replace("binance","Binance").replace("bybit","Bybit").replace("deribit","Deribit")
    lines.append(f"{label} & {s['n']} & {s['mean_bp']:.3f} & {s['std_bp']:.3f} & {s['abs_max_bp']:.3f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
(TAB / "tab_funding.tex").write_text("\n".join(lines), encoding="utf-8")

# --- Stablecoin table ---
stable_stats = {}
for sym in ("USDC","DAI","FDUSD","TUSD"):
    fp = DATA/"raw_binance"/f"stable_hourly_{sym}USDT.json"
    if not fp.exists(): continue
    j = json.load(open(fp, encoding="utf-8"))
    closes = [float(k[4]) for k in j]  # kline close
    if not closes: continue
    devs = [(c-1.0)*1e4 for c in closes]  # bp deviation
    stable_stats[sym] = dict(
        n=len(closes),
        mean_bp_dev=float(np.mean(devs)),
        std_bp_dev=float(np.std(devs)),
        abs_max_bp=float(max(abs(d) for d in devs)),
    )
lines = [
    r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
    r"Stable/USDT & $n_{\rm hrs}$ & Mean dev (bp) & Std dev (bp) & $|\!\max\!|$ (bp) \\",
    r"\midrule",
]
for sym, s in sorted(stable_stats.items()):
    lines.append(f"{sym} & {s['n']} & {s['mean_bp_dev']:.2f} & {s['std_bp_dev']:.2f} & {s['abs_max_bp']:.2f} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
(TAB / "tab_stable.tex").write_text("\n".join(lines), encoding="utf-8")

# --- also emit a facts stub ---
(RES / "funding_facts_v50.json").write_text(
    json.dumps(dict(funding=funding_stats, stable=stable_stats, per_source=per_source),
               indent=2, ensure_ascii=False), encoding="utf-8")

print(f"TOTAL EVENTS (valid): {len(valid)}")
print(f"per source:")
for k,v in per_source.items(): print(f"  {k}: n_obs={v['n_obs']}, n_events={v['n_events']}")
print(f"WROTE {RES/'events_v50.json'}")
