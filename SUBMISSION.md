# Property Revenue Dashboard — Submission

## Issues found and fixed

### 1. Incorrect March revenue

Monthly boundaries were calculated without the property's timezone, which excluded reservations close to the start or end of a month. The calculation now builds the month in the property's local timezone and converts the boundaries to UTC for the database query.

### 2. Revenue exposed between clients

The cache key contained only the property ID, so properties with the same ID could share cached revenue across tenants. Cache keys and database queries are now scoped by both tenant ID and property ID.

### 3. Totals off by a few cents

Revenue used floating-point arithmetic, which is unsafe for currency. Calculations now use `Decimal` values with consistent half-up rounding to two decimal places.

## Additional fix

The async database-session configuration was corrected so the revenue service uses the configured database connection properly.

## Verification

- Backend syntax checks passed.
- Timezone, tenant-isolation, and currency-rounding regression checks passed.
- The existing application structure was preserved.

## Screenshots

_Add the final dashboard verification screenshots here._
