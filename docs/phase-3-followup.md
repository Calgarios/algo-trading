# Phase 3 follow-up: risk explanation, eligibility and experiments

Updated 29 October 2026 (Asia/Bangkok). Phase 3's local engineering checkpoint
is complete. **No strategy tested here qualifies on all measured prize criteria.**
The changes remain in [PR #5](https://github.com/Calgarios/algo-trading/pull/5),
pending review/merge; no competition submission has been made.

## What controlled risk in the previous run

The original strategy was a transparent, low-turnover reference, not a model
that maximizes returns. Alphabetical selection has no predictive justification.

- Ten names received fixed monthly quantities worth approximately 7% of initial
  capital each at prior-month prices, leaving a 30% target cash allocation.
- Pre-buy checks constrained each stock to 10% of conservative marked NAV,
  total investment to 80%, cash to at least 20%, and holdings to ten names.
  Sales could not exceed actual holdings; purchases included fees and slippage.
- One own-symbol IOC per 15-minute slot, actual-fill reconciliation and fixed
  targets prevented repeated per-tick churn and overlapping pending orders.
- Prior-month history avoided future information in selection and targets.
  No price forecast, volatility model or stop-loss operated in the original run.

Cash reduced market exposure during a falling sample, and low turnover kept
fees at THB 11,837.38. Outperforming SET50 while losing money does not establish
stock-picking alpha or the best achievable return. The limits constrain new
buys; price movements can subsequently breach them. Monthly quantity targets
are not a continuously rebalanced 70% allocation.

## Correction to the eligibility wording

Negative total return alone does **not** fail all prize categories. The scoring
PDF's page 18 lists four common requirements: drawdown, completed round trips,
average exposure and positive expected payoff. Best Alpha additionally requires
total return ≥0 and excess return ≥0. Zero, rather than strictly positive
return, satisfies those Best Alpha additions. Stock participation is a separate
trading rule. See [source review and verification limits](award-criteria.md).

Reporting now assigns an explicit scope to every criterion and reports common
status, stock participation, Best Alpha and other award performance status
separately. Personal eligibility, prize availability, ranking, registration and
organizer acceptance are not inferred from a performance pass.

## Attempts to improve eligibility

Two experiments were declared before their respective results:

1. Keep the original selection and risk limits; exit at estimated net +2%
   profit, net −4% loss, or ten observed trading sessions. Retry partial exits
   from actual holdings and prohibit same-day re-entry after a sell intent.
2. Keep the same exits and risk limits, but select the ten strongest stocks by
   their 20 prior-month closes. This brings one Phase 4 hypothesis forward.

The second selected BCP, PTTGC, CCET, IVL, CRC, PTT, CPF, THAI, TCAP and KKP.
Thresholds were not tuned to find a passing result. No liquidation was forced
at the end of the sample, and realized losses were not excluded from payoff.
The [experiment declaration](phase-3-exit-experiment.md) records the rationale.

All results use the original 16 days, 9–30 September 2026, and all 2,906,167
ticks. SET50 returned −4.099496% with maximum drawdown 4.099496%.

| Requested metric | Retained original reference | Alphabetical + exits | Momentum + exits |
| --- | ---: | ---: | ---: |
| Net return | −2.991564% | −4.227932% | −5.550515% |
| SET50 excess return | +1.107932 pp | −0.128436 pp | −1.451019 pp |
| Official daily-close max drawdown | 2.899616% | 3.794080% | 5.845328% |
| Average daily closing exposure | 69.693722% | 57.033105% | 54.948217% |
| Distinct traded stocks | 10 | 10 | 10 |
| Completed FIFO round trips | 0 | 349 | 378 |
| Expected payoff per completed non-breakeven lot | Undefined | −THB 999.31 | −THB 1,390.41 |
| Commission plus VAT | THB 11,837.38 | THB 59,568.20 | THB 72,956.54 |
| Common criteria | Fail: no completed trades/payoff | Fail: negative payoff | Fail: negative payoff |
| Best Alpha | Fail | Fail | Fail |

Expected payoff for the original is undefined because nothing was closed;
the engine's default display value is 0.00. It is not a passing payoff.
FIFO counts are completed buy lots, often created by small partial fills;
349/378 lots do not mean that many independent trading ideas.

Drawdown here follows the official first-daily-close anchor. Including initial
capital gives 2.991564%, 4.227932% and 5.845328%, respectively. Exposure is the
average of daily closing invested/NAV ratios, not final exposure. Excess
return is a percentage-point difference using the documented official anchors.

The exit-only variant realized −THB 352,136.63 and retained −THB 70,656.57 of
unrealized P&L. The momentum variant realized −THB 525,574.75 and retained
−THB 29,476.78. Their completed-lot win rates were 36.39% and 33.07%, with
average losses larger than average gains. Both passed the measured stock-count,
round-trip, average-exposure and relative-drawdown checks, but negative payoff
still failed the common criteria. Additional turnover raised costs.

**Decision: reject both as replacements; retain the original reference.**
The experiments demonstrate execution and scoring behavior, not eligibility.
Making the software complete cannot guarantee positive expectancy. Keeping
losing positions open solely to improve reported payoff would not establish a
better strategy; realized, unrealized and total returns all remain visible.

## Additional engineering and validation

- 51 tests pass: original contracts, risk/selection scenarios, cost-aware exit
  triggers, holding-period recovery, partial stops, same-day re-entry blocking,
  sell-side tick bands, independent accounting and category-specific criteria.
- All days reconcile through the unchanged official engine for both experiments.
- Two new default-reference replays produce identical deterministic outputs and
  preserve the original reference's economic metrics. The updated outputs also
  bundle the exact strategy/configuration and expose realized/unrealized P&L.
- The original [evidence](phase-3-run-evidence.json) is retained as historical
  evidence for commit `5bc8859`. [Follow-up evidence](phase-3-followup-evidence.json)
  records current source/config hashes, all comparisons and validation scope.

An additional engine quirk surfaced in `tradeSim/Stock.py::from_dict`: a partially
sold lot's displayed market price can be restored using starting volume rather
than remaining volume. Its saved market value is correct. Our pre-buy risk
calculation now uses that saved value for other stocks until fresh quotes arrive;
a regression scenario verifies it. The engine/package bytes are unchanged.

Exit thresholds are checked at decision slots and do not guarantee fill prices
or loss limits. Intraday exit latches are process-local; new daily instances
re-evaluate saved lots. Holding-period exits remain derivable from lot dates and
observed historical sessions. Production restart behavior needs Phase 6 work.

## Where to continue

Phase 3 is complete as an engineering milestone. Phase 4 now has an intact
reference, working trade-lifecycle controls, category-aware reporting and two
recorded negative experiments; it does not start from zero.

1. Review PR #5 and retain the reference/evidence. Defaults remain the original
   alphabetical strategy; both rejected variants are explicit research configs.
2. Establish permitted chronological development/validation data. The September
   sample has already been inspected repeatedly and cannot serve as untouched
   validation. Longer usable tick history and historical membership remain open.
3. Diagnose the negative experiments' entry quality, turnover, realized losses
   and holding periods. Write the next hypothesis and acceptance criteria before
   changing parameters; do not tune only until this sample passes.
4. Compare candidates after all costs and track all seven requested metrics.
   Prioritize positive expected payoff with adequate exposure and controlled
   drawdown; require nonnegative total/excess returns when targeting Best Alpha.
   Promote only with credible chronological evidence and documented limitations.
5. Confirm registered owner, assigned repository, latest CU dates/testing cutoff
   and organizer validator independently. Local results do not constitute an
   accepted submission or a promise of prize eligibility.
