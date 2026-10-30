# Award eligibility: common criteria versus Best Alpha

Checked 29 October 2026 (Asia/Bangkok). The original
`KGI_ALGO26_Performance_TH.pdf`, page 18, distinguishes:

| Scope | Conditions |
| --- | --- |
| Common performance criteria | Portfolio maximum drawdown <1.5× SET50 maximum drawdown; at least 5 completed FIFO round trips; average closing exposure ≥50%; expected payoff >0 |
| Best Alpha additions | Portfolio total return ≥0 and excess return ≥0 |
| Best Risk Control ranking | Highest Calmar, then excess return, then lowest drawdown, after common criteria |
| Most Active Trader ranking | Highest round-trip count, after common criteria |
| Precision Trader ranking | Highest win rate, after common criteria |

**Positive total return is not a universal common eligibility condition.**
Best Alpha requires a *nonnegative* total return: zero satisfies that particular
condition. Positive expected payoff is a separate requirement concerning
completed trades. A portfolio can have profitable completed trades while its
remaining positions lose money, so both realized and unrealized performance
must remain visible.

Five distinct stocks is a separate trading-participation requirement from the
earlier webpage review, not one of the four common criteria on PDF page 18.
We track it independently and keep it in a conservative combined trading check.
Passing measured criteria does not mean winning a ranking or establish entry
eligibility, registration, organizer acceptance or satisfaction of all rules.

## Source and verification limits

The original PDF was supplied in the user's local `KGI.zip`. This check recovered
the PDF extraction from the **Start algorithm trading project** chat,
`01a17e2b-6e99-7480-a99f-5fbcb1d67677`, command output
`exec-6797cca6-1762-4ebb-9237-fc798b30c0b2`. Its page 18 text was complete;
the recorded PDF SHA-256 prefix is `e2a7d549dfffd969` (only the prefix was logged).
This is a review of the earlier original-source extraction, not a fresh download
of the PDF. The four common thresholds also match the checksum-pinned
TradeSim 0.2.7 `docs/competitor_guide.md`, section 9.

The [competition webpage](https://www.kgieworld.co.th/ApiUniversity/algo-trading/competition)
returned HTTP 403 on this check. Later organizer amendments and interpretation
of zero benchmark drawdown remain unconfirmed. Prize availability and personal
eligibility conditions described on PDF page 17 remain separate from these
performance metrics.
