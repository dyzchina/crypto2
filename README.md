# Reproducibility Bundle v7.0

**Manuscript.** *Hidden Risk in Missing Quotes: Identification Bounds
for Recovering Crypto Volatility Surfaces.*
**Target.** Journal under submission.
**Author.** Hongjun Gou · Industrial and Commercial Bank of China (ICBC).
**Data snapshot.** 2026-08-07 (frozen).
**Bundle generated.** 2026-09-30.

## What is in this bundle

```
reproducibility_bundle_v7.0/
├── README.md              (this file)
├── Makefile               (make all → full reproduction)
├── MANIFEST.json          (SHA-256 of every artefact)
├── data_charter.md        (L1 REAL / L2 PROXY / L3 SIM-GROUNDED classification)
├── manuscript/
│   ├── main.tex            (37 pp, submission-ready)
│   ├── main.pdf            (compiled)
│   ├── main_anonymous.tex  (double-blind copy, author field blank)
│   ├── main_anonymous.pdf  (compiled)
│   └── refs.bib
├── scripts/               (13 analysis scripts)
├── results/               (12 JSON fact files, *_v70.json)
├── tables/                (14 auto-generated .tex tables)
└── figures/               (3 publication figures × 3 formats)
```

## One-command reproduction

```bash
cd reproducibility_bundle_v7.0
make all       # data → figures → manuscript, 3-pass + bibtex
```

Requires: Python 3.9+ (numpy, matplotlib); MiKTeX/TeX Live with `ecta.bst`;
`bibtex`, `pdflatex`. The raw data sibling directory `../datawang/`
(13.07 MB across 46 files, frozen 2026-08-07, SHA-256 audit hashes
recorded in `MANIFEST.json`) must be present next to the bundle; every
`build_*.py` script resolves inputs via `Path(__file__).resolve().parents[1] / "datawang"`.
All random draws in the analysis scripts (block bootstrap, pairs
bootstrap, five-fold cross-validation folds) use the reproducible
seed `20260814`.

## Data policy (L1 / L2 / L3)

Every empirical claim in the manuscript carries a level tag from
`data_charter.md`:

- **L1 REAL** — direct public-API measurement, hashed in `MANIFEST.json`.
- **L2 PROXY** — a verifiable intermediate quantity proxying an
  unobservable target; identification and sensitivity are explicit.
- **L3 SIM-GROUNDED** — grounded simulation calibrated to L1 marginals;
  used only for illustrative benchmarking, never for headline claims.

Raw data live in `../datawang/` (a sibling directory of this bundle,
frozen 2026-08-07, 13.07 MB across 46 files from six independent
public endpoints: Deribit, Bybit, OKX, Dune Analytics, Binance,
CoinGecko). This structure means a single data snapshot can support
multiple bundle versions without duplication.

## Main-axis lock

The paper's main axis --- the **title**, **abstract**, and
**introduction (including the three-paragraph contribution segment)**
--- is locked and reflects the paper's central claim: the first
finance-econometric application of Wang's 2025 Fields-Medal-recognised
resolution of the three-dimensional Kakeya conjecture, paired with
Bourgain--Demeter cone decoupling, to derive an
**observability frontier** on implied-volatility-surface recovery
from sparse and directionally anisotropic quote families. Empirical
sections, figures, tables, and appendices are all built to support
this axis end-to-end.

## Version history

- **v0.1** (2026-08-13): initial exploratory bundle.
- **v2.0 → v2.3** (2026-08-14): three review rounds and adjudicated
  revisions; L1/L2/L3 charter introduced.
- **v3.0** (2026-08-14): clean submission-ready bundle. Main axis
  locked; 34-page manuscript; 36 journal references; every empirical
  number regenerated from `datawang/` real data; every table and
  figure connected by a semantic transition; specific in-bundle
  filenames removed from the body text (retained only in the
  Data Manifest appendix). The v2.0 and v2.3 bundles remain as
  reference archives.
- **v4.0 / v5.0** (2026-08-17 → 2026-09-09): abstract and introduction
  harmonisation; plain-language sticky-regime phrasing adopted in the
  abstract and introduction (technical wording retained in Theorem 9
  and Remark 11); cover-letter variants added for RES and SIAM JFM
  with all mathematical symbols removed.
- **v6.0** (2026-09-10): clean rebuild from the frozen 2026-08-07
  snapshot. Compilation artefacts (`.aux/.log/.blg/.out`), the
  anonymous variant, and superseded cover letters removed; all 13
  analysis scripts and the 3 publication figures regenerated
  end-to-end; README and MANIFEST refreshed to v6.0.
- **v7.0** (2026-09-30): submission-ready refresh. Title retargeted to
  *Hidden Risk in Missing Quotes: Identification Bounds for Recovering
  Crypto Volatility Surfaces*; abstract and introduction rewritten so
  the stated contribution matches the paper's actual mathematical
  provenance (the bounds are transferred from Wang 2025 and
  Bourgain--Demeter, not derived); cone decoupling attributed to
  Bourgain--Demeter (2015) Theorem 1.2 rather than to BDG (2016);
  self-limiting phrasing removed throughout; Table 3 typeset at the
  same size as the other tables; Algorithm 1 double-subscript error
  fixed. Version-stamped intermediates renamed `_v50` → `_v70`. All 13
  analysis scripts rerun from the frozen snapshot and verified
  key-by-key against v6.0 (7,080 numeric keys, no differences). The
  manuscript compiles with no errors and no unresolved references;
  `main_anonymous.pdf` is the double-blind submission copy.

## Contact

Hongjun Gou · gouhongjun_bs@cq.icbc.com.cn
