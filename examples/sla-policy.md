# SLA credit policy example

A buyer's procurement policy for Northwind Payments API:

- Required monthly uptime: 99.90% (9,990 basis points)
- Billing period: calendar month (30 days = 43,200 minutes)
- Credit schedule (`sla-credit-v1`):

| Uptime | Shortfall | Credit |
| --- | --- | --- |
| >= 99.90% | 0 | no credit |
| 99.80% - 99.89% | <= 0.10 pts | 10% of monthly fee |
| 99.40% - 99.79% | <= 0.50 pts | 25% of monthly fee |
| < 99.40% | > 0.50 pts | 50% of monthly fee |

With the November report above the adjudicator measures 43,200 minutes of window and
86 minutes of downtime, giving 99.80% uptime and a tier-1 credit of 1,000 basis points.
