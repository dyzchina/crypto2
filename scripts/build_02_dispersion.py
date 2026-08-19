"""
build_02_dispersion.py -- single-venue directional-dispersion angle theta.
L1 REAL. Source: datawang/raw_deribit/book_summary_option_{BTC,ETH}.csv.
Outputs: results/dispersion_v50.json + tables/tab_dispersion.tex +
         tables/tab_dispersion_sensitivity.tex.
"""
import json, csv, math
from pathlib import Path
from datetime import datetime
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
DATA = BUNDLE.parent / "datawang"
RES = BUNDLE / "results"
TAB = BUNDLE / "tables"

def parse(fp):
    rows = []
    with open(fp, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            try:
                inst = r["instrument_name"].split("-")
                if len(inst)!=4: continue
                _, exp, strike, _ = inst
                mark_iv = float(r.get("mark_iv") or 0)
                under = float(r.get("underlying_price") or 0)
                if mark_iv<=0 or under<=0: continue
                rows.append(dict(exp=exp, strike=float(strike),
                                 iv=mark_iv, spot=under))
            except Exception: continue
    return rows

def dirs_from_rows(rows, ref_date=datetime(2026,8,7)):
    ds = []
    for r in rows:
        try:
            exp_dt = datetime.strptime(r["exp"], "%d%b%y")
        except Exception: continue
        dte = (exp_dt - ref_date).days
        if dte<=0 or r["spot"]<=0: continue
        k = math.log(r["strike"]/r["spot"])
        tau = dte/365.0
        v = np.array([k, tau, 0.0])
        n = np.linalg.norm(v)
        if n>1e-9: ds.append(v/n)
    return ds

def theta_stats(dirs):
    if len(dirs)<2: return None
    dirs = sorted(dirs, key=lambda v: v[0])
    angles = []
    for i in range(len(dirs)-1):
        c = float(np.clip(np.dot(dirs[i], dirs[i+1]), -1, 1))
        angles.append(math.acos(abs(c)))
    a = np.array(angles)
    a = a[a>0]
    return dict(
        n_pairs=len(a),
        theta_min=float(a.min()),
        theta_med=float(np.median(a)),
        theta_trim=float(np.mean(np.sort(a)[int(0.05*len(a)):int(0.95*len(a))])) if len(a)>=20 else float(np.mean(a)),
        theta_mean=float(a.mean()),
    )

out = {}
for ccy in ("BTC","ETH"):
    fp = DATA / "raw_deribit" / f"book_summary_option_{ccy}.csv"
    if not fp.exists(): continue
    rows = parse(fp)
    dirs = dirs_from_rows(rows)
    st = theta_stats(dirs)
    if not st: continue
    n = len(dirs)
    # α=2.5 mid-range; δ = n^{-1/α}; θ* = δ^{1/2}
    alpha = 2.5
    delta = n**(-1/alpha)
    theta_star = delta**0.5
    out[ccy] = dict(
        n_directions=n, delta_ref=round(delta,5), theta_star_ref=round(theta_star,5),
        theta_min=round(st["theta_min"],6),
        theta_med=round(st["theta_med"],6),
        theta_trim=round(st["theta_trim"],6),
        theta_mean=round(st["theta_mean"],6),
        regime="dispersed" if st["theta_med"]>theta_star else "sticky",
    )

(RES / "dispersion_v50.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

# --- tab_dispersion.tex ---
lines = [
    r"\begin{tabular}{@{}lrrrrl@{}}", r"\toprule",
    r"Book & $N$ & $\theta_{\rm med}$ (rad) & $\delta_{\rm ref}$ & $\theta^{*}_{\rm ref}$ & Regime \\",
    r"\midrule",
]
for ccy in ("BTC","ETH"):
    v = out.get(ccy, {})
    if not v: continue
    lines.append(f"Deribit {ccy} & {v['n_directions']} & {v['theta_med']:.4e} & "
                 f"{v['delta_ref']:.4f} & {v['theta_star_ref']:.4f} & \\emph{{{v['regime']}}} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
(TAB / "tab_dispersion.tex").write_text("\n".join(lines), encoding="utf-8")

# --- tab_dispersion_sensitivity.tex ---
lines = [
    r"\begin{tabular}{@{}lrrrr@{}}", r"\toprule",
    r"Book & $\theta_{\min}$ & $\theta_{\rm med}$ & $\theta_{\rm trim10\%}$ & $\theta_{\rm mean}$ \\",
    r"\midrule",
]
for ccy in ("BTC","ETH"):
    v = out.get(ccy, {})
    if not v: continue
    lines.append(f"Deribit {ccy} & {v['theta_min']:.4e} & {v['theta_med']:.4e} & "
                 f"{v['theta_trim']:.4e} & {v['theta_mean']:.4e} \\\\")
lines += [
    r"\midrule",
    r"Reference threshold $\theta^{*}$ & \multicolumn{4}{c}{" +
        f"$\\approx$ {out.get('BTC',{}).get('theta_star_ref',0):.4f} (rad) at $\\delta \\approx$ " +
        f"{out.get('BTC',{}).get('delta_ref',0):.3f}" + r"} \\",
    r"\bottomrule", r"\end{tabular}",
]
(TAB / "tab_dispersion_sensitivity.tex").write_text("\n".join(lines), encoding="utf-8")

for k, v in out.items(): print(k, v)
print(f"WROTE {RES/'dispersion_v50.json'}")
