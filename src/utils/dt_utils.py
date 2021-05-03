"""Store helper functions related to date and time."""

import datetime as dt
from datetime import datetime, timezone, timedelta

DATE_FORMATS = {'en-US': '%m/%d', 'other': '%d/%m'}
# Correspond to 12h + AM/PM and 24h, respectively.
TIME_FORMATS = {'en-US': '%I:%M %p', 'other': '%H:%M'}


def date_to_relative_name(date: dt.date, tz: timezone, locale: str) -> str:
    """Return the relative name of a given date, if possible."""
    today = datetime.now(tz).date()
    relative_date_names = {today - timedelta(days=1): 'yesterday',
                           today: 'today',
                           today + timedelta(days=1): 'tomorrow'}

    if date in relative_date_names:
        return relative_date_names[date]

    return format_date(date, tz, locale)


def format_date(date: dt.date, tz: timezone, locale: str) -> str:
    """Format a date into a user-readable and context-aware representation."""
    if date.year == datetime.now(tz).year:
        return date.strftime(DATE_FORMATS[locale])

    # Only show year info if it's different from the current one.
    return date.strftime(DATE_FORMATS[locale] + '/%Y')


def string_to_date(date: str, tz: timezone, fmt) -> dt.date:
    """Convert a string to a date. If year is needed but not specified by the user,
    the current one is used.
    """

    try:
        return datetime.strptime(date, fmt).date()

    except ValueError:
        date += datetime.strftime(datetime.now(tz), '/%Y')
        output = datetime.strptime(date, fmt).date()
        return output
