# Strategy review for Best Alpha

## What the retention results established

C3 gained 0.3184 percentage points and reduced fees, but its open losses grew.
C4 lost another 0.1850 points. Both had negative payoff. Retention addresses
unnecessary exits, but does not identify enough profitable opportunities.

Best Alpha requires nonnegative total and excess return in addition to positive
FIFO payoff, >=50% average exposure, >=5 FIFO trips and strict benchmark-relative
drawdown. Our additional target is >5 trips. A negative-return strategy that
outperforms a falling SET50 still fails. See [working rules](../../docs/award-criteria.md)
for the original-source review and its verification limitations.

## Review of available approaches

| Approach | Economic hypothesis | Principal problem | Decision |
| --- | --- | --- | --- |
| C3 efficient breakout | Persistent demand sustains price strength | False breakouts and repeated tick/fee costs | Keep as the closest retention comparator; add friction screen and fewer allocation-driven sales |
| C1/T1/T2/T3 momentum and moving-average variants | Price trends persist | Closely related indicators do not constitute independent evidence; small winners can be harvested too early | Test one relative-strength momentum policy with a trailing exit instead of a fixed profit exit |
| C4/T4/T5 pullback/reversion | Temporary selling reverses within a healthy trend | Catching a deteriorating stock creates large open losses | Test defensive pullbacks with downside-volatility and beta screens |
| C2 low-risk stocks | Lower downside exposure cushions adverse markets | Low volatility is not a positive-return forecast; weak markets can lower exposure below eligibility | Use defensive screens and bounded risk sizing, retaining explicit loss exits |
| C5 rank ensemble | Combining different signals reduces concentration in one hypothesis | Averaging correlated or unprofitable signals does not create alpha | Defer another ensemble until component net edges are supported |
| Market-neutral pairs / index hedge | Remove market direction and monetize relative convergence | Current tested strategy interface is long-only; short/hedge permissions and costs are unverified | Do not assume these trades are permitted or simulate fictional hedges |
| Intraday reversal / market making | Short-term liquidity compensation | One-tick execution and commission burden, partial fills, limited independent sessions | Do not add high turnover without evidence of an edge larger than full costs |

## Exact new policies

All use prior daily information, the entire supplied candidate universe, and
existing data freshness, quality-sample, liquidity, trend and volatility checks.
Each runs equal weighting and risk weighting. No ticker is selected using its
September realized profit. Rules are in [the frozen experiment](experiment.md).

**Breakout** retains the original C3 signal: within 4% of the prior 55-session
high, positive 20-session return and efficiency >=0.15. It tests whether lower
friction and less allocation churn improve the retention baseline.

**Relative strength** requires positive 20/60-session returns and a 60-session
return above SET50. Scores are relative return divided by daily volatility.
Its profits stay invested until trend failure, loss stop, risk reduction or a
trailing stop based on the highest prior daily close since entry (after five
sessions). This is intended to avoid repeatedly selling a persistent winner;
it can give back profits during reversals.

**Defensive pullback** requires annualized downside deviation below 25%, beta
below one, and a five-session return between -4% and +1.5%. The inherited
above-60-session-average and 20-session deterioration checks remain. Low beta
is an exposure characteristic, not proof that a stock will profit.

**Weighting:** equal allocation versus inverse downside deviation with a bounded
0.75–1.25 score-rank multiplier and a 10% annualized downside floor. Position,
sector and liquidity capacities still constrain weights. The old negative
five-day quality estimate is not used to assert a profit probability. For
compatibility the risk-weighted config suffix is `quality`; reports call it risk.

## Costs and risk

Reject entries whose prior-close one-tick round-trip price impact plus commissions
and VAT exceeds 1.5%. This is a cost screen, not a forecast that remaining stocks
will cover costs. Ordinary allocation decreases no longer force sales. Explicit
trend/volatility exits and live drawdown reductions remain active. Actual name,
sector and exposure breaches request reductions even when retention or a
rebalance band would otherwise hold. Reductions depend on available fills;
prices and asynchronous marks can still exceed limits.

The existing hard guard can reduce exposure below the eligibility threshold.
It is retained rather than hiding that conflict. Forcing 50% exposure into weak
signals can make a strategy eligible on exposure while worsening both payoff
and total return. No final-period SET50 drawdown enters live decision rules.

## What would count as verified improvement

Use net total P&L including unsold losses, excess return, daily and initial-capital
drawdown, exposure, fees and completed FIFO payoff together. Review all variants,
not just the best one. Independent daily ledger reconciliation verifies accounting,
not predictive ability. FIFO lots are dependent fragments of position episodes;
large lot counts do not imply equally many independent observations.

September is already reused for development and cannot be relabeled a holdout.
Six more variants increase selection bias. These are mechanism tests with frozen
thresholds, not reliable estimates of win probability. Before promotion obtain
new permitted dates, dated SET50 membership and confirmed rules, then evaluate
a frozen candidate with cost stress and matched-exposure controls. Historical
indicator values alone cannot verify a high probability of profitable trades.
