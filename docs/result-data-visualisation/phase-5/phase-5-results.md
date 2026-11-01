# Phase 5 results

1 November 2026 (Asia/Bangkok). Official TradeSim 0.2.7; Python 3.13.5.

**20 base simulations and 8 predeclared sensitivity simulations completed.** Each uses 16 September sessions and 2,906,167 ticks. Starting capital THB 10 million. All 48 supplied names were assessed; 50-name coverage is unavailable.

**Common criteria: 0/20 pass. Best Alpha: 0/20 pass. User round-trip target (>5): 20/20 pass.** September is reused development data; no candidate is promoted and independent validation remains open.

## Paired results

| Run | Return % | Excess pp | DD % | Exposure % | FIFO trips | Episodes | Payoff THB | Common | Alpha |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| C1-equal | -3.847 | 0.252 | 4.096 | 43.893 | 445 | 41 | -633.73 | fail | fail |
| C1-quality | -3.888 | 0.212 | 4.007 | 44.522 | 393 | 42 | -803.80 | fail | fail |
| C2-equal | -3.861 | 0.238 | 4.027 | 45.077 | 438 | 40 | -705.29 | fail | fail |
| C2-quality | -3.777 | 0.322 | 3.761 | 47.292 | 360 | 43 | -898.10 | fail | fail |
| C3-equal | -4.137 | -0.038 | 4.642 | 35.069 | 341 | 30 | -1,044.74 | fail | fail |
| C3-quality | -4.111 | -0.012 | 4.616 | 35.079 | 355 | 30 | -989.09 | fail | fail |
| C4-equal | -3.608 | 0.491 | 3.424 | 38.439 | 535 | 56 | -559.95 | fail | fail |
| C4-quality | -3.535 | 0.565 | 3.310 | 38.159 | 531 | 56 | -556.03 | fail | fail |
| C5-equal | -3.877 | 0.222 | 4.031 | 45.195 | 421 | 44 | -750.25 | fail | fail |
| C5-quality | -3.952 | 0.148 | 3.941 | 47.267 | 375 | 45 | -898.40 | fail | fail |
| T1-equal | -4.195 | -0.095 | 4.462 | 43.574 | 457 | 41 | -689.16 | fail | fail |
| T1-quality | -4.184 | -0.085 | 4.279 | 44.201 | 446 | 40 | -742.83 | fail | fail |
| T2-equal | -4.231 | -0.131 | 4.376 | 43.501 | 431 | 47 | -814.30 | fail | fail |
| T2-quality | -4.357 | -0.258 | 4.393 | 44.558 | 415 | 46 | -869.53 | fail | fail |
| T3-equal | -4.495 | -0.396 | 4.873 | 40.296 | 411 | 28 | -815.23 | fail | fail |
| T3-quality | -4.446 | -0.346 | 4.833 | 39.512 | 446 | 28 | -770.86 | fail | fail |
| T4-equal | -3.407 | 0.692 | 3.232 | 34.991 | 507 | 47 | -508.33 | fail | fail |
| T4-quality | -3.453 | 0.647 | 3.263 | 34.894 | 504 | 47 | -536.63 | fail | fail |
| T5-equal | -2.678 | 1.421 | 2.619 | 24.010 | 317 | 29 | -721.55 | fail | fail |
| T5-quality | -2.504 | 1.595 | 2.445 | 22.975 | 335 | 30 | -630.77 | fail | fail |

SET50 return **-4.099496%**; SET50 DD **4.099496%**. Strict portfolio DD boundary **<6.149244%**. Common FIFO threshold is >=5; this task separately requires >5. N/A payoff means no non-breakeven completed lot.

Criterion breakdown: **0/20** meet average exposure >=50%; **0/20** have positive payoff; **20/20** satisfy the strict drawdown rule. Quality sizing improves net return in **6/10** pairs. A relative improvement does not establish a profitable or eligible strategy.

![Paired overview](figures/comparison.png)

## What changed and what the comparison supports

The old ten-stock frozen baskets became daily stock-by-stock screening over all 48 supplied names. Price conditions can reject deteriorating stocks; targets respect sector/liquidity caps, daily buy budgets and a recovering drawdown guard. No exposure floor forces purchases of rejected stocks. Equal and quality runs differ only in desired sizing; execution and realized exposure can consequently differ.

| Model | Quality minus equal return pp | Exposure change pp | Payoff change THB | Interpretation |
| --- | ---: | ---: | ---: | --- |
| C1 | -0.040 | 0.629 | -170.07 | No demonstrated sizing improvement |
| C2 | 0.084 | 2.215 | -192.81 | Development improvement only; exposure differs >2 pp |
| C3 | 0.026 | 0.010 | 55.65 | Development improvement only |
| C4 | 0.074 | -0.280 | 3.93 | Development improvement only |
| C5 | -0.074 | 2.072 | -148.15 | No demonstrated sizing improvement; exposure differs >2 pp |
| T1 | 0.011 | 0.627 | -53.66 | Development improvement only |
| T2 | -0.126 | 1.057 | -55.23 | No demonstrated sizing improvement |
| T3 | 0.049 | -0.784 | 44.37 | Development improvement only |
| T4 | -0.045 | -0.097 | -28.30 | No demonstrated sizing improvement |
| T5 | 0.174 | -1.035 | 90.78 | Development improvement only |

Historical controls (different universe/policy, not a causal attribution):

| Control | Return % | Exposure % | FIFO trips | Payoff THB |
| --- | ---: | ---: | ---: | ---: |
| R76 | -3.246 | 75.691 | 0 | N/A |
| P-C3 | -3.352 | 74.671 | 10 | 189.26 |

## Metric quality and uncertainty

The pre-start five-session calibration found no positive mean after estimated fees/ticks. The initial hard positive-edge gate is rejected and retained in the experiment record. The main runs test price/risk hypotheses, not a verified future-profit model. Quality-weighted means bounded historical-edge adjustment, model rank and inverse volatility.

Expected payoff is a sample THB average of completed non-breakeven FIFO buy lots. Partial fills fragment orders into lots, and realized partial sales can sit outside that average. Episodes count a stock returning from zero holdings to zero, not necessarily independent market bets. The JSON/CSV also report win/loss magnitude, profit factor, episode returns, realized/unrealized P&L, costs and turnover. Payoff uncertainty uses 2,000 symbol-cluster bootstrap draws (seed 20261101); fewer than five clusters is unavailable. Intervals do not establish independence, future profitability or correct for all tested choices.

![Payoff uncertainty](figures/payoff-uncertainty.png)

![Realized/open losses and trip definitions](figures/pnl-and-trips.png)

![Pre-start calibration](figures/calibration.png)

## Actual sensitivity replays

C1/C3 were selected before full results. Both weighting methods were rerun at twice commission (VAT unchanged) and separately with a 0.6%-NAV band. The official class commission setting changed only inside each isolated run; the package files stayed unchanged. Fills, cash, quantities and eligibility were recomputed. These are not fixed-fill fee add-backs.

| Run | Return % | Exposure % | FIFO trips | Payoff THB | Common | Alpha |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| C1-equal-fees2 | -4.147 | 43.779 | 427 | -768.22 | fail | fail |
| C1-equal-band6 | -3.848 | 43.633 | 403 | -708.08 | fail | fail |
| C1-quality-fees2 | -4.022 | 43.564 | 373 | -866.36 | fail | fail |
| C1-quality-band6 | -3.869 | 44.731 | 378 | -821.64 | fail | fail |
| C3-equal-fees2 | -4.526 | 33.999 | 351 | -1,116.31 | fail | fail |
| C3-equal-band6 | -4.144 | 35.165 | 334 | -1,066.58 | fail | fail |
| C3-quality-fees2 | -4.420 | 33.916 | 346 | -1,106.66 | fail | fail |
| C3-quality-band6 | -4.104 | 35.045 | 353 | -992.70 | fail | fail |

![Sensitivities](figures/sensitivity.png)

## Every-stock conditions

![Eligible sessions](figures/stock-eligibility.png)

[Stock-by-date conditions and weights](stock-conditions.csv) cover every name in every base simulation. [Historical stock calibration](stock-calibration.csv) includes sample size and uncertainty. [Strategy explanations](../../phase-5-strategies.md) define all predicates and sizing formulas.

## Each strategy

### C1: Risk-adjusted momentum

![C1 paths](figures/C1.png)

### C2: Downside defence

![C2 paths](figures/C2.png)

### C3: Efficient breakout

![C3 paths](figures/C3.png)

### C4: Trend pullback

![C4 paths](figures/C4.png)

### C5: Balanced ensemble

![C5 paths](figures/C5.png)

### T1: SMA trend

![T1 paths](figures/T1.png)

### T2: EMA trend

![T2 paths](figures/T2.png)

### T3: MACD acceleration

![T3 paths](figures/T3.png)

### T4: RSI pullback

![T4 paths](figures/T4.png)

### T5: Bollinger reversion

![T5 paths](figures/T5.png)

## Verification and limits

108 tests pass. All 448 strategy-days reconcile cash, holdings, costs, NAV, realized P&L, FIFO and official metrics. C1-quality fresh-process repeat matches 9 deterministic artifacts. Maximum observed daily runtime was 38.813s with concurrent research runs (local ceiling 900s).

Preparation reproduced all 30 JSON files byte for byte. 4 queued runs were stopped before trading when a relative-output preparation check added generated files inside the package directory. The generated files were moved out, the original package tree was reverified, and the stopped cases were replayed in a separate recovery directory. Initial failures and successful retries remain recorded. The safe preparation entrypoint now normalizes output paths and rejects the official package as an output location.

Every run retains exact strategy/config, source and input hashes, plans, decisions, fills, FIFO records and runtime under artifacts/. The report verifies those hashes and independently rebuilds fill-ledger and symbol P&L totals. Official drawdown uses daily closes; initial-capital drawdown is separately exported. Official benchmark starts at the first sample close, whereas strategy return starts at initial cash; aligned first-close excess is also exported.

Closing drift across the 320 base strategy-days: **26** position-cap breaches and **1** sector-cap breach. Largest closing position **8.5833%** versus the 8% pre-buy cap; largest closing sector **20.0157%** versus 20%. No base closing exposure exceeded 80%. These measured breaches show that pre-buy limits are not continuous holding limits.

Static membership, adjustments, production event order, restart durability, registered owner and organizer acceptance remain unverified. Stops can gap or partially fill and closing risk can drift after accepted purchases. No new tick period exists for independent evaluation. The absence of a validated profitable candidate means the Phase 5 improvement gate is not closed; completed implementation and experiments are distinct from profitability and validation.

[Machine-readable results](phase-5-results.json) · [Metrics CSV](phase-5-results.csv) · [Completed FIFO lots](completed-lots.csv) · [PDF](phase-5-results.pdf) · [Next actions](../../to-do/phase-6.md)
