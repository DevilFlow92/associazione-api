from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator


def _strip_tzinfo(v: datetime) -> datetime:
    """Coerce a datetime to tz-naive.

    asyncpg rejects timezone-aware datetimes when the target column is
    ``TIMESTAMP WITHOUT TIME ZONE``. Dropping the tzinfo lets such columns
    accept input that arrives with an offset (e.g. ``2026-06-20T10:00:00+02:00``).
    """
    return v.replace(tzinfo=None) if v.tzinfo else v


# Use for fields mapped to a naive ``DateTime`` column (no ``timezone=True``).
TzNaiveDatetime = Annotated[datetime, AfterValidator(_strip_tzinfo)]
