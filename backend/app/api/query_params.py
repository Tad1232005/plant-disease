"""Shared bounded pagination and explicit UTC time windows."""
from dataclasses import dataclass
from datetime import datetime, timezone
from fastapi import HTTPException, Query


@dataclass(frozen=True)
class TimeWindow:
    start: datetime | None
    end: datetime | None


def time_window(
    start: datetime | None = Query(None, alias="from"),
    end: datetime | None = Query(None, alias="to"),
) -> TimeWindow:
    for value in (start, end):
        if value is not None and value.utcoffset() is None:
            raise HTTPException(status_code=422, detail="Thời gian phải có múi giờ, ví dụ 2026-09-15T00:00:00Z")
    start = start.astimezone(timezone.utc) if start is not None else None
    end = end.astimezone(timezone.utc) if end is not None else None
    if start is not None and end is not None and start >= end:
        raise HTTPException(status_code=422, detail="from phải nhỏ hơn to; khoảng thời gian [from, to)")
    return TimeWindow(start, end)
