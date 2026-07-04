import datetime
import dateutil.parser
from django.utils import timezone

def parse_excel_date(date_val):
    """Parse an openpyxl cell value to a date, returning None on failure."""
    if isinstance(date_val, str):
        try:
            return dateutil.parser.parse(date_val).date()
        except (ValueError, TypeError, dateutil.parser.ParserError):
            return None
    elif isinstance(date_val, datetime.datetime):
        return date_val.date()
    elif isinstance(date_val, datetime.date):
        return date_val
    return None

def parse_excel_datetime(date_val):
    """Parse an openpyxl cell value to an aware datetime, returning None on failure."""
    if not date_val:
        return None
    if isinstance(date_val, str):
        try:
            parsed = dateutil.parser.parse(date_val)
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed)
            return parsed
        except (ValueError, TypeError, dateutil.parser.ParserError):
            return None
    elif isinstance(date_val, datetime.date) and not isinstance(date_val, datetime.datetime):
        dt = datetime.datetime.combine(date_val, datetime.time.min)
        return timezone.make_aware(dt)
    elif isinstance(date_val, datetime.datetime):
        if timezone.is_naive(date_val):
            return timezone.make_aware(date_val)
        return date_val
    return None
