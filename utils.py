import datetime

def current_year_and_month():
    today = datetime.date.today()
    return today.year, today.month

def current_yearmonth():
    year, month = current_year_and_month()
    return f"{year:04d}/{month:02d}"

def split_yearmonth(yearmonth, asint=False):
    year, month = yearmonth.split('/')
    if asint:
        year = int(year)
        month = int(month)
    return year, month

def yearmonth_iter(yearmonth_start, yearmonth_end):
    """(year, month) iterator using YYYY/MM format inputs
    
    Note that endpoint is inclusive.
    """
    start_year, start_month = split_yearmonth(yearmonth_start, asint=True)
    end_year, end_month = split_yearmonth(yearmonth_end, asint=True)
    ym_start = 12*start_year + start_month - 1
    ym_end = 12*end_year + end_month
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m+1
