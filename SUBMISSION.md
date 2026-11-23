# Portal submission

## Category

Builder -> Intelligent Contract

## Description (English, under 1,000 characters)

SLA Uptime Credit Adjudicator is a reusable GenLayer primitive for machine-to-machine service contracts. A buyer registers a claim with the vendor's public status page, the uptime the contract requires (basis points) and the billing period. Anyone can trigger adjudication. Validators independently fetch the status page and extract a single number - minutes of unavailability - then deterministic contract code computes uptime = ((total_minutes - downtime) * 10000) // total_minutes and maps it onto the frozen sla-credit-v1 schedule (10% / 25% / 50% of the monthly fee). Unreadable or contradictory reports, and downtime longer than the period, fail closed to REVIEW_REQUIRED instead of pricing a credit; an unreadable source only validates when the leader returns the complete fail-closed payload. Other contracts consume is_credit_owed(claim_id) to release escrow or accrue a credit. Ships source, 13 direct-mode tests, an SLA policy and a status-page example.

## Live evidence

- Repository: https://github.com/Fan-Yu0/sla-credit-adjudicator
- Status page judged: examples/service-status.md
- Policy: examples/sla-policy.md
- Contract: `0x024C5EC0B21D9d349A57259e37398a6A16524562`
- Deploy transaction: `0x8617676cc1d9ca9267f8a38e31a7a325ef9925f9c63a6f0dc6cbec355dc67f4b`
- Assessment transaction: `0xadc02f8b7c5abd3e9de5b566b4b8ac1ac4705fffd6d2f43d1c887dff191efb73`
- Live result: decision `TIER_1` (2), uptime `9980` bps, downtime `86` minutes of `43200`, credit `1000` bps, `is_credit_owed = true`

## Reviewer checklist

- Persistent state with a clear lifecycle (draft / assessed / withdrawn).
- Publisher-only withdrawal; permissionless re-assessment.
- Validators independently re-fetch the status page.
- The LLM extracts one constrained number; the credit stays arithmetic.
- Unreadable, contradictory or impossible downtime fails closed to review.
- Source, tests and documentation are public.