**Cover Letter**

Dear Editor,

I am pleased to submit my original research manuscript entitled "**From the Kakeya Theorem to Crypto Volatility Surfaces: A Three-Asset Observability Frontier from Sparse Quotes**" for consideration as an Article in *Nature*.

In 1917, Sōichi Kakeya asked how small a planar region could be if it accommodated a unit needle rotated through every direction. The three-dimensional version of that question resisted the world's harmonic analysts for a full century, until Hong Wang settled it in 2025 — a resolution recognised by the 2026 Fields Medal and now widely regarded as the sharpest tool available for bounding how much can be reconstructed from a family of directional measurements. A century-old question about needles in space has become, unexpectedly, the natural instrument for a first-order question in modern finance: how sharply can regulators reconstruct the implied-volatility surface of a market when its quotes are sparse and directional? Cryptocurrency option markets — with only a small band of live quotes anchoring a surface that determines margin, index products, and risk transfer — force this question to be answered, but the harmonic-analytic tools that answer it have never crossed into finance.

This manuscript asks a narrow question: does the recovery of a sparse, directionally structured implied-volatility surface admit a closed-form information-theoretic frontier — and, if so, does that frontier yield an operational, testable prediction that ordinary interpolation heuristics cannot see? The paper answers both questions in the affirmative. It constructs a kinetic representation of the volatility surface that maps every observed quote to a directed tube in a three-frequency space, derives a closed-form observability frontier by joining Wang's Kakeya inequality with the earlier Bourgain–Demeter cone decoupling programme, and traces the frontier through the current cryptocurrency option book. The exposition rests on three complementary elements:

1. **The Kakeya–Decoupling frontier**. A kinetic representation renders the Dupire calibration kernel as an oscillatory integral supported on a zero-Gaussian-curvature cone in a three-frequency space, and matching harmonic-analytic bounds pin the sharpest recovery rate any scheme can attain: a Kakeya-type lower bound below, a decoupled reconstruction above, and a closed-form threshold at which the two rates cross. To the best of my knowledge, this is the first import of Wang's 2025 result into a finance-econometric setting, and the first paper in finance to jointly deploy Kakeya volume inequalities and Bourgain–Demeter decoupling on a single problem.

2. **The Frontier Location**. The frontier is not a rate exponent alone but a directional-dispersion threshold in closed form. Above it, decoupling reconstructions strictly outpace kernel and spline interpolants; below it, the surface collapses onto a one-dimensional Wolff-type smile. The threshold has a direct empirical interpretation: it separates books on which conventional smoothing is sharp from books on which the reconstruction geometry irreducibly fails. Public cryptocurrency option books sit two orders of magnitude below the threshold, placing today's market on the reconstruction-geometry-failing side of the boundary.

3. **Three Independent Empirical Anchors**. The empirical section validates the theoretical frontier through three separately identifying design cuts on public order-book data: a rolling-window classification across eight venue-currency panels and 1,711 windows; a natural-experiment identification exploiting n = 130 perpetual-futures sign-flip events across Deribit, Bybit, and Binance; and a three-asset pooling experiment that documents a monotone lift of the dispersion angle toward the frontier as stablecoin, Bitcoin, and Ether books are combined. Every numeric anchor in the manuscript is bound to a public Python script and a SHA-256-hashed raw data extract; the complete reproducibility bundle is available to referees at https://github.com/dyzchina/crypto2 and reproduces every table and figure in a single build pass.

The topic is timely for a general-audience venue. Cryptocurrency option open interest on the three largest venues has grown from approximately 25 to over 100 billion U.S. dollars between January 2024 and June 2026, and the implied-volatility surfaces that regulators, clearinghouses, and index providers rely on are reconstructed from a small fraction of the theoretically listable strike–tenor grid. The observability frontier derived here yields, for the first time, a quantitative recovery boundary: a testable regime beyond which no smoothing scheme is sharp and inside which a decoupling scheme is provably optimal. That boundary is falsifiable with the public four-venue data set already in the public domain, and the paper submits itself to that falsification with each of the three identification strategies above.

To the best of the author's knowledge, this manuscript is the earliest application of this Fields-Medal-recognised harmonic-analytic result to any finance-econometric setting, and among the first pieces of work in which mathematics of such recent depth, market microstructure of that substrate, and empirical identification of that rigour are brought together within a single derivation. The interdisciplinary character of that kinship is what makes the manuscript a natural fit for *Nature*'s cross-field readership.

This manuscript is the author's original work, has not been published previously, and is not under consideration for publication elsewhere. The author has no conflicts of interest to disclose.

Thank you for your time and consideration. I look forward to hearing from you.

Sincerely,

Hongjun Gou

Email: gouhongjun_bs@cq.icbc.com.cn

**Supplements: Authorship & Declarations**

**From the Kakeya Theorem to Crypto Volatility Surfaces: A Three-Asset Observability Frontier from Sparse Quotes**

Hongjun Gou¹,*,

1. Industrial and Commercial Bank of China, Beijing 100140, China

*Corresponding author: Hongjun Gou. Email: gouhongjun_bs@cq.icbc.com.cn

# **Abstract**

We study how sharply an implied-volatility surface can be recovered from a sparse and directionally anisotropic quote family. In cryptocurrency option markets a small band of live quotes anchors the surface that regulators use for margin and risk transfer. We build a kinetic representation that maps every quote to a directed tube in a three-frequency space and prove a closed-form observability frontier. The frontier separates two regimes: above it decoupling reconstructions strictly outpace kernel interpolants, and below it a sticky-strike collapse pins recovery to a one-dimensional smile. Public books sit well below the frontier. Perpetual-futures regime shifts supply the within-sticky identifying variation. Three-asset pooling delivers a policy-relevant lift. The empirical slope is negative in every specification and remains significant under venue fixed effects.

***Keywords***: Kakeya theorem; harmonic analysis; decoupling; implied-volatility surface; sparse quotes; three-asset pooling; stablecoin; Bitcoin; Ether; observability frontier.

JEL: C14, C58, G13, G17.

# **Author Information**

Hongjun Gou (First Author & Corresponding author)

Director, ICBC Training Center (Chongqing Financial Training School), and Senior Economist, Industrial and Commercial Bank of China (ICBC), Beijing 100140, China.

Email: gouhongjun_bs@cq.icbc.com.cn

Research Interests: Financial Econometrics, FinTech, Banking Risk Management.

Biographical Note: Hongjun Gou is a Fellow of CPA Australia and a former director of ICBC Group subsidiaries. Building on his Ph.D. in Quantitative Economics (STEM) from Chongqing University, he leverages his extensive executive experience at a Global Systemically Important Bank (G-SIB) to tackle challenges in banking risk and financial technology through advanced computational methods.

# **Declarations**

## **Authorship Contribution Statement**

The submission is single-authored. Hongjun Gou is responsible for Conceptualization, Investigation, Formal Analysis, Writing – original draft, and Writing – review & editing. The author has approved the final version of the manuscript to be published and agrees to be accountable for all aspects of the work.

## **Declaration of Competing Interest**

The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

## **Acknowledgements**

No external financial support was received for this work. The author acknowledges the institutional support of Chongqing University.

## **Data and Code Availability**

The complete reproducibility bundle — including 13 build scripts, seven auto-generated tables, three publication figures in three formats, and a SHA-256 audit manifest covering all 47 artefacts — is publicly available at https://github.com/dyzchina/crypto2 and reproduces every table and figure reported in the manuscript in a single build pass. Raw data (46 files, 14 MB) drawn from six independent public endpoints (Deribit, Bybit, OKX, Dune Analytics, Binance, and CoinGecko) are frozen at 2026-08-07 and available from the author upon reasonable request.

## **Ethical Statement**

This manuscript is the author's original work and has not been published previously. It is not under consideration for publication elsewhere. The author has approved the submission.

## **Declaration of generative AI and AI-assisted technologies**

During the preparation of this work the author used DeepSeek in order to language translation and refinement. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.
