import requests
import re
from datetime import date
from bs4 import BeautifulSoup
from convertdate import persian
# =========================================================
# SETTINGS
# =========================================================
TIMEOUT = 20
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}
# =========================================================
# CACHE
# =========================================================
_holiday_cache = {}
# =========================================================
# GREGORIAN → JALALI
# =========================================================
def gregorian_to_jalali(g_date):
    """
    Convert Gregorian date to Jalali date.
    """
    year, month, day = persian.from_gregorian(
        g_date.year,
        g_date.month,
        g_date.day
    )
    return (
        f"{year:04d}/"
        f"{month:02d}/"
        f"{day:02d}"
    )
# =========================================================
# GET CURRENT JALALI YEAR
# =========================================================
def get_jalali_year(g_date):
    """
    Return Jalali year for Gregorian date.
    """
    year, _, _ = persian.from_gregorian(
        g_date.year,
        g_date.month,
        g_date.day
    )
    return year
# =========================================================
# FETCH OFFICIAL HOLIDAYS
# =========================================================
def get_official_holidays(year):
    """
    Fetch official Iranian holidays from time.ir.
    """
    global _holiday_cache
    if year in _holiday_cache:
        return _holiday_cache[year]
    url = (
        f"https://www.time.ir/fa/event/list/0/{year}"
    )
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
    except Exception as e:
        print(
            "HOLIDAY FETCH ERROR:",
            type(e).__name__,
            str(e)
        )
        # Fail Safe
        _holiday_cache[year] = None
        return None
    try:
        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )
    except Exception as e:
        print(
            "HOLIDAY HTML ERROR:",
            type(e).__name__,
            str(e)
        )
        _holiday_cache[year] = None
        return None
    holidays = {}
    # =====================================================
    # METHOD 1
    # Search elements containing holiday markers
    # =====================================================
    elements = soup.find_all(
        [
            "tr",
            "li",
            "div",
            "td"
        ]
    )
    for element in elements:
        text = element.get_text(
            " ",
            strip=True
        )
        if not text:
            continue
        # -------------------------------------------------
        # Holiday detection
        # -------------------------------------------------
        holiday_keywords = [
            "تعطیل",
            "تعطیلات",
            "نوروز",
            "عید فطر",
            "عید قربان",
            "عاشورا",
            "تاسوعا",
            "اربعین",
            "شهادت",
            "رحلت",
            "مبعث",
            "غدیر",
            "فطر",
            "قربان",
            "جمهوری اسلامی",
            "پیروزی انقلاب",
            "ولادت حضرت",
            "ولادت امام",
        ]
        if not any(
            keyword in text
            for keyword in holiday_keywords
        ):
            continue
        # -------------------------------------------------
        # Extract Jalali date
        # -------------------------------------------------
        match = re.search(
            rf"({year}/\d{{1,2}}/\d{{1,2}})",
            text
        )
        if not match:
            match = re.search(
                r"(14\d{2}/\d{1,2}/\d{1,2})",
                text
            )
        if not match:
            continue
        holiday_date = match.group(1)
        # -------------------------------------------------
        # Normalize date
        # -------------------------------------------------
        parts = holiday_date.split("/")
        if len(parts) != 3:
            continue
        try:
            normalized_date = (
                f"{int(parts[0]):04d}/"
                f"{int(parts[1]):02d}/"
                f"{int(parts[2]):02d}"
            )
        except Exception:
            continue
        holidays[
            normalized_date
        ] = text
    # =====================================================
    # CACHE
    # =====================================================
    _holiday_cache[year] = holidays
    print(
        f"Official holidays loaded for {year}: "
        f"{len(holidays)}"
    )
    return holidays
# =========================================================
# GET HOLIDAY NAME
# =========================================================
def get_holiday_name(g_date):
    """
    Return holiday name for a Gregorian date.
    Friday is also considered non-working,
    but this function returns 'جمعه'.
    """
    # -----------------------------------------------------
    # Friday
    # Python:
    # Monday = 0
    # Friday = 4
    # -----------------------------------------------------
    if g_date.weekday() == 4:
        return "جمعه"
    # -----------------------------------------------------
    # Jalali date
    # -----------------------------------------------------
    jalali_date = gregorian_to_jalali(
        g_date
    )
    # -----------------------------------------------------
    # Year
    # -----------------------------------------------------
    jalali_year = get_jalali_year(
        g_date
    )
    # -----------------------------------------------------
    # Holidays
    # -----------------------------------------------------
    holidays = get_official_holidays(
        jalali_year
    )
    # -----------------------------------------------------
    # If holiday source failed
    # -----------------------------------------------------
    if holidays is None:
        raise RuntimeError(
            "Official holiday calendar "
            "could not be verified."
        )
    return holidays.get(
        jalali_date
    )
# =========================================================
# IS NON-WORKING DAY
# =========================================================
def is_non_working_day(g_date):
    """
    Return True if date is:
    - Friday
    - Official Iranian holiday
    Return False only when the date has been
    successfully verified as a working day.
    """
    # -----------------------------------------------------
    # Friday
    # -----------------------------------------------------
    if g_date.weekday() == 4:
        return True
    # -----------------------------------------------------
    # Official holiday
    # -----------------------------------------------------
    holiday_name = get_holiday_name(
        g_date
    )
    if holiday_name:
        return True
    return False