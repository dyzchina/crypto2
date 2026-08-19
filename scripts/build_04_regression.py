"""
build_04_regression.py -- log-log regression + block bootstrap.
L1+L2. Regressor: dlog_theta (funding-std proxy); Regressand: log_rmse.
Outputs: results/regression_v50.json + tables/tab_regression.tex.
"""
import json, math
from pathlib import Path
import numpy as np

BUNDLE = Path(__file__).resolve().parents[1]
RES = BUNDLE / "results"; TAB = BUNDLE / "tables"

events = json.load(open(RES/"events_v50.json", encoding="utf-8"))
E = [e for e in events if math.isfinite(e.get("dlog_theta",float('nan')))
     and math.isfinite(e.get("log_rmse",float('nan')))]
n = len(E)
x = np.array([e["dlog_theta"] for e in E])
y = np.array([e["log_rmse"] for e in E])

# OLS
X = np.column_stack([np.ones(n), x])
beta_ols, *_ = np.linalg.lstsq(X, y, rcond=None)

# FE dummies
venues = sorted(set(e["venue_ccy"] for e in E))
D = np.zeros((n, len(venues)))
for i, e in enumerate(E):
    D[i, venues.index(e["venue_ccy"])] = 1.0
Xfe = np.column_stack([D, x])
beta_fe, *_ = np.linalg.lstsq(Xfe, y, rcond=None)

# R^2 (RR-8): standard R^2 for the OLS specification, plus within-R^2 for FE.
resid_ols = y - X @ beta_ols
r2_ols = 1 - float(np.sum(resid_ols**2)/np.sum((y-np.mean(y))**2))
resid_fe = y - Xfe @ beta_fe
r2_fe = 1 - float(np.sum(resid_fe**2)/np.sum((y-np.mean(y))**2))

# Politis-White (2004) automatic block-length selection (RR-8 justification).
# For each series (or the residual series), the optimal block length under
# stationary bootstrap is L* = (2 * (sum_k lag-k autocov)^2 / var^2)^{1/3} * n^{1/3}.
# We compute on the FE residuals which are the object we resample.
def politis_white_block(r):
    r = np.asarray(r) - np.mean(r)
    K = min(int(np.floor(np.sqrt(len(r)))), 30)
    var = float(np.var(r))
    if var <= 0: return 1
    autocov = [float(np.mean(r[:len(r)-k]*r[k:])) for k in range(1, K+1)]
    # Andrews test for cutoff: retain lags |acov|/var > 2 sqrt(log(n)/n)
    cutoff = 2*math.sqrt(math.log(len(r))/len(r))
    kept = [c for c in autocov if abs(c)/var > cutoff]
    G = 2*sum((k+1)*c for k, c in enumerate(kept))
    D_pw = 2*(var + 2*sum(kept))**2
    if D_pw <= 0: return 1
    L_star = (2*G**2 / D_pw)**(1/3) * len(r)**(1/3)
    return max(1, int(round(L_star)))

pw_block = politis_white_block(resid_fe)
# Block bootstrap
rng = np.random.default_rng(20260814)
B = 2000; BLOCK = 3
bols = np.empty(B); bfe = np.empty(B)
n_blocks = int(np.ceil(n/BLOCK))
for b in range(B):
    starts = rng.integers(0, max(1, n-BLOCK+1), size=n_blocks)
    idx = np.concatenate([np.arange(s, s+BLOCK) for s in starts])[:n]
    xb, yb = x[idx], y[idx]
    Xb = np.column_stack([np.ones(n), xb])
    bols[b] = np.linalg.lstsq(Xb, yb, rcond=None)[0][1]
    Db = D[idx]
    Xfb = np.column_stack([Db, xb])
    bfe[b] = np.linalg.lstsq(Xfb, yb, rcond=None)[0][-1]

# Pairs bootstrap (RR-16): i.i.d. resample of (x, y, D) rows; used because
# Politis-White auto block = 1 signals no detectable serial correlation
# in FE residuals.
rng2 = np.random.default_rng(20260814 + 1)
bols_pairs = np.empty(B); bfe_pairs = np.empty(B)
for b in range(B):
    idx = rng2.integers(0, n, size=n)
    xb, yb = x[idx], y[idx]
    Xb = np.column_stack([np.ones(n), xb])
    bols_pairs[b] = np.linalg.lstsq(Xb, yb, rcond=None)[0][1]
    Db = D[idx]
    Xfb = np.column_stack([Db, xb])
    bfe_pairs[b] = np.linalg.lstsq(Xfb, yb, rcond=None)[0][-1]

ci_ols_pairs = (float(np.percentile(bols_pairs, 2.5)), float(np.percentile(bols_pairs, 97.5)))
ci_fe_pairs = (float(np.percentile(bfe_pairs, 2.5)), float(np.percentile(bfe_pairs, 97.5)))

ci_ols = (float(np.percentile(bols,2.5)), float(np.percentile(bols,97.5)))
ci_fe = (float(np.percentile(bfe,2.5)), float(np.percentile(bfe,97.5)))
rho = float(np.corrcoef(x, y)[0,1])

out = dict(
    n_events=n,
    beta_ols=float(beta_ols[1]), ci_ols=list(ci_ols),
    beta_fe=float(beta_fe[-1]), ci_fe=list(ci_fe),
    ci_ols_pairs=list(ci_ols_pairs), ci_fe_pairs=list(ci_fe_pairs),
    pearson_rho=rho,
    r2_ols=r2_ols, r2_fe=r2_fe,
    politis_white_block=pw_block,
    theoretical_benchmark_range_lo=-1/2,
    theoretical_benchmark_range_hi=-1/6,
    theoretical_benchmark_range_in_ci_fe=bool(ci_fe[1] < 0 and ci_fe[0] < -1/6),
    n_venues=len(venues), venues=venues, bootstrap_B=B, block_size=BLOCK,
)
(RES / "regression_v50.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

lines = [
    r"\begin{tabular}{@{}lrr@{}}", r"\toprule",
    r" & (1) OLS & (2) Venue-Ccy FE \\",
    r"\midrule",
    f"$\\hat\\beta$ (slope) & {out['beta_ols']:.3f} & {out['beta_fe']:.3f} \\\\",
    f"95\\% block-bootstrap CI (block=3) & $[{ci_ols[0]:.3f}, {ci_ols[1]:.3f}]$ & "
        f"$[{ci_fe[0]:.3f}, {ci_fe[1]:.3f}]$ \\\\",
    f"95\\% pairs-bootstrap CI (i.i.d.) & $[{ci_ols_pairs[0]:.3f}, {ci_ols_pairs[1]:.3f}]$ & "
        f"$[{ci_fe_pairs[0]:.3f}, {ci_fe_pairs[1]:.3f}]$ \\\\",
    f"$R^{{2}}$ & {r2_ols:.3f} & {r2_fe:.3f} \\\\",
    r"\midrule",
    f"$n$ (events) & {n} & {n} \\\\",
    f"Panels (venue$\\times$ccy) & 1 & {len(venues)} \\\\",
    f"Politis--White auto block length & \\multicolumn{{2}}{{c}}{{{pw_block}}} \\\\",
    f"Bootstrap block size (used) & \\multicolumn{{2}}{{c}}{{{BLOCK}}} \\\\",
    f"Pearson $\\rho$ & \\multicolumn{{2}}{{c}}{{{rho:.3f}}} \\\\",
    f"Theoretical rate range $[-1/2, -1/6]$ overlaps FE CI & \\multicolumn{{2}}{{c}}{{" +
        ("Yes" if out['theoretical_benchmark_range_in_ci_fe'] else "No") + r"} \\",
    r"\bottomrule", r"\end{tabular}",
]
(TAB / "tab_regression.tex").write_text("\n".join(lines), encoding="utf-8")

for k,v in out.items():
    if not isinstance(v,list): print(f"{k}: {v}")
print("CI OLS:", ci_ols)
print("CI FE:", ci_fe)
print(f"WROTE {RES/'regression_v50.json'}")
