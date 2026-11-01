# Phase 5 research declaration

Declared 1 November 2026 (Asia/Bangkok), before Phase 5 tick results.
September 9–30 is reused development data. No independent validation claim.

## Experiment and promotion rules

Run C1–C5 and T1–T5 twice: equal allocation and quality/inverse-volatility
allocation, under identical stock filters, risk limits and execution rules.
Consider every supplied constituent each day: currently 48, not an invented 50.
This supersedes the earlier ten-stock/15-stock planning restriction at the user's
request. Membership remains a static sample, without effective dates.

Keep the original strategy, Phase 3/4 declarations and results unchanged.
Freeze new source/config hashes before replay; keep all failures. No parameter
search against September and no threshold relaxation to produce eligible results.
Equal allocation means equal desired weights among eligible names before sector,
position, liquidity and risk caps; unallocated weight stays in cash.

Calibration: at most 500 prior daily bars per stock, non-overlapping five-session
outcomes (next open through fifth close), one tick each side plus commission/VAT.
Use only outcomes ending strictly before September 9. A prior close above its
60-session SMA defines the historical support population. Record actual sample
size, mean, standard error, shrinkage toward zero, Beta(2,2) win estimate, Wilson
95% interval, profit factor and downside tails. These are historical daily-price
proxies, not official-engine fills, calibrated future probabilities or independent
proof of alpha. Do not use post-start calibration outcomes or final stock P&L.

Eligibility: at least 12 supported outcomes, positive shrunk net mean, smoothed
win fraction >=50%, daily close above SMA60, ret20 > -3%, 20-day median traded
value >=THB 20m, daily volatility <=5%, plus the model-specific entry signal.
The 95% lower confidence bounds are reported, not silently interpreted as passing.
Portfolio sizing limits the quality-score influence; it is not Kelly sizing.

Normal target 76%, pre-buy maximum 80%, cash reserve 20%, position cap 8%, sector
cap 20%; participation target <=1% of prior median daily value per position.
Soft current drawdown >=1.5% or >=1.15x known benchmark DD (once >=1%) lowers
target to 55%. Hard >=3% or >=1.3x benchmark DD (once >=1%) lowers it to 35%.
Recovery follows current distance from the known NAV peak, not the all-time
maximum drawdown statistic. No forced exposure floor when signals or risk fail.

Signals are daily; execution uses 15-minute slots, 100-share lots, current cash
and actual residual quantities. A 0.4%-NAV rebalance band limits small changes.
After initial deployment, new buys are budgeted at 15% NAV per day, split across
selected names. Sell risk is never blocked by this budget. No same-day re-entry
after an exit, and no end-sample liquidation to create round trips.
Exit on loss of the 60-day trend by 1.5%, severe 20-day deterioration (<-5%),
net loss beyond max(2%, 2.5x ATR14/close), or a five-session mature profit beyond
max(1%, 2x current estimated round-trip friction). Targets handle signal decay
and concentration separately. Stops are sampled, can gap and can partially fill.

Sensitivity: preselected C1 and C3, both weighting modes, replay at 2x commission
and separately with a 0.6%-NAV rebalance band. These eight extra runs are actual
engine executions in isolated processes using its commission setting; no package
files are patched. The base comparison remains twenty runs.

Report every run's net and excess returns, both drawdown anchors, average
exposure, distinct stocks, completed FIFO round trips, position episodes,
expected payoff, win/loss magnitude, profit factor, fees, turnover and open losses.
Common rules require >=5 FIFO lots; the user's stricter target is **>5**.
Best Alpha additionally requires nonnegative net and excess returns.

Retain complexity only if it improves after-cost return/payoff without losing
eligibility or violating risk constraints, survives the declared sensitivities,
and later confirms on additional permitted chronological data. An attractive
September result alone does not close validation or justify a profitable-trading
claim. Phase 5 closes only when the guide's improvement/sensitivity gate is met;
engineering and completed experiments are reported separately.
