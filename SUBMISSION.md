# Property Revenue Dashboard — Debugging Submission

## Summary

This assignment fixes three reported revenue-dashboard defects without rebuilding the application:

| Report | Root cause | Fix | Verification evidence |
|---|---|---|---|
| Sunset Properties' March revenue was incorrect | Month boundaries were treated as naive UTC dates instead of boundaries in the property's timezone | Convert the property's local month start/end to UTC before querying reservations | For `Europe/Paris`, March 2024 resolves to `2024-02-29 23:00 UTC` through `2024-03-31 22:00 UTC`; the boundary reservation is included and the expected total is `$2,250.00` |
| Ocean Rentals sometimes saw another company's revenue after refresh | The revenue cache key used only `property_id`, allowing identical property IDs from different tenants to share cached data | Scope cache reads and writes with both `tenant_id` and `property_id`; also require tenant filtering in every revenue query | The same `prop-001` request now creates different keys for `tenant-a` and `tenant-b` |
| Finance totals were occasionally off by cents | Revenue was handled with binary floating-point arithmetic and inconsistent rounding | Keep values as `Decimal` and apply `ROUND_HALF_UP` at the currency boundary | Regression check: `333.325` becomes `333.33` |

The fix also repairs the async database-session configuration so revenue queries execute against the configured database rather than silently relying on placeholder data.

## Files changed

- `backend/app/services/cache.py` — tenant-safe cache keys and graceful cache-failure handling.
- `backend/app/services/reservations.py` — tenant-filtered queries, timezone-aware monthly boundaries, and decimal money calculations.
- `backend/app/core/database_pool.py` — valid async SQLAlchemy engine and session setup.
- `backend/app/api/v1/dashboard.py` — required tenant context and currency-boundary rounding.
- `frontend/src/components/Dashboard.tsx` — tenant-specific property selection.
- `DEBUGGING_NOTES.md` — detailed investigation notes and reproduction commands.

## Verification completed

- Python syntax compilation passed for every changed backend module.
- Focused regression checks passed for timezone boundaries, tenant cache isolation, and half-up currency rounding.

Full UI verification still requires the Docker stack to finish building and both demo accounts to be exercised. Do not claim the end-to-end demonstration as passed until the screenshots below are captured.

## Screenshot checklist

Capture these in this order and give each image a short caption:

1. **Sunset Properties login and dashboard** — sign in as `manager@sunset.com`, select `prop-001`, and show the revenue result.
2. **Sunset refresh check** — refresh the page and show that the same tenant's data remains visible.
3. **Ocean Rentals isolation check** — sign out, sign in as `admin@oceanrentals.com`, select `prop-001`, and show that Sunset's `$2,250.00` is not displayed.
4. **Cache-key fix** — show the `tenant_id` and `property_id` components in `backend/app/services/cache.py`.
5. **Timezone and rounding fixes** — show the local-to-UTC month boundaries and `Decimal`/`ROUND_HALF_UP` logic in `backend/app/services/reservations.py`.

Demo passwords are documented in the assignment repository. Keep passwords out of screenshots and the final PR description.

## Loom script (5–7 minutes)

**0:00–0:30 — Introduction**  
“This was a debugging exercise for three reported revenue problems: a March total mismatch, cross-tenant data leakage after refresh, and cent-level rounding errors.”

**0:30–1:40 — March calculation**  
Show the seed reservation near the month boundary. Explain that March must be interpreted in the property's timezone, not as naive UTC dates. Show the updated local-month-to-UTC calculation and the `$2,250.00` expected result.

**1:40–3:00 — Tenant isolation**  
Show the old risk: a cache key containing only `property_id`. Then show the new `tenant_id:property_id` key and the tenant condition in the database query. Demonstrate Sunset, refresh, then Ocean using the same property ID.

**3:00–4:10 — Money rounding**  
Explain that floats cannot reliably represent decimal currency. Show the `Decimal` calculation and `ROUND_HALF_UP`, then mention the regression value `333.325 → 333.33`.

**4:10–5:30 — Verification**  
Show the two tenant dashboards and the focused checks. Mention the database-session repair and that Redis failure no longer breaks the revenue calculation.

**5:30–6:00 — Close**  
“The result is timezone-correct revenue, tenant-isolated caching and querying, and deterministic currency rounding, implemented within the existing application structure.”

## Copy-ready pull request description

### What changed

Fixed the three revenue-dashboard defects described in the assignment:

- made monthly revenue boundaries timezone-aware;
- isolated cached and queried revenue by tenant;
- replaced floating-point money handling with decimal half-up rounding;
- repaired async database-session configuration;
- limited the dashboard's property choices to the active tenant.

### How it was verified

- backend syntax compilation;
- focused timezone-boundary regression check;
- tenant-specific cache-key check;
- decimal rounding regression check.

### Final check before submission

- manually verify the dashboard with both supplied demo accounts;
- attach the screenshots and Loom link.

### Evidence

Attach the five screenshots listed in `SUBMISSION.md` and include the Loom link here.
