# Phase 5 strategy explanations

All ten models now examine every supplied SET50 constituent each day: **48
available stocks**. They no longer freeze a ten-stock basket. A name can enter,
leave or re-enter on later days when its own conditions change. No missing 49th
or 50th stock is invented. Static membership is a data limitation.

Each model has two simulations: **equal** and **quality**. Both use the same
entry filters, exit rules, capital, dates and risk controls. Only desired sizing
changes. “Quality” names a research sizing formula; it does not mean its alpha
or future win probability has been validated.

## What the metrics establish

The original Phase 4 problem was mostly unrealized stock losses, not only fees.
Broader diversification alone cannot fix that. Phase 5 adds explicit stock entry
conditions, permits declining names to leave, budgets new buys and makes the
portfolio guard recover as current drawdown improves.

A 500-bar pre-start calibration measures non-overlapping five-session returns
from the next open to fifth close, under the broad condition close >= SMA60.
One adverse tick each side and 0.157% commission plus 7% VAT on commission are
included. Every outcome ends before 9 September 2026. The stock's mean is shrunk
by n/(n+20); its win estimate uses (wins+2)/(n+4). The report includes sample size,
standard error, approximate mean interval, Wilson win interval, profit factor
and worst outcome. These are daily-price proxies; stops, IOC liquidity and
strategy-specific predicates are not represented in the calibration trades.

**No stock had a positive mean after these costs in this calibration.** A hard
positive-edge gate was rejected after it made no trades in a two-day smoke test.
The main experiment therefore tests price and risk hypotheses, while displaying
this adverse statistical evidence. It does not label estimated win fractions as
verified future probabilities. Confidence intervals do not correct static
membership bias, all model choices or the reuse of September data.

## Conditions shared by every stock

Before a new allocation, each stock needs at least 80 valid, ordered, unique daily
bars ending strictly before the decision date, a fresh last observation (at most
seven calendar days old), and at least 40 aligned stock/SET50 return intervals.
OHLC values must be positive, finite and internally consistent. Calibration must
contain at least 12 supported outcomes; the supplied short BANPU history fails
this test. Median close-times-volume over 20 sessions must be >=THB 20m, daily
return volatility must be positive and <=5%, close >= SMA60, and 20-session
return >-3%. The model-specific condition below must also hold.

These rules are **evaluated for each stock**, not a hindsight blacklist of losing
symbols. [Stock conditions](result-data-visualisation/phase-5/stock-conditions.csv)
records every base run, date, symbol, pass/fail reason, target, weight and relevant
indicator. [Calibration](result-data-visualisation/phase-5/stock-calibration.csv)
records each stock's historical evidence. Insufficient history is a rejection,
not a fabricated score. Exposure can fall short when few stocks qualify.

## Ten model definitions

Returns are fractional close-to-close returns. vol20 is the sample standard
deviation of 20 daily returns. RSI14 uses Wilder smoothing. EMA uses adjust=False
recursion from the first supplied close. MACD is EMA12 minus EMA26; its histogram
subtracts EMA9 of MACD. Bollinger z uses the 20-close sample standard deviation.
Beta60 uses aligned return intervals; downside20 is annualized RMS of negative
20-session daily returns. Ranking affects only quality sizing.

| ID | Strategy and entry condition | Quality ranking signal | Rationale and principal failure mode |
| --- | --- | --- | --- |
| C1 | Risk-adjusted momentum: ret20>0 and ret60>0 | (0.6 ret20+0.4 ret60)/(vol20 sqrt(20)) | Favors persistent advances per unit risk; loses in reversals and gaps |
| C2 | Downside defence: downside20<35%, beta60<1.2 | -(downside20+0.1 max(beta60,0)) | Seeks less downside sensitivity within an uptrend; low beta is not positive alpha |
| C3 | Efficient breakout: close>=96% of prior 55-session high, ret20>0, efficiency20>=0.15 | (close/high55-1)/vol20+0.5 efficiency20 | Seeks orderly advances near highs; false breakouts and expensive entry ticks hurt |
| C4 | Trend pullback: ret60>0, -4%<=ret5<=1.5% | (ret60-2 ret5)/(vol20 sqrt(20)) | Buys a pause in an established trend; a pullback can become a prolonged decline |
| C5 | Balanced ensemble: at least two of C1–C4 entry predicates | Mean percentile of C1–C4 scores, equal treatment of ties | Diversifies signal definitions; components share exposures and are not independent bets |
| T1 | SMA trend: SMA20>=SMA60 and close>=SMA20 | (SMA20/SMA60-1)/vol20 | Requires price and average trend agreement; lag and whipsaws remain |
| T2 | EMA trend: EMA12>=EMA26 and close>=EMA26 | (EMA12-EMA26)/(close vol20) | Faster trend response; more false changes and turnover |
| T3 | MACD acceleration: MACD>0 and histogram>0 | (histogram+0.25 MACD)/(close vol20) | Requires positive trend plus acceleration; late signals can reverse |
| T4 | RSI pullback: RSI14 in [35,60], ret5<=1% | -(RSI14-35)^2/100+5 if close>SMA60 | Seeks moderate pullbacks in the shared long trend; may stay underinvested |
| T5 | Bollinger reversion: z in [-1.75,0] | -abs(z+1)-2 max(-2-z,0)+1 if close>SMA60 | Seeks below-average prices without severe breakdown; often very few eligible stocks |

The high55 window excludes the latest completed bar. Efficiency20 is absolute
net movement divided by total absolute movement over 20 intervals; direction is
established separately by the trend predicates. These are daily entry states,
not claims that a crossover occurred exactly today.

## Equal and quality sizing

Equal assigns raw score 1 to each eligible stock. Quality assigns:

`(0.75 + 0.5 * score_percentile) * confidence_adjustment / max(vol20, 0.01)`

`confidence_adjustment = clip(1 + shrunk_mean_net/max(se_net,0.005), 0.5,1.5)`

The bounded adjustment cannot certify a positive edge. Negative evidence reduces
relative weight; the minimum prevents uncertain estimates from dominating sizing.
Scores tied at a value receive the same percentile. No leverage or Kelly sizing.

A deterministic proportional allocation respects 8% per stock, 20% per sector
and a position value <=1% of its prior median daily traded value. The last rule
is a position-size liquidity proxy, not a guarantee about today's participation.
Weights sum to at most the portfolio target; unused capacity stays cash. Under
binding caps even the “equal” portfolio can have unequal final weights. A 48-name
candidate universe does not require 48 holdings or trades.

## Risk and execution

- Normal target 76%, maximum pre-buy exposure 80%, minimum cash reserve 20%.
- Current drawdown from the known NAV peak >=1.5% lowers the target to 55%; >=3%
  lowers it to 35%. Relative triggers are 1.15x and 1.3x prior known benchmark
  drawdown once benchmark drawdown reaches 1%. Recovery uses current drawdown;
  the guard does not permanently latch the historic maximum loss.
- Live sampled marks may further reduce daily targets. Cross-symbol ticks retain
  organizer notebook row-round-robin order and are not simultaneous. These are
  sampled protections, not continuous drawdown guarantees.
- Exit the entire remaining position after a trend break (last<SMA60*0.985 or
  prior ret20<-5%), a net liquidation loss beyond max(2%,2.5 ATR14/close), or a
  profit after at least five observed holding sessions above max(1%,2x estimated
  round-trip friction). ATR14 is the mean of 14 true ranges. This is not a
  trailing-stop model. Costs are included in the net liquidation estimate.
- A name losing its daily entry eligibility has a zero target and can be sold.
  Profits, stop-outs, open losses and partial realization are all reported; taking
  profits alone does not demonstrate a profitable portfolio.
- 15-minute execution slots, 100-share lots and a 0.4%-NAV rebalance activation
  band reduce churn. Risk exits and zero targets bypass the band. A triggered
  position exit remains active for that symbol for the rest of the day; a sell
  prevents same-day buys. Partial exits retry actual remaining holdings.
- Initial buy budgets follow capped target weights. Later daily buys total at
  most 15% of opening NAV, allocated equally as a budget across selected names;
  unused budgets are not reassigned. Sales are never stopped by the buy budget.
- Pre-buy calculations include fees, slippage, current sector/position values and
  conservative NAV. Rejections and zero fills are logged. Risk limits can drift
  after price moves. There is no sample-end liquidation or round-trip quota.

Runtime state (slot, buy budget, exit latch) is currently process-local. A same-day
restart could reset those controls. Daily reload uses saved engine holdings/cash,
but durable same-day state must be addressed during the Phase 6 recovery work.

## Reading the results

Official expected payoff is mean THB P&L on fully closed non-breakeven FIFO buy
lots. It is affected by lot sizes and IOC fragmentation. The report additionally
shows full zero-position-to-zero-position episodes, win rate, win/loss magnitude,
profit factor, turnover, fees, mark-to-market losses and uncertainty. More FIFO
lots do not imply more independent decisions. Bootstrap payoff intervals group
lots by symbol to acknowledge within-stock dependence; even those cannot remove
market-wide dependence or multiple-testing bias.

Common criteria use >=5 FIFO round trips; the user's stricter goal is **>5**.
The drawdown rule is strict: portfolio DD <1.5x SET50 DD. Positive total return is
a Best Alpha addition. The side-by-side [results](result-data-visualisation/phase-5/phase-5-results.md)
report all checks with unrounded inputs. A selected model must improve after
costs, preserve eligibility and survive sensitivity plus fresh validation before
promotion. A profitable or high-probability strategy is not presumed.
