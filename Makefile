# Makefile -- Reproducibility Bundle v5.0
# One-command reproduction. Windows: use `make all` under Git Bash / MSYS2.
#
#  Sources: ../datawang/  (frozen 2026-08-07, hashed in MANIFEST.json)
#  Outputs: results/  tables/  figures/
#  Manuscript: manuscript/main_eca.{tex,pdf}
#
#  Steps ordered so that each script only reads outputs produced by
#  earlier steps (no circular dependencies).

PY := python
SCR := scripts
RES := results
TAB := tables
FIG := figures
MAN := manuscript

.PHONY: all data figures manuscript manifest clean

all: data figures manuscript manifest

data:
	$(PY) $(SCR)/build_01_snapshot.py
	$(PY) $(SCR)/build_02_dispersion.py
	$(PY) $(SCR)/build_03_events.py
	$(PY) $(SCR)/build_04_regression.py
	$(PY) $(SCR)/build_05_rolling.py
	$(PY) $(SCR)/build_06_benchmark.py
	$(PY) $(SCR)/build_07_cross_venue_pool.py
	$(PY) $(SCR)/build_08_three_asset_pool.py
	$(PY) $(SCR)/build_10_robustness.py
	$(PY) $(SCR)/build_11_phi_sensitivity.py
	$(PY) $(SCR)/build_12_insample_benchmark.py

figures:
	$(PY) $(SCR)/build_figures.py

manuscript:
	cd $(MAN) && pdflatex -interaction=nonstopmode main_eca.tex \
	  && bibtex main_eca \
	  && pdflatex -interaction=nonstopmode main_eca.tex \
	  && pdflatex -interaction=nonstopmode main_eca.tex

manifest:
	$(PY) $(SCR)/build_manifest.py

clean:
	rm -f $(MAN)/*.aux $(MAN)/*.bbl $(MAN)/*.blg $(MAN)/*.log $(MAN)/*.out $(MAN)/*.toc
