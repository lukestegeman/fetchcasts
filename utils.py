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
