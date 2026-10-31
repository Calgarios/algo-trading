# Phase 4 restored-engine results

30 October 2026 (Asia/Bangkok). Same September 9–30 development sample; no untouched validation or candidate promotion.

The reuploaded archive matches the original checksum and 536-file tree. All ten Phase 3 runs were replayed; all nine deterministic artifacts per run match the committed hashes (90/90). Wall-clock runtime is excluded.

## R76: original reference with only the target raised to 76%

| Metric | Measured |
| --- | ---: |
| Net return (%) | -3.2456 |
| SET50 excess return (pp) | 0.8539 |
| First-close-aligned excess (pp) | 1.3075 |
| Official maximum drawdown (%) | 3.1488 |
| Initial-capital maximum drawdown (%) | 3.2456 |
| SET50 return (%) | -4.0995 |
| SET50 maximum drawdown (%) | 4.0995 |
| Average closing exposure (%) | 75.6907 |
| Distinct stocks | 10 |
| Completed FIFO lots | 0 |
| Expected payoff (THB) | Undefined |
| Commission/VAT (THB) | 12,866.2399 |
| Realized P&L (THB) | 0.0000 |
| Unrealized P&L (THB) | -324,560.2399 |

Common criteria: **fail**; Best Alpha: **fail**. No sample-end liquidation or artificial round trips.

Against the original 70%-target reference, net return changes by -0.254039 pp and average exposure changes by +5.996991 pp.

| Candidate | Net return minus R76 (pp) | Average exposure minus R76 (pp) | Within 2 pp exposure |
| --- | ---: | ---: | --- |
| C2 | -0.464395 | -1.022596 | True |
| C3 | -0.343900 | -1.536624 | True |

These are portfolio comparisons. Different baskets, quantity anchors and guard policies prevent attributing the differences to signals. Equal-weight and passive paired controls remain pending.

## Actual fills: costs and completed-lot horizons

| ID | Fees THB | Price concession THB | Fees/concession added back % | Completed lots | Median holding sessions |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1 | 17,949.69 | 55,805.00 | -3.624350 | 25 | 3.0000 |
| C2 | 15,459.78 | 45,195.00 | -3.103450 | 5 | 6.0000 |
| C3 | 19,905.19 | 63,375.00 | -2.756700 | 34 | 3.0000 |
| C4 | 18,002.79 | 56,640.00 | -4.516250 | 39 | 11.0000 |
| C5 | 19,214.41 | 58,845.00 | -4.074450 | 39 | 14.0000 |
| T1 | 15,515.93 | 49,601.00 | -3.672410 | 17 | 3.0000 |
| T2 | 16,227.38 | 54,210.00 | -3.508450 | 25 | 3.0000 |
| T3 | 23,953.53 | 71,450.00 | -3.335850 | 61 | 4.0000 |
| T4 | 26,261.28 | 84,335.00 | -3.463940 | 54 | 6.0000 |
| T5 | 33,162.82 | 111,826.00 | -3.657170 | 72 | 6.0000 |

Price concession is quantity × (fill price − fill-time quote) for buys, and quantity × (quote − fill price) for sells. The verified engine records the execution tick LastPrice in `Market Price`. Adding these costs back keeps fills and final marks fixed; it is not a zero-cost replay, future-profit forecast or estimate of opportunity cost.

Holding sessions count from the first buy fill to final lot completion. Partial and still-open lots are excluded from the completed-lot median. Counts are not independent trading ideas.

## Largest symbol losses

| ID | Symbol | Net P&L THB | Realized THB | Unrealized THB |
| --- | --- | ---: | ---: | ---: |
| C1 | BCP | -124,750.61 | -18,331.09 | -106,419.52 |
| C1 | CPF | -72,929.30 | -3,320.92 | -69,608.38 |
| C1 | KTC | -57,945.53 | -5,206.12 | -52,739.42 |
| C2 | CPF | -72,832.85 | -10,294.91 | -62,537.94 |
| C2 | PTTEP | -60,049.71 | 0.00 | -60,049.71 |
| C2 | PTT | -46,595.68 | -442.29 | -46,153.40 |
| C3 | CPF | -76,318.52 | -13,714.75 | -62,603.77 |
| C3 | CCET | -49,733.17 | -8,213.21 | -41,519.96 |
| C3 | PTTEP | -46,020.37 | -2,982.19 | -43,038.18 |
| C4 | BCP | -123,616.71 | -4,024.64 | -119,592.08 |
| C4 | CPF | -80,907.18 | -14,077.00 | -66,830.17 |
| C4 | KTC | -65,437.05 | -3,410.34 | -62,026.71 |
| C5 | BCP | -117,944.41 | -11,717.30 | -106,227.11 |
| C5 | CPF | -78,458.17 | -15,345.70 | -63,112.47 |
| C5 | KTC | -51,882.58 | -3,909.02 | -47,973.56 |
| T1 | BCP | -125,702.79 | 0.00 | -125,702.79 |
| T1 | CPF | -76,254.19 | -11,573.36 | -64,680.83 |
| T1 | KTC | -51,821.43 | -3,732.39 | -48,089.04 |
| T2 | BCP | -109,466.03 | -2,303.97 | -107,162.06 |
| T2 | CPF | -71,229.51 | -5,364.56 | -65,864.95 |
| T2 | KBANK | -47,527.32 | -2,413.59 | -45,113.73 |
| T3 | BCP | -91,829.43 | -14,352.41 | -77,477.02 |
| T3 | DELTA | -63,670.60 | -35,081.32 | -28,589.28 |
| T3 | CCET | -56,749.58 | -22,623.59 | -34,125.99 |
| T4 | MTC | -78,640.33 | -25,958.46 | -52,681.87 |
| T4 | KTC | -76,792.97 | -19,036.84 | -57,756.12 |
| T4 | GPSC | -69,795.22 | -23,945.12 | -45,850.09 |
| T5 | KTC | -83,242.00 | -41,116.67 | -42,125.33 |
| T5 | MTC | -77,187.13 | -29,949.35 | -47,237.78 |
| T5 | GPSC | -71,632.91 | -12,892.84 | -58,740.07 |
| R76 | BCP | -104,515.70 | 0.00 | -104,515.70 |
| R76 | BEM | -69,978.71 | 0.00 | -69,978.71 |
| R76 | CCET | -47,350.20 | 0.00 | -47,350.20 |

All symbol P&L reconciles to total P&L. JSON/CSV retain every symbol and completed lot, including winners. Intraday adverse excursions and entry-quality causality are not established.

## Decision and remaining work

**Retain the original engineering reference; no candidate is promoted.** Inspect the symbol/lot evidence before implementing the declared P-C2, P-C3, H-C3 and B-C3 comparisons. Fresh chronological validation still needs additional permitted ticks and effective-dated membership. Restoring this archive supplies no new tick period.

See the [experiment log](../phase-4-experiments.md) and [frozen research protocol](../phase-4-research-spec.md).
