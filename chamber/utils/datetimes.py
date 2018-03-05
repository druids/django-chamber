from copy import copy
from datetime import datetime, time, timedelta

from django.utils import timezone
from django.utils.timezone import utc


def range_for_today():
    return range_for_day(datetime.today())


def range_for_day(day):
    return (datetime.combine(day, time.min).replace(tzinfo=utc),
            datetime.combine(day, time.max).replace(tzinfo=utc))


def range_for_month_by_day(day):
    start = copy(day).replace(day=1)
    return (datetime.combine(start, time.min).replace(tzinfo=utc),
            datetime.combine(day, time.max).replace(tzinfo=utc))


def range_for_current_month():
    return range_for_month_by_day(datetime.today())


def range_for_last_24_hours(now=datetime.now(tz=utc)):
    return (now - timedelta(hours=24), now)


def make_naive(datetime_object):
    return (timezone.make_naive(datetime_object, timezone.get_default_timezone())
            if timezone.is_aware(datetime_object) else datetime_object)


def make_aware(datetime_object):
    return timezone.make_aware(datetime_object, timezone.get_default_timezone())


def date_to_datetime(date_object):
    return make_aware(datetime(year=date_object.year, month=date_object.month, day=date_object.day, hour=12))


def aware_datetime(*args, **kwargs):
    return make_aware(datetime(*args, **kwargs))
