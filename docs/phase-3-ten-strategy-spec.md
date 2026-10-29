# Ten-strategy comparison specification

Declared 30 October 2026 (Asia/Bangkok), before running these ten configurations.
These are development hypotheses, not promises of profit or prize qualification.

## Shared experiment and portfolio controls

- Use unchanged TradeSim 0.2.7, the same 16 tick days (9–30 September 2026),
  THB 10 million, identical costs, IOC rules and notebook event ordering.
- Read at most 180 daily bars through the verified historical API. Require 80
  complete prior bars, strictly increasing dates, positive finite OHLC prices,
  nonnegative volume and a latest observation within seven calendar days.
- At the September 9 start, form a liquidity pool of the 30 largest median
  20-session close-times-volume values among eligible supplied stocks. Rank this
  pool independently for each strategy; select ten, with at most two per sector.
  Record inputs and freeze each basket in its companion configuration. Never
  rotate into an eleventh distinct stock during this comparison.
- Recalculate signals daily, using only previous-day-and-earlier observations.
  Rank the ten frozen names and allocate from 1.2 to 0.8 times equal weight
  (strongest to weakest); the weights sum to the portfolio target. The regular
  target is 76% of opening NAV, with maximum 10% per name, 80% invested and
  minimum 20% cash before buys. New weights may change existing positions.
- Use prior close to translate weights into daily fixed 100-share quantity
  targets. Rebalance only if the initial gap exceeds 0.4% of opening NAV, or a
  position is absent. Once an intent is active, retry actual residual quantities
  in later 15-minute decision slots; do not repeatedly trade on forming ticks.
  No forced sample-end liquidation, cosmetic round trips, or fixed profit exits.
- Shared drawdown guard uses the known opening portfolio drawdown (including
  initial capital) and SET50 history scoped to the run start. Target falls to
  72% if portfolio drawdown reaches 2%, or reaches 1.2 times benchmark drawdown
  when benchmark drawdown is at least 0.5%. It falls to 55% if portfolio drawdown
  reaches 4%, or reaches 1.35 times benchmark drawdown when benchmark drawdown
  is at least 1%. Hard protection takes priority over the user's 70–80% average
  exposure preference. Daily lag, gaps and partial fills can still breach limits.
- No rule guarantees final drawdown <1.5 times SET50 drawdown or positive payoff.
  Use raw independent metrics for the strict eligibility threshold. Zero/missing
  benchmark cases remain explicit. Distinguish common criteria from Best Alpha.
- All ten use this shared risk/execution layer so signal differences are easier
  to assess. This is signal-ranked allocation, not a classic all-in/all-out
  crossover backtest: remaining invested is an intentional exposure constraint.

## Five custom approaches

| ID | Strategy | Predeclared score and rationale |
| --- | --- | --- |
| C1 | Risk-adjusted momentum | (0.6 × 20-session return + 0.4 × 60-session return) / (20-session daily volatility × √20); favor persistent gains relative to risk |
| C2 | Downside defence | Negative (annualized downside deviation + 0.1 × positive 60-session SET50 beta); favor lower downside and market sensitivity |
| C3 | Efficient breakout | Distance from previous 55-session high / 20-session volatility, plus 0.5 × 20-session efficiency ratio; favor near-high prices reached with less back-and-forth movement |
| C4 | Trend pullback | (60-session return − 2 × 5-session return) / (20-session volatility × √20); favor a recent pullback within a stronger longer trend |
| C5 | Balanced ensemble | Mean cross-sectional percentile rank of C1–C4; avoid relying on one signal family |

## Five indicator-based approaches

| ID | Strategy | Predeclared score and rationale |
| --- | --- | --- |
| T1 | SMA trend | (SMA20 / SMA60 − 1) / 20-session volatility; favor stronger medium-term trends |
| T2 | EMA trend | (EMA12 − EMA26) / (close × 20-session volatility); react faster to trend changes |
| T3 | MACD acceleration | (MACD histogram + 0.25 × MACD line) / (close × 20-session volatility), using 12/26/9 EMAs; favor improving momentum |
| T4 | RSI pullback | −(RSI14 − 35)² / 100, plus 5 when close > SMA60; prefer moderate oversold conditions within an established trend |
| T5 | Bollinger reversion | −abs(z20 + 1) − 2 × max(−2 − z20, 0), plus 1 when close > SMA60; prefer moderate lower-band pullbacks and penalize extreme falls |

Volatility is sample standard deviation of daily simple returns. Downside
deviation is √mean(min(return, 0)²). Beta uses aligned symbol/SET50 daily
returns (at least 40). Efficiency is absolute 20-session net change divided
by total absolute daily change. EMA is seeded at the first available close
and updated with 2/(period+1); RSI uses Wilder's 14-period smoothing. Bollinger
z uses the 20-close mean and sample standard deviation. Alphabetical ties are
deterministic. Constant-price/zero-variance inputs use explicit finite handling.

## Evaluation and acceptance

Do not tune these parameters after seeing the comparison. Report all ten,
including failures, plus the earlier three references in a separate historical
comparison. Save per-run SET50 return, strategy net return, excess return (pp),
portfolio and SET50 maximum drawdown (%), average and closing exposure, distinct
stocks, completed FIFO lots, payoff, fees, realized/unrealized P&L and runtime.

Show user-target exposure (70–80%) separately from common minimum exposure
(≥50%). Report the strict relative drawdown threshold and both common/Best Alpha
status. Eligibility comes before return in identifying a development lead; if
none pass, name no prize-ready winner. Repeat a selected representative run to
check deterministic artifacts. The reused September sample cannot establish
out-of-sample profitability; chronological validation remains future work.
