from datetime import timezone


def pymongo_naive_utc_datetime_to_ms(dt):
    """Assumes that 'dt' is a naive datetime object returned by pymongo.
    Sets the correct tzinfo so that it is converted properly"""
    utc_value = dt.replace(tzinfo=timezone.utc)
    return utc_value.timestamp() * 1000
