import requests
import re
from bs4 import BeautifulSoup
# =========================================================
# SETTINGS
# =========================================================
PIVAN_BASE = "https://pivan.co"
TIMEOUT = 30
# =========================================================
# CHANNEL FACTORIES
# =========================================================
CHANNEL_FACTORIES = [
    # -----------------------------------------------------
    # ناودانی سبک
    # -----------------------------------------------------
    {
        "key": "سبک ناب",
        "name": "ناودانی سبک ناب تبریز",
        "type": "سبک",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        )
    },
    {
        "key": "سبک شکفته",
        "name": "ناودانی سبک شکفته",
        "type": "سبک",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        )
    },
    # -----------------------------------------------------
    # ناودانی سنگین
    # -----------------------------------------------------
    {
        "key": "سنگین ناب",
        "name": "ناودانی سنگین ناب تبریز",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "tabriz-pure-steel/uchannel/"
        )
    },
    {
        "key": "سنگین فایکو",
        "name": "ناودانی سنگین فایکو",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "iranian-alborz-steel-factory-faiko/"
            "uchannel/"
        )
    },
    {
        "key": "سنگین ابهر",
        "name": "ناودانی سنگین ابهر",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "west-alborz-steel-complex-and-factory/"
            "uchannel/"
        )
    },
    {
        "key": "سنگین شکفته",
        "name": "ناودانی سنگین شکفته",
        "type": "سنگین",
        "url": (
            "https://pivan.co/brands/"
            "shekofteh-steel/uchannel/"
        )
    }
]
# =========================================================
# NORMALIZE DIGITS
# =========================================================
def normalize_digits(text):
    if text is None:
        return ""
    text = str(text)
    replacements = {
        "۰": "0",
        "۱": "1",
        "۲": "2",
        "۳": "3",
        "۴": "4",
        "۵": "5",
        "۶": "6",
        "۷": "7",
        "۸": "8",
        "۹": "9",
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text
# =========================================================
# EXTRACT NUMBERS
# =========================================================
def extract_numbers(text):
    text = normalize_digits(text)
    if not text:
        return []
    # -----------------------------------------------------
    # تبدیل جداکننده‌های عددی
    # -----------------------------------------------------
    text = text.replace("٬", ",")
    text = text.replace("،", ",")
    
    # -----------------------------------------------------
    # استخراج عددها
    #
    # مثال:
    # "80,000 تومان"
    # -> ["80,000"]
    #
    # "8,800 تومان"
    # -> ["8,800"]
    # -----------------------------------------------------
    matches = re.findall(
        r"\d[\d,]*",
        text
    )
    numbers = []
    for item in matches:
        item = item.replace(",", "")
        try:
            number = int(item)
            numbers.append(number)
        except Exception:
            continue
    return numbers
# =========================================================
# CLEAN TEXT
# =========================================================
def clean_text(text):
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    return " ".join(
        text.split()
    ).strip()
# =========================================================
# GET PAGE
# =========================================================
def get_page(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        )
    }
    response = requests.get(
        url,
        headers=headers,
        timeout=TIMEOUT
    )
    response.raise_for_status()
    return response.text
# =========================================================
# FIND SIZE
# =========================================================
def find_size(values):
    for value in values:
        numbers = extract_numbers(
            value
        )
        for number in numbers:
            if 6 <= number <= 30:
                return number
    return None
# =========================================================
# FIND LENGTH
# =========================================================
def find_length(values):
    lengths = []
    for value in values:
        numbers = extract_numbers(
            value
        )
        for number in numbers:
            if number in (6, 12):
                lengths.append(
                    number
                )
    if not lengths:
        return None
    # -----------------------------------------------------
    # اگر 12 وجود داشت، اولویت با 12
    # -----------------------------------------------------
    if 12 in lengths:
        return 12
    return 6
# =========================================================
# FIND PRICE
# =========================================================
def find_price(values):
    candidates = []
    for value in values:
        numbers = extract_numbers(
            value
        )
        for number in numbers:
            # -------------------------------------------------
            # قیمت‌های واقعی این بخش معمولاً در این محدوده‌اند.
            #
            # 79,100
            # 79,500
            # 80,000
            # 80,900
            # 83,200
            # 83,600
            # 100,000
            # -------------------------------------------------
            if 10_000 <= number <= 500_000:
                candidates.append(
                    number
                )
    if not candidates:
        return None
    # -----------------------------------------------------
    # معمولاً آخرین عدد معتبر موجود در سلول قیمت است.
    # -----------------------------------------------------
    return candidates[-1]
# =========================================================
# PARSE TABLE
# =========================================================
def parse_uchannel_table(
    html,
    factory
):
    soup = BeautifulSoup(
        html,
        "html.parser"
    )
    tables = soup.find_all(
        "table"
    )
    print(
        "TABLE COUNT:",
        len(tables)
    )
    if not tables:
        return []
    # -----------------------------------------------------
    # جدول اول Pivan
    # -----------------------------------------------------
    table = tables[0]
    rows = table.find_all(
        "tr"
    )
    print(
        "SELECTED CHANNEL TABLE: 0"
    )
    print(
        "ROWS:",
        len(rows)
    )
    products = []
    for row in rows:
        cells = row.find_all(
            ["td", "th"]
        )
        if not cells:
            continue
        values = [
            clean_text(
                cell.get_text(
                    " ",
                    strip=True
                )
            )
            for cell in cells
        ]
        row_text = " ".join(
            values
        )
        # -------------------------------------------------
        # Header
        # -------------------------------------------------
        header_words = [
            "سایز",
            "قیمت",
            "طول",
            "وزن",
            "استاندارد"
        ]
        if any(
            word in row_text
            for word in header_words
        ):
            continue
        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------
        size = find_size(
            values
        )
        if size is None:
            continue
        # -------------------------------------------------
        # LENGTH
        # -------------------------------------------------
        length = find_length(
            values
        )
        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------
        price = find_price(
            values
        )
        if price is None:
            print(
                f"SIZE {size}: PRICE NOT FOUND"
            )
            continue
        if length is None:
            length = 12
        product = {
            "size":
                size,
            "length":
                length,
            "price":
                price,
            "factory":
                factory["key"],
            "factory_name":
                factory["name"],
            "type":
                factory["type"]
        }
        products.append(
            product
        )
        print(
            f"SIZE {size} | "
            f"LENGTH {length} | "
            f"PRICE {price:,}"
        )
    return products
# =========================================================
# FETCH FACTORY
# =========================================================
def fetch_factory(
    factory
):
    print()
    print(
        "=" * 70
    )
    print(
        "CHANNEL PRICE"
    )
    print(
        "=" * 70
    )
    print(
        "FACTORY:",
        factory["name"]
    )
    print(
        "TYPE:",
        factory["type"]
    )
    print(
        "URL:",
        factory["url"]
    )
    try:
        html = get_page(
            factory["url"]
        )
        print(
            "HTTP: 200"
        )
        print(
            "LENGTH:",
            len(html)
        )
        prices = parse_uchannel_table(
            html,
            factory
        )
        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------
        unique = {}
        for item in prices:
            key = (
                item["size"],
                item["length"]
            )
            # -------------------------------------------------
            # اگر یک سایز/طول چند بار آمد،
            # آخرین قیمت معتبر را نگه می‌داریم.
            # -------------------------------------------------
            unique[key] = item
        prices = list(
            unique.values()
        )
        prices.sort(
            key=lambda x: (
                x["size"],
                x["length"]
            )
        )
        print(
            "VALID CHANNEL PRODUCTS:",
            len(prices)
        )
        return {
            "key":
                factory["key"],
            "name":
                factory["name"],
            "type":
                factory["type"],
            "url":
                factory["url"],
            "prices":
                prices
        }
    except Exception as e:
        print(
            "FACTORY ERROR:",
            factory["name"],
            e
        )
        return {
            "key":
                factory["key"],
            "name":
                factory["name"],
            "type":
                factory["type"],
            "url":
                factory["url"],
            "prices":
                []
        }
# =========================================================
# MAIN
# =========================================================
def main():
    results = []
    for factory in CHANNEL_FACTORIES:
        result = fetch_factory(
            factory
        )
        results.append(
            result
        )
    # =====================================================
    # FINAL RESULT
    # =====================================================
    print()
    print(
        "=" * 70
    )
    print(
        "FINAL CHANNEL RESULT"
    )
    print(
        "=" * 70
    )
    for factory in results:
        print()
        print(
            f"{factory['key']} -> "
            f"{'ok' if factory['prices'] else 'FAILED'}"
        )
        for item in factory["prices"]:
            print(
                f"ناودانی "
                f"{item['size']} - "
                f"{item['length']} متر : "
                f"{item['price']:,} تومان"
            )
    print()
    print(
        "=" * 70
    )
    return results
# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    main()