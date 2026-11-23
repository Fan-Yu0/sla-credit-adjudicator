# SLA Uptime Credit Adjudicator

A reusable GenLayer primitive for machine-to-machine service contracts.

A buyer registers a claim: the vendor's public status page, the uptime the contract
requires, and the billing period. Anyone can trigger an adjudication. Validators fetch
the status page themselves and extract only one number (minutes of unavailability), and
deterministic contract code maps the measured uptime onto the published credit schedule.

The vendor's summary is never trusted, and the credit is not a prompt result - it is
arithmetic over a number every validator independently re-derived from the source.

## Why it needs a judgement layer

An SLA credit is a fact about the outside world: "was the API up, and for how long".
An EVM cannot read a status page, and a single oracle becomes the party that decides
whether the vendor owes money. GenLayer validators each fetch the page, extract the
downtime independently, agree on the number, and only then does the deterministic
schedule price the credit.

## Decision policy

Credit schedule (`sla-credit-v1`), in basis points of the monthly fee:

| Measured uptime | Shortfall vs requirement | Decision | Credit |
| --- | --- | --- | --- |
| at or above the requirement | 0 | `NO_CREDIT` | 0 |
| shortfall <= 10 bps (0.10 pts) | tier 1 | `TIER_1` | 1,000 bps (10%) |
| shortfall <= 50 bps (0.50 pts) | tier 2 | `TIER_2` | 2,500 bps (25%) |
| shortfall > 50 bps | tier 3 | `TIER_3` | 5,000 bps (50%) |
| unreadable or contradictory report, or downtime > period | - | `REVIEW_REQUIRED` | 0 |

Uptime is `((total_minutes - downtime_minutes) * 10000) // total_minutes`, with
`total_minutes = period_days * 1440`. The schedule is fixed by `policy_version`, so a
verdict can be recomputed from public inputs years later.

## Fail-closed evidence handling

If the status page cannot be read, the leader must return the complete fail-closed
payload (`downtime_minutes >= 1_000_000_000` and `consistency == "insufficient"`).
Validators reject a bare claim, a wrong consistency label, or a malformed payload, and
a downtime larger than the period is routed to review rather than priced as a credit.

## Contract interface

| Function | Type | Notes |
| --- | --- | --- |
| `register_claim(claim_id, vendor, status_url, required_uptime_bps, period_days)` | write | validates id length, https URL, 1..10000 bps, 1..366 days |
| `assess(claim_id)` | write | permissionless re-assessment; runs the consensus read |
| `withdraw(claim_id)` | write | publisher only |
| `get_claim(claim_id)` | view | full record including uptime, credit and evidence summary |
| `is_credit_owed(claim_id)` | view | true only when an assessed claim carries credit |
| `policy()` | view | frozen schedule and enum values |

Other contracts consume `is_credit_owed(claim_id)` to release escrow or accrue a credit.

## Tests

```bash
python -m pytest tests -q
```

Direct-mode tests mock the web fetch and the LLM call to exercise the full leader-side
state machine: SLA met, all three credit tiers, the tier boundary (86 vs 87 minutes),
unreadable sources, contradictory reports, downtime beyond the period, duplicate
registration, invalid periods and publisher-only withdrawal.

## Live deployment

| Field | Value |
| --- | --- |
| Network | GenLayer Studio |
| Contract | `0x024C5EC0B21D9d349A57259e37398a6A16524562` |
| Deploy tx | `0x8617676cc1d9ca9267f8a38e31a7a325ef9925f9c63a6f0dc6cbec355dc67f4b` |
| Explorer | https://explorer-studio.genlayer.com/address/0x024C5EC0B21D9d349A57259e37398a6A16524562 |
| Live result | `TIER_1` - 9980 bps uptime, 86 minutes down of 43200, 1000 bps credit |

See `evidence/live.json` for the captured assessment.
