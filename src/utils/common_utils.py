from datetime import datetime, timedelta
from typing import Optional, Tuple


def get_date_range(n_days: int, end_date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    if not end_date:
        end_date = datetime.today()
    start_date = end_date - timedelta(days=n_days)
    return start_date, end_date


def get_iso_datetime_format(date_time: datetime) -> str:
    return date_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')


def get_compact_datime_format(iso_date: str) -> str:
    return datetime.strptime(iso_date, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%Y%m%d%H%M%f')


def date_string_format(date_time: datetime) -> str:
    return date_time.strftime('%Y-%m-%d')
