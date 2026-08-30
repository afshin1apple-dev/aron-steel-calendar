import holidays


# =========================================================
# IRAN OFFICIAL HOLIDAYS
# =========================================================

IRAN_HOLIDAYS = holidays.country_holidays(
    "IR",
    language="fa"
)


# =========================================================
# CHECK OFFICIAL HOLIDAY
# =========================================================

def is_official_holiday(date=None):

    if date is None:
        from datetime import date
        date = date.today()

    return date in IRAN_HOLIDAYS


# =========================================================
# HOLIDAY NAME
# =========================================================

def get_holiday_name(date=None):

    if date is None:
        from datetime import date
        date = date.today()

    if date not in IRAN_HOLIDAYS:
        return None

    return IRAN_HOLIDAYS.get(date)


# =========================================================
# CHECK NON-WORKING DAY
# =========================================================

def is_non_working_day(date=None):

    if date is None:
        from datetime import date
        date = date.today()

    # Friday
    if date.weekday() == 4:
        return True

    # Official holiday
    if is_official_holiday(date):
        return True

    return False