import requests
import re
import json
from html import unescape
from datetime import datetime, timezone
from urllib.parse import urljoin


# =========================================================
# SETTINGS
# =========================================================

URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://pivan.co/brands/khorasan-steel-neishabour/rebar/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


session = requests.Session()
session.headers.update(HEADERS)


# =========================================================
# TEXT / NUMBER HELPERS
# =========================================================

def clean(text):
    if text is None:
        return ""

    text = unescape(str(text))

    text = re.sub(
        r"<[^>]+>",
        "",
        text
    )

    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")

    return " ".join(
        text.split()
    ).strip()


def normalize_digits(text):
    """
    تبدیل اعداد فارسی و عربی به انگلیسی
    """

    if text is None:
        return ""

    text = str(text)

    translation = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(
        translation
    )


def price_value(text):
    """
    تبدیل متن قیمت به عدد

    مثال:
    71,800
    ۷۱,۸۰۰
    71,800 تومان

    خروجی:
    71800
    """

    if text is None:
        return None

    text = clean(text)
    text = normalize_digits(text)

    if text in (
        "",
        "-",
        "—",
        "–",
        "null",
        "None",
        "تماس بگیرید"
    ):
        return None

    digits = re.sub(
        r"[^\d]",
        "",
        text
    )

    if not digits:
        return None

    try:
        return int(digits)

    except Exception:
        return None


# =========================================================
# GENERIC HTML TABLE
# =========================================================

def extract_table_rows(html):

    rows = re.findall(
        r"<tr\b[^>]*>(.*?)</tr>",
        html,
        flags=re.I | re.S
    )

    result = []

    for row in rows:

        cells = re.findall(
            r"<td\b[^>]*>(.*?)</td>",
            row,
            flags=re.I | re.S
        )

        values = [
            clean(cell)
            for cell in cells
        ]

        if values:
            result.append(values)

    return result


# =========================================================
# KHORASAN STEEL OTHER PRODUCTS
# =========================================================

def extract_products(html, source_page):

    rows = extract_table_rows(
        html
    )

    products = []

    for values in rows:

        if len(values) < 5:
            continue

        factory = clean(values[0])
        size = clean(values[1])
        yesterday = clean(values[2])
        today = clean(values[3])
        description = clean(values[4])

        if not factory or not size:
            continue

        if "قیمت دیروز" in yesterday:
            continue

        if "قیمت امروز" in today:
            continue

        if factory == "میلگرد":
            continue

        if "قیمت ها با احتساب" in factory:
            continue

        old_price = price_value(
            yesterday
        )

        new_price = price_value(
            today
        )

        if old_price is None and new_price is None:
            continue

        products.append({
            "factory": factory,
            "size": size,
            "yesterday": old_price,
            "today": new_price,
            "description": description,
            "source_page": source_page
        })

    return products


# =========================================================
# PIVAN
# =========================================================

def extract_pivan_price_from_cell(cell_html):
    """
    پیوان در HTML دو قیمت دارد:

    in-tax  = قیمت با ارزش افزوده
    ex-tax  = قیمت قبل از ارزش افزوده

    ما فقط ex-tax را مبنا قرار می‌دهیم.
    """

    # -----------------------------------------------------
    # EX TAX
    # -----------------------------------------------------

    ex_tax_match = re.search(
        r'class=["\'][^"\']*\bex-tax\b[^"\']*["\'][^>]*>(.*?)</(?:span|div|td)>',
        cell_html,
        flags=re.I | re.S
    )

    if ex_tax_match:

        ex_tax_text = clean(
            ex_tax_match.group(1)
        )

        value = price_value(
            ex_tax_text
        )

        if value is not None:
            return value

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    # اگر ساختار HTML تغییر کرد، قیمت موجود در ex-tax
    # را با جستجوی عمومی پیدا می‌کنیم.

    ex_tax_match = re.search(
        r'\bex-tax\b[^>]*>([^<]+)',
        cell_html,
        flags=re.I | re.S
    )

    if ex_tax_match:

        value = price_value(
            ex_tax_match.group(1)
        )

        if value is not None:
            return value

    return None


def extract_pivan_products(html):

    products = []

    # -----------------------------------------------------
    # پیدا کردن جدول قیمت
    # -----------------------------------------------------

    tables = re.findall(
        r"<table\b[^>]*>(.*?)</table>",
        html,
        flags=re.I | re.S
    )

    print()
    print("=" * 70)
    print("PIVAN PRICE EXTRACTION")
    print("=" * 70)

    print(
        "TABLE COUNT:",
        len(tables)
    )

    for table_index, table_html in enumerate(
        tables,
        start=1
    ):

        rows = re.findall(
            r"<tr\b[^>]*>(.*?)</tr>",
            table_html,
            flags=re.I | re.S
        )

        print(
            f"TABLE {table_index}:",
            len(rows),
            "ROWS"
        )

        for row_html in rows:

            cells = re.findall(
                r"<td\b[^>]*>(.*?)</td>",
                row_html,
                flags=re.I | re.S
            )

            if len(cells) < 5:
                continue

            values = [
                clean(cell)
                for cell in cells
            ]

            # ------------------------------------------------
            # تشخیص ردیف محصول
            # ------------------------------------------------

            size = values[0]
            standard = values[1]
            delivery = values[2]
            unit = values[3]

            if not re.search(
                r"\d+",
                normalize_digits(size)
            ):
                continue

            # فقط کیلوگرم
            if "کیلو" not in unit:
                continue

            # ------------------------------------------------
            # سلول قیمت
            # ------------------------------------------------

            price_cell = cells[4]

            price = extract_pivan_price_from_cell(
                price_cell
            )

            if price is None:

                # fallback از متن سلول
                price = price_value(
                    values[4]
                )

            if price is None:
                continue

            # ------------------------------------------------
            # محدود کردن به سایزهای واقعی
            # ------------------------------------------------

            size_normalized = normalize_digits(
                size
            )

            size_match = re.search(
                r"\d+",
                size_normalized
            )

            if not size_match:
                continue

            size_number = int(
                size_match.group()
            )

            if size_number < 8 or size_number > 40:
                continue

            # ------------------------------------------------
            # محصول
            # ------------------------------------------------

            product = {
                "factory": "فولاد خراسان نیشابور",
                "size": str(size_number),
                "standard": standard,
                "delivery": delivery,
                "unit": unit,
                "today": price,
                "yesterday": None,
                "description": "",
                "source_page": URLS["میلگرد نیشابور"],
                "price_type": "ex-tax",
                "tax_included": False
            }

            products.append(
                product
            )

            print(
                f"FOUND | سایز {size_number} | "
                f"{price:,} تومان | "
                f"قبل از ارزش افزوده"
            )

    return products


# =========================================================
# PIVAN PREVIOUS PRICE
# =========================================================

def load_old_prices():

    filename = "prices.json"

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        old_prices = {}

        for item in data.get(
            "prices",
            []
        ):

            factory = item.get(
                "factory"
            )

            size = item.get(
                "size"
            )

            today = item.get(
                "today"
            )

            if not factory or not size:
                continue

            if today is None:
                continue

            key = (
                factory,
                str(size)
            )

            old_prices[key] = today

        return old_prices

    except Exception:

        return {}


# =========================================================
# PIVAN FETCH
# =========================================================

def fetch_pivan():

    url = URLS[
        "میلگرد نیشابور"
    ]

    print()
    print("=" * 70)
    print("FETCH PIVAN")
    print("=" * 70)

    print(
        "URL:",
        url
    )

    try:

        response = session.get(
            url,
            timeout=30
        )

        print(
            "HTTP:",
            response.status_code
        )

        print(
            "LENGTH:",
            len(response.text)
        )

        response.raise_for_status()

        html = response.text

        products = extract_pivan_products(
            html
        )

        return products

    except Exception as e:

        print(
            "PIVAN ERROR:",
            e
        )

        return []


# =========================================================
# FETCH KHORASAN OTHER PRODUCTS
# =========================================================

def fetch_khorasan_other():

    url = URLS[
        "میلگرد سایر کارخانجات"
    ]

    print()
    print("=" * 70)
    print("FETCH KHORASAN STEEL")
    print("=" * 70)

    print(
        "URL:",
        url
    )

    try:

        response = session.get(
            url,
            timeout=30
        )

        print(
            "HTTP:",
            response.status_code
        )

        print(
            "LENGTH:",
            len(response.text)
        )

        response.raise_for_status()

        products = extract_products(
            response.text,
            "میلگرد سایر کارخانجات"
        )

        print(
            "FOUND:",
            len(products)
        )

        return products

    except Exception as e:

        print(
            "KHORASAN ERROR:",
            e
        )

        return []


# =========================================================
# CALCULATE CHANGE
# =========================================================

def calculate_change(
    yesterday,
    today
):

    if yesterday is None:
        return 0.0

    if today is None:
        return 0.0

    if yesterday == 0:
        return 0.0

    return round(
        (
            (today - yesterday)
            / yesterday
        ) * 100,
        2
    )


# =========================================================
# NORMALIZE PRODUCT
# =========================================================

def normalize_product(
    product,
    old_prices
):

    factory = product.get(
        "factory",
        ""
    )

    size = str(
        product.get(
            "size",
            ""
        )
    )

    today = product.get(
        "today"
    )

    key = (
        factory,
        size
    )

    # -----------------------------------------------------
    # اگر قیمت دیروز از فایل قبلی موجود باشد
    # -----------------------------------------------------

    yesterday = product.get(
        "yesterday"
    )

    if yesterday is None:

        yesterday = old_prices.get(
            key
        )

    change = calculate_change(
        yesterday,
        today
    )

    product["factory"] = factory
    product["size"] = size
    product["yesterday"] = yesterday
    product["today"] = today
    product["change_percent"] = change

    return product


# =========================================================
# REMOVE DUPLICATES
# =========================================================

def remove_duplicates(
    products
):

    unique = []
    seen = set()

    for product in products:

        key = (
            product.get(
                "factory"
            ),
            str(
                product.get(
                    "size"
                )
            ),
            product.get(
                "today"
            ),
            product.get(
                "source_page"
            )
        )

        if key in seen:
            continue

        seen.add(
            key
        )

        unique.append(
            product
        )

    return unique


# =========================================================
# SAVE JSON
# =========================================================

def save_json(
    products
):

    data = {
        "source": "Pivan + Khorasan Steel",
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "count": len(products),
        "prices": products
    }

    with open(
        "prices.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    return data


# =========================================================
# PRINT PIVAN SUMMARY
# =========================================================

def print_pivan_summary(
    products
):

    print()
    print("=" * 70)
    print("PIVAN FINAL PRICES")
    print("=" * 70)

    for product in products:

        size = product.get(
            "size"
        )

        today = product.get(
            "today"
        )

        yesterday = product.get(
            "yesterday"
        )

        change = product.get(
            "change_percent",
            0
        )

        if today is None:
            price_text = "نامشخص"
        else:
            price_text = (
                f"{today:,}"
            )

        if yesterday is None:
            old_text = "ندارد"
        else:
            old_text = (
                f"{yesterday:,}"
            )

        print(
            f"🏭 فولاد خراسان نیشابور | "
            f"سایز {size} | "
            f"امروز {price_text} | "
            f"دیروز {old_text} | "
            f"تغییر {change}%"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print("STEEL PRICE BOT")
    print("=" * 70)

    # -----------------------------------------------------
    # قیمت‌های قبلی
    # -----------------------------------------------------

    old_prices = load_old_prices()

    print()
    print(
        "OLD PRICES LOADED:",
        len(old_prices)
    )

    all_products = []

    # =====================================================
    # 1. سایر کارخانجات
    # =====================================================

    other_products = fetch_khorasan_other()

    for product in other_products:

        product = normalize_product(
            product,
            old_prices
        )

        all_products.append(
            product
        )

    # =====================================================
    # 2. فولاد خراسان نیشابور از پیوان
    # =====================================================

    pivan_products = fetch_pivan()

    print()
    print(
        "PIVAN PRODUCTS FOUND:",
        len(pivan_products)
    )

    # -----------------------------------------------------
    # اگر پیوان موفق بود
    # -----------------------------------------------------

    if pivan_products:

        for product in pivan_products:

            product = normalize_product(
                product,
                old_prices
            )

            all_products.append(
                product
            )

    else:

        print()
        print(
            "WARNING: PIVAN RETURNED NO PRODUCTS"
        )

        print(
            "NISHABOUR PRODUCTS WILL NOT BE OVERWRITTEN."
        )

        # -------------------------------------------------
        # اگر پیوان قطع بود، اطلاعات قبلی نیشابور
        # را از prices.json حفظ می‌کنیم.
        # -------------------------------------------------

        try:

            with open(
                "prices.json",
                "r",
                encoding="utf-8"
            ) as file:

                old_data = json.load(
                    file
                )

            for product in old_data.get(
                "prices",
                []
            ):

                if product.get(
                    "factory"
                ) == "فولاد خراسان نیشابور":

                    all_products.append(
                        product
                    )

        except Exception:

            pass

    # =====================================================
    # حذف تکراری
    # =====================================================

    all_products = remove_duplicates(
        all_products
    )

    # =====================================================
    # SAVE
    # =====================================================

    data = save_json(
        all_products
    )

    # =====================================================
    # RESULT
    # =====================================================

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        "TOTAL PRODUCTS:",
        len(all_products)
    )

    print(
        "JSON FILE: prices.json"
    )

    print()

    # -----------------------------------------------------
    # خلاصه نیشابور
    # -----------------------------------------------------

    nishabour = [
        p
        for p in all_products
        if p.get("factory")
        == "فولاد خراسان نیشابور"
    ]

    print(
        "NISHABOUR PRODUCTS:",
        len(nishabour)
    )

    print_pivan_summary(
        nishabour
    )

    print()
    print("=" * 70)
    print("SAMPLE ALL PRODUCTS")
    print("=" * 70)

    for product in all_products[:15]:

        print(
            f"{product.get('factory')} | "
            f"سایز {product.get('size')} | "
            f"امروز {product.get('today')} | "
            f"تغییر {product.get('change_percent', 0)}%"
        )

    print()
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()