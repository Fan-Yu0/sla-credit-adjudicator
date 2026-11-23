# November 2026 availability report - Northwind Payments API

Billing period: 2026-11-01 00:00 UTC to 2026-11-30 23:59 UTC (30 days, 43,200 minutes).

## Incident INC-4412

- Start: 2026-11-07 02:14 UTC
- End: 2026-11-07 03:40 UTC
- Duration: 86 minutes of unavailability
- Root cause: primary database failover stalled and the read replicas were promoted late
- Affected scope: card authorisation endpoint in eu-west-1 only

All other days in the billing period were fully available.

Contact: ops@northwind.example
