from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
import arrow
import datetime
import time
from odoo.exceptions import ValidationError
from odoo import fields
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from pytz import timezone
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


def get_dates(start, end):
    start = str2date(start)
    end = str2date(end)
    if not start or not end:
        raise Exception("Missing start and end.")

    result = []
    c = start
    while c <= end:
        result.append(date2str(c))
        c = c + datetime.timedelta(days=1)
    return result


def ensure_strdate(day):
    return date2str(str2date(day))


def dayofweek(day, month=None, year=None):
    """
    if month and year is None, then day is date
    """
    d = day
    m = month
    y = year
    if not month and not year:
        day = str2date(day)
        d = day.day
        m = day.month
        y = day.year
    del day
    del month
    del year
    if m < 3:
        z = y - 1
    else:
        z = y
    dayofweek = 23 * m // 9 + d + 4 + y + z // 4 - z // 100 + z // 400
    if m >= 3:
        dayofweek -= 2
    dayofweek = dayofweek % 7

    dayofweek -= 1
    if dayofweek == -1:
        dayofweek = 6

    return dayofweek


def get_localized_monthname(month, locale="de_DE"):
    if locale == "de_DE":
        months = [
            "Januar",
            "Februar",
            "März",
            "April",
            "Mai",
            "Juni",
            "Juli",
            "August",
            "September",
            "Oktober",
            "November",
            "Dezember",
        ]
    else:
        raise Exception("implement!")
    return months[month - 1]


def _get_date_ranges(start, end):
    first_of_month = time.strftime("%Y-%m-") + str(1)
    first_of_month = str2date(first_of_month)

    date_start = (first_of_month + relativedelta(months=start)).strftime(
        DEFAULT_SERVER_DATE_FORMAT
    )
    date_end = (first_of_month + relativedelta(months=end)).strftime(
        DEFAULT_SERVER_DATE_FORMAT
    )
    return {
        "date_start": date_start,
        "date_end": date_end,
    }


def is_dst(_date):
    """
    Liefert zu einem Datum bool bei Sommezeit zuruecken, ansonsten
    False fuer Normalzeit/Winterzeit
    """
    year = _date.year

    def get_last_sunday(year, month):
        day = 31
        while True:
            dt = datetime.datetime(year, month, day)
            dow = int(dt.strftime("%w"))
            if dow == 0:
                break
            day = day - 1
        return datetime.datetime(year, month, day)

    normal_time_start = get_last_sunday(year, 10)
    dst_time_start = get_last_sunday(year, 3)

    result = bool(_date >= dst_time_start and _date < normal_time_start)
    return result


def get_day_of_week(dt, lang="de_DE"):
    translations = {
        "de_DE": {
            "Monday": "Montag",
            "Tuesday": "Dienstag",
            "Wednesday": "Mittwoch",
            "Thursday": "Donnerstag",
            "Friday": "Freitag",
            "Saturday": "Samstag",
            "Sunday": "Sonntag",
        }
    }
    result = dt.strftime("%A")
    result = translations.get(lang, {result: result}).get(result, result)
    return result


def convert_to_utc(d, tz="CET"):
    if not d:
        return d
    if is_dst(d):
        d = d - relativedelta(hours=1)
    from_tz = timezone(tz)
    d = from_tz.localize(d)
    d = d.astimezone(timezone("utc")).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    return d


def convert_timezone(from_tz, datestring, to_tz, return_format=False):
    """
    Konvertiert einen datum string von einer zu ner anderen zeitzone
    Eventuell soll noch is_dst verwendet werden s.o.
    """
    if not to_tz:
        to_tz = "UTC"
    if from_tz.upper() != "UTC":
        timezoneoffset = datetime.datetime.now(timezone(from_tz)).strftime("%z")
        datestring = datestring + " " + timezoneoffset
        dt = parse(datestring)
    else:
        utc = datetime.datetime.strptime(datestring, "%Y-%m-%d %H:%M:%S")
        dt = utc.replace(tzinfo=timezone(from_tz))
    return dt.astimezone(timezone(to_tz)).strftime(
        return_format or DEFAULT_SERVER_DATETIME_FORMAT
    )


def get_time_from_float(_float):
    hour = int(_float)
    minutes = _float - hour
    return "%02.0f:%02.0f:00" % (hour, int(round(60.0 * minutes)))


def get_float_from_time(time):
    return float(time[0:2]) + (float(time[3:5]) / 60)


def get_month_list():
    months = []
    for i in range(1, 13):
        months.append((i, datetime.date(2011, i, 1).strftime("%B")))
    return months


def day_of_weeks_list(include_holiday=False):
    days = []
    days.append(("Mo", "Monday"))
    days.append(("Tue", "Tuesday"))
    days.append(("Wed", "Wednesday"))
    days.append(("Th", "Thursday"))
    days.append(("Fr", "Friday"))
    days.append(("Sat", "Saturday"))
    days.append(("Sun", "Sunday"))
    if include_holiday:
        days.append(("Hol", "Holiday"))
    return days


def date_type(d):
    if not d:
        return None

    if isinstance(d, str):
        if len(str) == len("00.00.0000"):
            return "date"
        elif len(str) == len("00.00.0000 00:00:00"):
            return "datetime"

    if isinstance(d, datetime.date):
        return "date"

    if isinstance(d, datetime.datetime):
        return "datetime"


def str2date(string):
    if not string:
        return False
    if isinstance(string, arrow.arrow.Arrow):
        return string.date()
    if isinstance(string, datetime.date):
        return string
    if isinstance(string, datetime.datetime):
        return string.date()
    return parse(string).date()


def str2datetime(string):
    if not string:
        return False
    if isinstance(string, arrow.arrow.Arrow):
        return string.datetime
    if isinstance(string, datetime.datetime):
        return string
    if isinstance(string, datetime.date):
        return datetime(
            datetime.date.year, datetime.date.month, datetime.date.day, 0, 0, 0
        )
    return parse(string)


def date2str(date):
    if not date:
        return False
    if isinstance(date, str):
        return date
    return date.strftime("%Y-%m-%d")


def time2str(thetime):
    if not thetime:
        return False
    if isinstance(date, str):
        return date
    return thetime.strftime("%H-%M-%S")


def str2time(thetime):
    if not thetime:
        return False
    return parse(thetime).time()


def datediff(d1, d2):
    delta = d1 - d2
    return delta.days


def timediff(t1, t2, unit="hours"):
    t1_ms = (t1.hour * 60.0 * 60.0 + t1.minute * 60.0 + t1.second) * 1000.0
    t2_ms = (t2.hour * 60.0 * 60.0 + t2.minute * 60.0 + t2.second) * 1000.0

    delta_ms = max([t1_ms, t2_ms]) - min([t1_ms, t2_ms])

    if unit == "hours":
        return float(delta_ms) / 3600.0 / 1000.0
    else:
        raise NotImplementedError("not implemented unit: %s" % unit)


def datetime2str(time, date_format=False):
    if not time:
        return None
    if isinstance(time, str):
        if len(time) != 10:
            raise Exception(f"Invalid datetime: {time}")
        return time
    if not date_format:
        return time.strftime("%Y-%m-%d %H:%M:%S")
    return time.strftime(date_format)


def date_in_range(date, start, end):
    """
    Checks wether date is between start and end;
    start, end can be string or python date

    if start is False, then start will be 01.01.1980
    if end is False, then End will be 31.12.2100
    """
    if isinstance(start, (datetime.date, datetime.datetime)):
        start = date2str(start)
    if isinstance(end, (datetime.date, datetime.datetime)):
        end = date2str(end)
    if isinstance(date, (datetime.date, datetime.datetime)):
        date = date2str(date)

    if not date:
        raise Exception("date is not given - cannot determine range")

    if not start:
        start =         datetime.min.strftime("%Y-%m-%d")
    if not end:
        end =         datetime.max.strftime("%Y-%m-%d")

    return date >= start and date <= end

def datetime_in_range(date, start, end):
    """
    Checks wether date is between start and end;
    start, end can be string or python date

    if start is False, then start will be 01.01.1980
    if end is False, then End will be 31.12.2100
    """
    if isinstance(start, (datetime.date, datetime.datetime)):
        start = datetime2str(start)
    if isinstance(end, (datetime.date, datetime.datetime)):
        end = datetime2str(end)
    if isinstance(date, (datetime.date, datetime.datetime)):
        date = datetime2str(date)

    if not date:
        raise Exception("date is not given - cannot determine range")

    if not start:
        start =         datetime.min.strftime("%Y-%m-%d")
    if not end:
        end =         datetime.max.strftime("%Y-%m-%d")

    return date >= start and date <= end

def todatetime(d):
    if isinstance(d, (datetime.datetime,)):
        return d
    if isinstance(d, str):
        return str2datetime(d)
    raise NotImplementedError(d)


def todate(d):
    if isinstance(d, (datetime.date,)):
        return d
    if isinstance(d, str):
        return str2date(d)
    raise NotImplementedError(d)


def date_range_overlap(date_range1, date_range2):
    date_range1 = list(map(date2str, date_range1))
    date_range2 = list(map(date2str, date_range2))
    return _date_range_overlap(date_range1, date_range2)


def datetime_range_overlap(date_range1, date_range2):
    date_range1 = list(map(datetime2str, date_range1))
    date_range2 = list(map(datetime2str, date_range2))
    return _date_range_overlap(date_range1, date_range2)


def _date_range_overlap(date_range1, date_range2):
    """
    Prueft, ob sich die angegebenen Datumsbereiche ueberschneiden

    :param date_range1:  Tuple (from, to)
    :param date_range2:  Tuple (from, to)
    :returns True or False:

    """
    d1 = date_range1
    d2 = date_range2

    assert all([isinstance(x, (list, tuple)) for x in [d1, d2]])
    assert all([len(x) == 2 for x in [d1, d2]])

    MIN = "1980-01-01"
    MAX = "2100-01-01"

    if not d1[0]:
        d1[0] = MIN
    if not d2[0]:
        d2[0] = MIN
    if not d1[1]:
        d1[1] = MAX
    if not d2[1]:
        d2[1] = MAX

    assert all([x[0] <= x[1] for x in [d1, d2]])

    if date_in_range(d1[0], d2[0], d2[1]):
        return True
    if date_in_range(d2[0], d1[0], d1[1]):
        return True
    if date_in_range(d1[1], d2[0], d2[1]):
        return True
    if date_in_range(d2[1], d1[0], d1[1]):
        return True
    if d1[0] < d2[0] and d1[1] > d2[1]:
        return True
    if d2[0] < d1[0] and d2[1] > d1[1]:
        return True
    return False


def clean_milliseconds(date):
    date = str2datetime(date)
    return arrow.get(int(str(arrow.get(date).float_timestamp).split(".")[0]))


def slice_range(start, end, interval):
    """ """
    start = arrow.get(start)
    end = arrow.get(end)
    start = clean_milliseconds(start)
    end = clean_milliseconds(end)

    i = start
    res = set()
    while i < end:
        res.add(i.datetime)
        i = i.shift(**{interval: 1})
    return res


def remove_times(start, end, times, filters=None, negative_filters=None):
    """
    times: array of (float start, float end, timezone)
    filters: array of start end tuples; only times within these ranges are taken into account
             (equivalent to working hours from to)
    """
    if end < start:
        raise ValidationError(f"End<Start {start =} {end = }")

    # expects timezone UTC of start and end or naive

    start = arrow.get(start)
    end = arrow.get(end)
    assert str(start.tzinfo) == "tzutc()"
    assert str(end.tzinfo) == "tzutc()"

    minutes = slice_range(start, end, "minutes")

    for positive_filter in filters or []:
        start, stop = tuple(map(arrow.get, positive_filter))
        start = start.to("utc")
        stop = stop.to("utc")
        minutes = set(
            filter(lambda minute: minute >= start and minute <= stop, minutes)
        )

    for negative_filter in negative_filters or []:
        start, stop = tuple(map(arrow.get, negative_filter))
        start = start.to("utc")
        stop = stop.to("utc")
        minutes = set(filter(lambda minute: minute < start or minute > stop, minutes))

    for I, b in enumerate(times):
        tz = b[3]
        days = set(map(lambda x: arrow.get(x).to(tz).date(), minutes))

        for day in days:
            if b[0] != day.weekday():
                continue
            b1 = (
                arrow.get(day).replace(tzinfo=b[3]).shift(hours=b[1]).to("utc").datetime
            )
            b2 = (
                arrow.get(day)
                .replace(tzinfo=b[3])
                .shift(hours=b[2])
                .replace(tzinfo=b[3])
                .to("utc")
                .datetime
            )
            breakintervals = slice_range(b1, b2, "minutes")
            minutes -= breakintervals

    minutes_count = len(minutes)
    return minutes_count


def slices_to_intervals(slices, detect_leap_seconds=60):
    """
    Puts slices into intervals
    """

    result = []

    current_interval = [None, None]
    slices = list(sorted(slices))
    for i in range(len(slices)):
        if current_interval[0] is None:
            current_interval[0] = slices[i]

        if i == len(slices) - 1:
            current_interval[1] = (
                arrow.get(slices[i]).shift(seconds=detect_leap_seconds).datetime
            )
            yield current_interval
            break

        diff = (slices[i + 1] - slices[i]).total_seconds()
        if diff > detect_leap_seconds:
            current_interval[1] = (
                arrow.get(slices[i]).shift(seconds=detect_leap_seconds).datetime
            )
            yield current_interval
            current_interval = [None, None]


def remove_range(interval, range):
    """

    interval: 08:00 - 12:00 range 09:00 - 10:00

    returns:
    08:00 - 08:59:59
    10:00 - 12:00
    """

    i1 = str2datetime(interval[0])
    i2 = str2datetime(interval[1])
    r1 = str2datetime(range[0])
    r2 = str2datetime(range[1])
    I = (i1, i2)
    R = (r1, r2)
    tz = i1.tzinfo

    assert (
        arrow.get(i1).tzinfo
        == arrow.get(i2).tzinfo
        == arrow.get(r1).tzinfo
        == arrow.get(r2).tzinfo
    )

    if not date_range_overlap(I, R):
        return [interval]
    interval_sliced = slice_range(*I, "minutes")
    range_sliced = slice_range(*R, "minutes")
    valid = interval_sliced - range_sliced
    intervals = list(slices_to_intervals(valid, detect_leap_seconds=60))
    intervals = list(
        map(
            lambda x: (
                arrow.get(x[0]).to(tz).datetime,
                arrow.get(x[1]).to(tz).datetime,
            ),
            intervals,
        )
    )
    return intervals


def iterate_dtrange(start, stop, interval="days", inc=1):
    assert interval == "days"

    iterator = start
    calc_start = start
    calc_stop = stop
    while iterator < stop:
        if iterator.strftime(DT) == start.strftime(DT):
            calc_start = start
            calc_stop = calc_start.replace(hour=23, minute=59, second=59)
        else:
            calc_start = iterator.replace(hour=0, minute=0, second=0)
            calc_stop = stop

        yield calc_start, calc_stop
        iterator = arrow.get(iterator).shift(**{interval: inc})


def _inc_business_days(self, start, busdays, step={"days": -1}):
    import numpy as np

    s = start.strftime(DTF)
    start = fields.Date.from_string(s[:10])
    offset = start
    while abs(np.busday_count(offset, start)) < busdays:
        start = start + timedelta(**step)
    return fields.Datetime.from_string(start.strftime(DT) + s[10:])
