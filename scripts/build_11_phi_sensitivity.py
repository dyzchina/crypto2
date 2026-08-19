"""
build_11_phi_sensitivity.py -- RR-15: phi_anchor sensitivity table for
3-asset pool theta. Sweeps phi_anchor across 6 levels (0 to 1e-1)
and reports theta_pool. Tests whether the 3-asset lift is a
tuning-parameter artefact or a real geometric feature.

L1 REAL: all quote directions are real; phi_anchor is a scalar
functional of the L1 real stablecoin dislocation median.
"""
import json, csv, math
from pathlib import Path
from datetime import datetime
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
DATA = BUNDLE.parent / "datawang"
RES = BUNDLE / "results"; TAB = BUNDLE / "tables"

REF = datetime(2026, 8, 7)

def dirs_ccy(fp, phi_bias):
    ds = []
    with open(fp, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            try:
                inst = r["instrument_name"].split("-")
                if len(inst) != 4: continue
                _, exp, strike, _ = inst
                strike = float(strike); iv = float(r.get("mark_iv") or 0)
                under = float(r.get("underlying_price") or 0)
                if iv <= 0 or under <= 0: continue
                exp_dt = datetime.strptime(exp, "%d%b%y")
                dte = (exp_dt - REF).days
                if dte <= 0: continue
                k = math.log(strike / under); tau = dte / 365.0
                v = np.array([k, tau, phi_bias])
                n = np.linalg.norm(v)
                if n > 1e-9: ds.append(v / n)
            except Exception: continue
    return ds

def theta_med(dirs):
    if len(dirs) < 2: return None, 0
    dirs = sorted(dirs, key=lambda v: (v[0], v[1]))
    angles = []
    for i in range(len(dirs) - 1):
        c = float(np.clip(np.dot(dirs[i], dirs[i+1]), -1, 1))
        a = math.acos(abs(c))
        if a > 0: angles.append(a)
    return (float(np.median(angles)) if angles else None), len(dirs)

# phi_anchor levels: 0 (no third axis), then 5 log-spaced
levels = [0.0, 1e-5, 1e-4, 1.81e-4, 1e-3, 1e-2, 1e-1]
# note: 1.81e-4 is the median stablecoin dislocation (baseline used in build_08)
results = []
for phi in levels:
    btc = dirs_ccy(DATA / "raw_deribit" / "book_summary_option_BTC.csv", +phi)
    eth = dirs_ccy(DATA / "raw_deribit" / "book_summary_option_ETH.csv", -phi)
    pool = btc + eth
    theta, n = theta_med(pool)
    results.append(dict(
        phi_anchor=phi,
        n=n,
        theta_med=float(theta) if theta else None,
        regime="dispersed" if theta and theta > 0.26 else "sticky",
    ))

out = dict(
    sweep_levels=levels,
    baseline_phi=1.81e-4,
    results=results,
    note="phi_anchor sensitivity: theta_pool = f(phi_anchor). "
         "If theta_pool is monotone in phi_anchor, the '3-asset lift' "
         "is a phi-scaled feature rather than a pure geometric effect.",
)
(RES / "phi_sensitivity_v50.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

# LaTeX table
lines = [
    r"\begin{tabular}{@{}rrrl@{}}", r"\toprule",
    r"$\phi_{\rm anchor}$ & $N$ & $\theta_{\rm pool}$ (rad) & Regime \\",
    r"\midrule",
]
for r in results:
    phi = r["phi_anchor"]
    if phi == 0.0:
        phi_s = "$0$ (no third axis)"
    elif abs(phi - 1.81e-4) < 1e-9:
        phi_s = f"${phi:.2e}$ (baseline)"
    else:
        phi_s = f"${phi:.0e}$"
    theta_s = f"{r['theta_med']:.4e}" if r['theta_med'] else "---"
    lines.append(f"{phi_s} & {r['n']} & {theta_s} & \\emph{{{r['regime']}}} \\\\")
lines += [
    r"\midrule",
    r"Reference threshold $\theta^{*}$ & \multicolumn{3}{c}{$\approx 0.26$ rad} \\",
    r"\bottomrule", r"\end{tabular}",
]
(TAB / "tab_phi_sensitivity.tex").write_text("\n".join(lines), encoding="utf-8")

print(f"phi_anchor sensitivity sweep, {len(levels)} levels:")
for r in results:
    print(f"  phi={r['phi_anchor']:.2e}: theta={r['theta_med']:.4e} ({r['regime']})")
print(f"WROTE {RES/'phi_sensitivity_v50.json'}")
