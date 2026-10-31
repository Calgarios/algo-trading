# Phase 4 development diagnostics

Derived from frozen Phase 3 evidence; no new simulation or validation run.

Decision: **retain the engineering reference; revise research**. No candidate is promoted. September remains reused development data.

## Loss attribution

| ID | Net % | Realized THB | Unrealized THB | Fees THB | Fee-added-back % | Traded / initial NAV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | -4.3619 | -43,040.04 | -393,149.65 | 17,949.69 | -4.1824 | 1.0685 |
| C2 | -3.7100 | -14,365.47 | -356,634.30 | 15,459.78 | -3.5554 | 0.9203 |
| C3 | -3.5895 | -25,478.24 | -333,471.95 | 19,905.19 | -3.3905 | 1.1849 |
| C4 | -5.2627 | -32,288.52 | -493,979.27 | 18,002.79 | -5.0826 | 1.0717 |
| C5 | -4.8550 | -47,213.84 | -438,290.57 | 19,214.41 | -4.6629 | 1.1438 |
| T1 | -4.3236 | -13,124.49 | -419,233.44 | 15,515.93 | -4.1684 | 0.9236 |
| T2 | -4.2128 | -21,927.17 | -399,355.21 | 16,227.38 | -4.0506 | 0.9660 |
| T3 | -4.2899 | -71,046.99 | -357,941.55 | 23,953.53 | -4.0503 | 1.4259 |
| T4 | -4.5699 | -87,163.07 | -369,827.21 | 26,261.28 | -4.3073 | 1.5633 |
| T5 | -5.1071 | -172,507.93 | -338,197.89 | 33,162.82 | -4.7754 | 1.9741 |

10/10 remain negative after recorded commission/VAT is added back. Execution prices still include slippage. This is an accounting identity, not a cost-free replay.

Traded notional = fees / 0.0016799, counting buys plus sells, including initial deployment. It is not round-trip turnover. Post-first-day notional and fee stresses are in the JSON.

## Return anchors and completed lots

| ID | Official excess pp | First-close excess pp | Completed lots | Payoff THB | Open partial realized THB |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1 | -0.2624 | -0.7846 | 25 | -1,125.90 | -14,892.49 |
| C2 | 0.3895 | 0.3810 | 5 | -977.95 | -9,475.71 |
| C3 | 0.5100 | -0.2110 | 34 | -603.88 | -4,946.48 |
| C4 | -1.1632 | -1.1880 | 39 | -360.27 | -18,238.17 |
| C5 | -0.7555 | -1.1690 | 39 | -825.33 | -15,026.10 |
| T1 | -0.2241 | 0.0367 | 17 | -472.03 | -5,100.03 |
| T2 | -0.1133 | -0.6543 | 25 | -393.96 | -12,078.18 |
| T3 | -0.1904 | -0.6020 | 61 | -618.61 | -33,311.92 |
| T4 | -0.4704 | 0.2420 | 54 | -654.89 | -51,798.85 |
| T5 | -1.0076 | -0.2543 | 72 | -2,221.38 | -12,568.92 |

Official return includes the portfolio first day, whereas SET50 starts at its first close. The aligned column starts both at the first close; neither is a matched-basket control.

Completed-lot payoff excludes breakeven lots and partial sales of lots still open. Open partial realized P&L is total realized P&L minus completed-lot P&L. Lot counts are not independent investment decisions.

## Largest daily losses

| ID | Session | NAV change THB | Day fees THB | Closing exposure % |
| --- | --- | ---: | ---: | ---: |
| C1 | 2026-09-30 | -192,804.95 | 749.95 | 71.826 |
| C1 | 2026-09-16 | -132,425.00 | 0.00 | 74.899 |
| C1 | 2026-09-11 | -101,491.57 | 236.57 | 74.456 |
| C2 | 2026-09-30 | -193,376.59 | 371.59 | 74.503 |
| C2 | 2026-09-16 | -105,622.24 | 157.24 | 73.877 |
| C2 | 2026-09-29 | -59,544.93 | 69.93 | 75.228 |
| C3 | 2026-09-30 | -198,829.59 | 529.59 | 70.925 |
| C3 | 2026-09-16 | -131,587.07 | 882.07 | 74.909 |
| C3 | 2026-09-11 | -73,309.45 | 284.45 | 75.135 |
| C4 | 2026-09-30 | -210,975.00 | 225.00 | 71.064 |
| C4 | 2026-09-29 | -116,747.47 | 577.47 | 72.141 |
| C4 | 2026-09-11 | -108,637.86 | 362.86 | 75.560 |
| C5 | 2026-09-30 | -215,905.33 | 465.33 | 70.977 |
| C5 | 2026-09-16 | -150,627.11 | 357.11 | 75.635 |
| C5 | 2026-09-11 | -96,310.59 | 445.59 | 75.241 |
| T1 | 2026-09-30 | -203,161.78 | 269.78 | 72.458 |
| T1 | 2026-09-16 | -118,036.20 | 187.20 | 75.058 |
| T1 | 2026-09-29 | -100,941.00 | 0.00 | 74.671 |
| T2 | 2026-09-30 | -225,131.16 | 446.16 | 72.182 |
| T2 | 2026-09-16 | -146,525.00 | 0.00 | 74.832 |
| T2 | 2026-09-11 | -86,971.80 | 371.80 | 75.344 |
| T3 | 2026-09-30 | -224,375.15 | 475.15 | 71.185 |
| T3 | 2026-09-16 | -134,394.42 | 3,464.42 | 75.028 |
| T3 | 2026-09-11 | -113,594.73 | 139.73 | 74.676 |
| T4 | 2026-09-30 | -230,316.90 | 1,399.90 | 70.974 |
| T4 | 2026-09-24 | -95,563.61 | 1,020.61 | 75.367 |
| T4 | 2026-09-29 | -92,161.58 | 637.58 | 75.900 |
| T5 | 2026-09-30 | -219,556.03 | 1,723.03 | 70.991 |
| T5 | 2026-09-29 | -111,321.98 | 1,413.98 | 75.781 |
| T5 | 2026-09-16 | -98,129.62 | 3,406.62 | 75.325 |

Daily P&L uses the preceding close, or initial capital on the first day. All 16 days remain development evidence; these are not separate validation folds.

## Evidence coverage

- C1: symbol/lot diagnostics unavailable.
- C2: symbol/lot diagnostics unavailable.
- C3: symbol/lot diagnostics unavailable.
- C4: symbol/lot diagnostics unavailable.
- C5: symbol/lot diagnostics unavailable.
- T1: symbol/lot diagnostics unavailable.
- T2: symbol/lot diagnostics unavailable.
- T3: symbol/lot diagnostics unavailable.
- T4: symbol/lot diagnostics unavailable.
- T5: symbol/lot diagnostics unavailable.

Raw bundle mode checks committed hashes and reconciles fills, FIFO, cash, holdings and symbol P&L. Without those bundles, symbol/lot attribution and holding ages remain unknown. Intraday adverse excursion and slippage attribution additionally require decision/tick evidence.

The JSON retains every daily observation, both fixed-fill fee stresses, inputs and script hashes. The +25%/+50% fee stresses keep quantities and prices fixed; they do not simulate execution responses.

See [research protocol](../phase-4-research-spec.md) for declared controls, data requirements and acceptance criteria. No fresh engine run or untouched validation is claimed.
