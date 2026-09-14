# Property Revenue Dashboard — investigation notes

## Findings

1. Redis revenue keys used only `property_id`. Because property IDs are scoped
   by tenant (`properties` has a composite primary key), a cached response for
   one company could be returned to another company using the same ID.
2. Monthly revenue was a placeholder that always returned zero. Its sample SQL
   also used naive datetimes, which would classify a reservation around local
   midnight in the wrong month (for example, Paris in the seed data).
3. The database pool referenced settings that do not exist and exposed an async
   session incorrectly, so queries fell into a fabricated mock-data path.
   Returning those values was both inaccurate and unsafe for a multi-tenant
   dashboard.
4. The API converted unrounded database totals directly to `float`, allowing
   sub-cent precision to produce display/reporting discrepancies.
5. The frontend displayed a static list of every company's properties. It now
   limits the selector to the authenticated tenant.

## Changes

- Tenant-scoped Redis keys and graceful cache degradation when Redis is down.
- Real monthly aggregation with tenant filtering, timezone-aware UTC bounds,
  and `Decimal` cent rounding (`ROUND_HALF_UP`).
- Database pool now uses `DATABASE_URL`, SQLAlchemy's async queue pool, and a
  usable session factory.
- Removed fabricated totals on database failure; failures return a safe zero
  result rather than another tenant's plausible number.
- Dashboard totals are rounded before JSON conversion and require a tenant
  context.
- Tenant-aware property selector in the React dashboard.

## Verification

`python3 -m py_compile` passes for all changed backend modules. A regression
check verifies that March 2024 in `Europe/Paris` uses UTC bounds
`2024-02-29T23:00:00Z` through `2024-03-31T22:00:00Z`, includes the tenant in
the query, and rounds `333.325` to `333.33`.

For the required Loom walkthrough, demonstrate both supplied logins, request
`prop-001` in each session (showing tenant-specific results), refresh to prove
the cache does not cross tenants, and explain the timezone/rounding regression.
