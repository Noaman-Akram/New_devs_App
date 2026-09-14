from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
from zoneinfo import ZoneInfo

async def calculate_monthly_revenue(
    property_id: str,
    month: int,
    year: int,
    db_session=None,
    *,
    tenant_id: str,
    property_timezone: str = "UTC",
) -> Decimal:
    """
    Calculates revenue for a specific month.
    """

    if not tenant_id:
        raise ValueError("tenant_id is required for revenue calculations")
    try:
        tz = ZoneInfo(property_timezone)
    except Exception as exc:
        raise ValueError(f"Invalid property timezone: {property_timezone}") from exc

    # Convert local calendar boundaries to UTC instants before querying the
    # timestamptz column.  This correctly handles DST and reservations that
    # cross midnight in the property's local timezone.
    start_date = datetime(year, month, 1, tzinfo=tz).astimezone(dt_timezone.utc)
    if month < 12:
        end_date = datetime(year, month + 1, 1, tzinfo=tz).astimezone(dt_timezone.utc)
    else:
        end_date = datetime(year + 1, 1, 1, tzinfo=tz).astimezone(dt_timezone.utc)
        
    print(f"DEBUG: Querying revenue for {property_id} from {start_date} to {end_date}")

    query = """
        SELECT SUM(total_amount) as total
        FROM reservations
        WHERE property_id = $1
        AND tenant_id = $2
        AND check_in_date >= $3
        AND check_in_date < $4
    """
    
    if db_session is None:
        raise ValueError("db_session is required for monthly revenue calculations")

    # Support asyncpg-style sessions and SQLAlchemy AsyncSession.
    if hasattr(db_session, "fetchval"):
        total = await db_session.fetchval(query, property_id, tenant_id, start_date, end_date)
    else:
        from sqlalchemy import text
        result = await db_session.execute(
            text(query.replace("$1", ":property_id").replace("$2", ":tenant_id").replace("$3", ":start_date").replace("$4", ":end_date")),
            {"property_id": property_id, "tenant_id": tenant_id, "start_date": start_date, "end_date": end_date},
        )
        row = result.fetchone()
        total = row[0] if row else None

    return (Decimal(str(total)) if total is not None else Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for revenue calculations")
    try:
        # Import database pool
        from app.core.database_pool import DatabasePool
        
        # Initialize pool if needed
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text
                
                query = text("""
                    SELECT 
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations 
                    WHERE property_id = :property_id AND tenant_id = :tenant_id
                    GROUP BY property_id
                """)
                
                result = await session.execute(query, {
                    "property_id": property_id, 
                    "tenant_id": tenant_id
                })
                row = result.fetchone()
                
                if row:
                    total_revenue = Decimal(str(row.total_revenue or "0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": str(total_revenue),
                        "currency": "USD", 
                        "count": row.reservation_count
                    }
                else:
                    # No reservations found for this property
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0
                    }
        else:
            raise Exception("Database pool not available")
            
    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        
        # Do not return fabricated values on a database failure: a plausible
        # number from another tenant is a privacy and accuracy incident.
        return {
            "property_id": property_id,
            "tenant_id": tenant_id, 
            "total": "0.00",
            "currency": "USD",
            "count": 0
        }
