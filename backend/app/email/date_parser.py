from email.utils import parsedate_to_datetime
from datetime import datetime

def parse_email_date(date_str: str) -> datetime | None:
    try:
        dt = parsedate_to_datetime(date_str)
        if dt and dt.tzinfo:
            dt = dt.replace(tzinfo=None)  
        return dt
    except Exception as e:
        print("⚠️ Date parse failed:", date_str, e)
        return None
