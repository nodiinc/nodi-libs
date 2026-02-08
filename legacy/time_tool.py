from datetime import datetime, timedelta, timezone
from time import strftime, localtime
import pytz

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

def get_current_timestamp(format: str=TIMESTAMP_FORMAT, decimal: int=0) -> str:
    current_time = datetime.now()
    if decimal > 0:
        format += f".%f"
        timestamp = current_time.strftime(format)
        timestamp_with_decimal = timestamp[:-(6 - decimal)]
        return timestamp_with_decimal
    else:
        timestamp = current_time.strftime(format)
        return timestamp

def seconds_to_isotimestamp(seconds: int, exponent: int=0) -> str:
    seconds = seconds / (10 ** exponent)
    dt_object = datetime.fromtimestamp(seconds)
    isotimestamp = dt_object.isoformat() + 'Z'
    return isotimestamp

def isotimestamp_to_seconds(isotimestamp: str, exponent: int=0) -> int:
    if isotimestamp.endswith('Z'):
        isotimestamp = isotimestamp[:-1]
    dt_object = datetime.fromisoformat(isotimestamp)
    seconds = dt_object.timestamp()
    seconds = int(seconds * (10 ** exponent))
    return seconds

def seconds_to_timestamp(seconds: int, exponent: int=0,
                         format: str=TIMESTAMP_FORMAT) -> str:
    seconds = seconds / (10 ** exponent)
    dt_object = datetime.fromtimestamp(seconds)
    timestamp = dt_object.strftime(format)
    return timestamp

def timestamp_to_seconds(timestamp: str, exponent: int=0) -> int:
    dt_object = datetime.fromisoformat(timestamp)
    seconds = dt_object.timestamp()
    seconds = int(seconds * (10 ** exponent))
    return seconds

def convert_isotimestamp_timezone(isotimestamp: str, from_tz: str, to_tz: str) -> str:
    if isotimestamp.endswith('Z'):
        isotimestamp = isotimestamp[:-1]
    dt_object = datetime.fromisoformat(isotimestamp)
    from_timezone = pytz.timezone(from_tz)
    from_datetime = from_timezone.localize(dt_object)
    to_timezone = pytz.timezone(to_tz)
    to_datetime = from_datetime.astimezone(to_timezone)
    return to_datetime.isoformat()

def convert_timestamp_timezone(timestamp: str, from_tz: str, to_tz: str) -> str:
    dt_object = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
    from_timezone = pytz.timezone(from_tz)
    from_datetime = from_timezone.localize(dt_object)
    to_timezone = pytz.timezone(to_tz)
    to_datetime = from_datetime.astimezone(to_timezone)
    to_timestamp = to_datetime.strftime(TIMESTAMP_FORMAT)
    return to_timestamp

def convert_seconds_timezone(seconds: int, from_tz: str, to_tz: str) -> int:
    dt_object = datetime.fromtimestamp(seconds, timezone.utc)
    from_timezone = pytz.timezone(from_tz)
    from_datetime = dt_object.astimezone(from_timezone)
    to_timezone = pytz.timezone(to_tz)
    to_datetime = from_datetime.astimezone(to_timezone)
    to_seconds = int(to_datetime.timestamp())
    return to_seconds

def convert_timestamp_format(timestamp: str, format: str=TIMESTAMP_FORMAT):
    dt_object = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
    new_timestamp = dt_object.strftime(format)
    return new_timestamp

def check_vaild_seconds(seconds: int):
    try:
        datetime.fromtimestamp(seconds)
        return True
    except ValueError:
        return False

def check_vaild_timestamp(timestamp: int):
    try:
        datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        return True
    except ValueError:
        return False

def split_by_days(from_time: str, to_time: str) -> list[list]:
    
    # Create results list
    results = []
    
    # Convert string to datetime
    from_dt_object = datetime.strptime(from_time, TIMESTAMP_FORMAT)
    to_dt_object = datetime.strptime(to_time, TIMESTAMP_FORMAT)
    
    # Get starting date and run in loop
    this_date = from_dt_object.date()
    while this_date <= to_dt_object.date():
        
        # Get start/end time of this date
        start_time = datetime.combine(this_date, datetime.min.time())
        end_time = datetime.combine(this_date, datetime.max.time())
        
        # Exceptional processing for from/to date
        if this_date == from_dt_object.date():
            start_time = from_dt_object
        if this_date == to_dt_object.date():
            end_time = to_dt_object
        
        # Convert datetime to string
        start_timestamp = start_time.strftime(TIMESTAMP_FORMAT)
        end_timestamp = end_time.strftime(TIMESTAMP_FORMAT)
        
        # Add to results list
        results.append([start_timestamp, end_timestamp])
        
        # Move to next date
        this_date += timedelta(days=1)
    
    return results

if __name__ == '__main__':
    # print(convert_timestamp_format('2024-06-07 10:11:12', '%Y%m%d-%H%M%S'))
    print(isotimestamp_to_seconds('2024-11-26T00:00:00Z', 9))

    # 1732579800000000000
    # 1732546800000000000