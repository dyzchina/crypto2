"""
build_07_cross_venue_pool.py -- pool option-quote directions across
Deribit + Bybit + OKX to compute theta_pool.
L1 REAL. Sources: option chain snapshots from all three venues.
Outputs: results/pool_venue_v50.json.

Deribit provides mark_iv + underlying_price directly.
Bybit option_tickers gives markIv + underlyingPrice.
OKX okx_option_tickers gives markVol + last (uses index as under proxy).
For each venue we build (log-moneyness, tenor-normalised, 0) direction
vectors then take the pooled principal-angle multiset.
"""
import json, csv, math
from pathlib import Path
from datetime import datetime
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
DATA = BUNDLE.parent / "datawang"
RES = BUNDLE / "results"

REF = datetime(2026,8,7)

def deribit_dirs(fp, ccy):
    ds = []
    with open(fp, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            try:
                inst = r["instrument_name"].split("-")
                if len(inst)!=4: continue
                _, exp, strike, _ = inst
                strike = float(strike)
                iv = float(r.get("mark_iv") or 0)
                under = float(r.get("underlying_price") or 0)
                if iv<=0 or under<=0 or strike<=0: continue
                exp_dt = datetime.strptime(exp, "%d%b%y")
                dte = (exp_dt-REF).days
                if dte<=0: continue
                k = math.log(strike/under); tau = dte/365.0
                v = np.array([k, tau, 0.0])
                n = np.linalg.norm(v)
                if n>1e-9: ds.append(v/n)
            except Exception: continue
    return ds

def bybit_dirs(fp, ccy):
    ds = []
    try:
        j = json.load(open(fp, encoding="utf-8"))
    except Exception: return ds
    rows = j.get("list", j) if isinstance(j, dict) else j
    for r in rows:
        try:
            sym = r.get("symbol","")
            # BTC-27JUN25-40000-C
            parts = sym.split("-")
            if len(parts)!=4: continue
            _, exp, strike, _ = parts
            strike = float(strike)
            under = float(r.get("underlyingPrice") or r.get("indexPrice") or 0)
            iv = float(r.get("markIv") or 0)
            if iv<=0 or under<=0: continue
            exp_dt = datetime.strptime(exp, "%d%b%y")
            dte = (exp_dt-REF).days
            if dte<=0: continue
            k = math.log(strike/under); tau = dte/365.0
            v = np.array([k, tau, 0.0])
            n = np.linalg.norm(v)
            if n>1e-9: ds.append(v/n)
        except Exception: continue
    return ds

def okx_dirs(fp, ccy):
    ds = []
    try:
        j = json.load(open(fp, encoding="utf-8"))
    except Exception: return ds
    rows = j.get("data", j) if isinstance(j, dict) else j
    for r in rows:
        try:
            sym = r.get("instId","")
            # BTC-USD-250627-45000-C
            parts = sym.split("-")
            if len(parts)!=5: continue
            _, _, exp, strike, _ = parts
            strike = float(strike)
            iv = float(r.get("markVol") or 0)
            under = float(r.get("last") or r.get("markPx") or 0)
            if iv<=0 or under<=0: continue
            exp_dt = datetime.strptime(exp, "%y%m%d")
            dte = (exp_dt-REF).days
            if dte<=0: continue
            k = math.log(strike/under); tau = dte/365.0
            v = np.array([k, tau, 0.0])
            n = np.linalg.norm(v)
            if n>1e-9: ds.append(v/n)
        except Exception: continue
    return ds

def theta_med(dirs):
    if len(dirs)<2: return None, 0
    dirs = sorted(dirs, key=lambda v: v[0])
    angles = []
    for i in range(len(dirs)-1):
        c = float(np.clip(np.dot(dirs[i], dirs[i+1]), -1, 1))
        a = math.acos(abs(c))
        if a>0: angles.append(a)
    if not angles: return None, len(dirs)
    return float(np.median(angles)), len(dirs)

by_venue = {}
by_venue["deribit_BTC"] = deribit_dirs(DATA/"raw_deribit"/"book_summary_option_BTC.csv", "BTC")
by_venue["deribit_ETH"] = deribit_dirs(DATA/"raw_deribit"/"book_summary_option_ETH.csv", "ETH")
for ccy in ("BTC","ETH","SOL"):
    by_venue[f"bybit_{ccy}"] = bybit_dirs(DATA/"raw_bybit"/f"option_tickers_{ccy}.json", ccy)
    by_venue[f"okx_{ccy}"] = okx_dirs(DATA/"raw_deribit"/f"okx_option_tickers_{ccy}.json", ccy)

# per-venue stats
per_venue = {}
for k, dirs in by_venue.items():
    t, n = theta_med(dirs)
    if t is not None:
        per_venue[k] = dict(n=n, theta_med=float(t))

# BTC pool across 3 venues
btc_pool = by_venue["deribit_BTC"] + by_venue["bybit_BTC"] + by_venue["okx_BTC"]
t_btc, n_btc = theta_med(btc_pool)
# ETH pool
eth_pool = by_venue["deribit_ETH"] + by_venue["bybit_ETH"] + by_venue["okx_ETH"]
t_eth, n_eth = theta_med(eth_pool)
# Full pool (BTC+ETH+SOL across 3 venues)
full = []
for v in by_venue.values(): full.extend(v)
t_full, n_full = theta_med(full)

theta_star = 0.26  # from build_02

pool_stats = dict(
    per_venue=per_venue,
    btc_pool=dict(n=n_btc, theta_med=float(t_btc) if t_btc else None,
                  regime="dispersed" if t_btc and t_btc>theta_star else "sticky"),
    eth_pool=dict(n=n_eth, theta_med=float(t_eth) if t_eth else None,
                  regime="dispersed" if t_eth and t_eth>theta_star else "sticky"),
    full_pool=dict(n=n_full, theta_med=float(t_full) if t_full else None,
                   regime="dispersed" if t_full and t_full>theta_star else "sticky"),
    theta_star_ref=theta_star,
)

(RES/"pool_venue_v50.json").write_text(
    json.dumps(pool_stats, indent=2, ensure_ascii=False), encoding="utf-8")

print(json.dumps(pool_stats, indent=2))
print(f"WROTE {RES/'pool_venue_v50.json'}")
