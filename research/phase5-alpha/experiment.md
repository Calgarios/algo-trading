# Cost-aware retention and stock-selection experiment

Declared before new replay outcomes, 8 November 2026. Six variants, no sweep:
breakout / relative / defensive, each equal and risk weighted (`quality` config
label is retained for compatibility). September is reused development data.

Staged strategy SHA-256: c8ae7b5c7bfc1fbe88696e3eadac273abb761d1c7017c432cca3be5cc9f06972

All variants preserve the retention source and add: at most 1.5% estimated
round-trip friction at prior close; hold through allocation reductions unless
an explicit exit or risk limit applies; enforce actual position, sector and
exposure reductions. These are bundled engineering changes; attribution to any
single change is unavailable. Prices moving after checks can exceed caps.

- Breakout: original C3 stock conditions and profit/stop rules.
- Relative strength: positive 20/60-session return and 60-session excess versus
  SET50; remove fixed profit harvesting and use a 2.5 ATR / minimum 3% trailing
  prior-close stop after five sessions. Intended to let sustained winners run.
- Defensive pullback: downside volatility below 25% annualized, beta below one,
  five-session return between -4% and +1.5%, existing trend filter; original profit exits.

Every variant uses all 48 supplied names as candidates, existing liquidity,
volatility, trend, history checks, 8% name / 25% sector caps, 20% minimum cash,
80% maximum exposure and existing drawdown guards. No fabricated 50-name claim.
Weighted sizing uses inverse downside volatility times a bounded score rank,
without interpreting the old negative five-day calibration as profitable evidence.

Acceptance: official Best Alpha gates, >5 FIFO trips, full net P&L (including
open positions), daily ledger reconciliation. Compare retained C3 and C4 and SET50.
Report all six outcomes and exposure differences; no causal matched-risk claim.
Do not change thresholds after seeing results. A passing sample still needs new
permitted dates and effective-dated membership before a promotion claim.

Replay: `.venv/bin/python scripts/run_alpha_experiment.py --output artifacts/alpha-v1`

Initial alpha-v1 attempt failed during syntax checking before any replay. Corrected the source and froze this hash before alpha-v2.
