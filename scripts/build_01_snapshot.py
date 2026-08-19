"""
build_01_snapshot.py -- option chain snapshot statistics.
L1 REAL. Sources: Deribit book_summary_option_{BTC,ETH}.csv,
Bybit option_tickers_{BTC,ETH,SOL}.json,
OKX okx_option_summary_{BTC,ETH,SOL}.json.
Outputs: results/snapshot_v50.json + tables/tab_snapshot.tex + tab_datasources.tex.
"""
import json, csv, math
from pathlib import Path
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
DATA = BUNDLE.parent / "datawang"
RES = BUNDLE / "results"
TAB = BUNDLE / "tables"
RES.mkdir(exist_ok=True); TAB.mkdir(exist_ok=True)

snapshot = {}

# --- Deribit ---
def parse_deribit(fp):
    rows = []
    with open(fp, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        for r in rd:
            try:
                inst = r["instrument_name"]
                parts = inst.split("-")
                if len(parts) != 4: continue
                ccy, exp, strike, cp = parts
                mark_iv = float(r.get("mark_iv") or 0)
                oi = float(r.get("open_interest") or 0)
                under = float(r.get("underlying_price") or 0)
                bid_iv = r.get("bid_iv") or ""
                ask_iv = r.get("ask_iv") or ""
                rows.append(dict(
                    ccy=ccy, exp=exp, strike=float(strike), cp=cp,
                    mark_iv=mark_iv, oi=oi, spot=under,
                    has_bid=bool(bid_iv and float(bid_iv or 0) > 0),
                    has_ask=bool(ask_iv and float(ask_iv or 0) > 0),
                ))
            except Exception:
                continue
    return rows

for ccy in ("BTC", "ETH"):
    fp = DATA / "raw_deribit" / f"book_summary_option_{ccy}.csv"
    if not fp.exists(): continue
    rows = parse_deribit(fp)
    ivs = [r["mark_iv"] for r in rows if r["mark_iv"] > 0]
    spots = [r["spot"] for r in rows if r["spot"] > 0]
    strikes = sorted(set(r["strike"] for r in rows))
    expiries = sorted(set(r["exp"] for r in rows))
    spot = float(np.median(spots)) if spots else 0
    logm = [math.log(r["strike"]/spot) for r in rows if r["strike"]>0 and spot>0]
    snapshot[f"deribit_{ccy}"] = dict(
        venue="Deribit", ccy=ccy,
        n_instruments=len(rows),
        n_two_way=sum(1 for r in rows if r["has_bid"] and r["has_ask"]),
        n_distinct_strikes=len(strikes),
        n_distinct_expiries=len(expiries),
        iv_median_pct=round(float(np.median(ivs)),2) if ivs else None,
        iv_p05_pct=round(float(np.percentile(ivs,5)),2) if ivs else None,
        iv_p95_pct=round(float(np.percentile(ivs,95)),2) if ivs else None,
        spot_ref=round(spot,2),
        logm_min=round(min(logm),3) if logm else None,
        logm_max=round(max(logm),3) if logm else None,
    )

# --- Bybit ---
for ccy in ("BTC","ETH","SOL"):
    fp = DATA / "raw_bybit" / f"option_tickers_{ccy}.json"
    if not fp.exists(): continue
    j = json.load(open(fp, encoding="utf-8"))
    items = j.get("list", j) if isinstance(j, dict) else j
    snapshot[f"bybit_{ccy}"] = dict(venue="Bybit", ccy=ccy, n_instruments=len(items))

# --- OKX ---
for ccy in ("BTC","ETH","SOL"):
    fp = DATA / "raw_deribit" / f"okx_option_summary_{ccy}.json"
    if not fp.exists(): continue
    j = json.load(open(fp, encoding="utf-8"))
    items = j.get("data", j) if isinstance(j, dict) else j
    snapshot[f"okx_{ccy}"] = dict(venue="OKX", ccy=ccy, n_instruments=len(items))

# --- Write facts ---
(RES / "snapshot_v50.json").write_text(
    json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

# --- tab_snapshot.tex ---
lines = [
    r"\begin{tabular}{@{}llrrrrrr@{}}", r"\toprule",
    r"Venue & Ccy & Inst. & Strikes & Expiries & Med IV (\%) & p05 IV & p95 IV \\",
    r"\midrule",
]
for key in ("deribit_BTC","deribit_ETH"):
    s = snapshot.get(key, {})
    if not s: continue
    lines.append(f"{s['venue']} & {s['ccy']} & {s['n_instruments']} & "
                 f"{s['n_distinct_strikes']} & {s['n_distinct_expiries']} & "
                 f"{s['iv_median_pct']} & {s['iv_p05_pct']} & {s['iv_p95_pct']} \\\\")
for key in ("bybit_BTC","bybit_ETH","bybit_SOL","okx_BTC","okx_ETH","okx_SOL"):
    s = snapshot.get(key, {})
    if not s: continue
    lines.append(f"{s['venue']} & {s['ccy']} & {s['n_instruments']} & "
                 r"--- & --- & --- & --- & --- \\")
lines += [r"\bottomrule", r"\end{tabular}"]
(TAB / "tab_snapshot.tex").write_text("\n".join(lines), encoding="utf-8")

# --- tab_datasources.tex ---
lines = [
    r"\begin{tabular}{@{}llll@{}}", r"\toprule",
    r"Source & Endpoint & Coverage & Level \\",
    r"\midrule",
    r"Deribit REST & option chain, funding & BTC/ETH, 2026-08-07 & L1 \\",
    r"Bybit REST & option tickers, funding & BTC/ETH/SOL, 2026-08-07 & L1 \\",
    r"OKX REST & option summary, tickers & BTC/ETH/SOL, 2026-08-07 & L1 \\",
    r"Binance REST & funding, stable hourly & BTC/ETH/SOL + 4 stables & L1 \\",
    r"CoinGecko & spot daily history & BTC/ETH/SOL/DAI/FDUSD, 1y & L1 \\",
    r"Dune Analytics & DEX daily volume & Ethereum, 2020--2026 & L2 proxy \\",
    r"\bottomrule", r"\end{tabular}",
]
(TAB / "tab_datasources.tex").write_text("\n".join(lines), encoding="utf-8")

# --- Total instrument count for §6 first paragraph ---
n_total = sum(s.get("n_instruments",0) for s in snapshot.values())
print(f"n_total_instruments={n_total}")
print(f"snapshot keys: {list(snapshot.keys())}")
print(f"WROTE {RES/'snapshot_v50.json'}")
print(f"WROTE {TAB/'tab_snapshot.tex'}")
print(f"WROTE {TAB/'tab_datasources.tex'}")
