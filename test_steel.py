import requests
import re
import json
from html import unescape
from datetime import datetime, timezone
from urllib.parse import urljoin


URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://khorasan-steel.com/product.php?prd=3",
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
}


session = requests.Session()
session.headers.update(HEADERS)


# =========================================================
# TEXT CLEAN
# =========================================================

def clean(text):

    if text is None:
        return ""

    text = unescape(str(text))

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = text.replace(
        "\xa0",
        " "
    )

    text = text.replace(
        "&nbsp;",
        " "
    )

    return " ".join(
        text.split()
    ).strip()


# =========================================================
# DIGIT CONVERSION
# =========================================================

def normalize_digits(text):

    if text is None:
        return ""

    text = str(text)

    arabic = "٠١٢٣٤٥٦٧٨٩"
    persian = "۰۱۲۳۴۵۶۷۸۹"

    for i in range(10):

        text = text.replace(
            arabic[i],
            str(i)
        )

        text = text.replace(
            persian[i],
            str(i)
        )

    return text


# =========================================================
# PRICE
# =========================================================

def price_value(text):

    text = clean(text)

    text = normalize_digits(text)

    if not text:
        return None

    if text in (
        "-",
        "—",
        "–",
        "null",
        "None",
        "ندارد"
    ):
        return None

    # حذف کد گرید و موارد غیرقیمتی
    text = re.sub(
        r"\bA[123]\b",
        " ",
        text,
        flags=re.I
    )

    # فقط اعداد
    numbers = re.findall(
        r"\d[\d,]*",
        text
    )

    if not numbers:
        return None

    # بزرگ‌ترین عدد معمولاً قیمت است
    values = []

    for number in numbers:

        digits = re.sub(
            r"[^\d]",
            "",
            number
        )

        if not digits:
            continue

        try:
            value = int(digits)

            # قیمت‌های فولادی معمولاً در این بازه‌اند
            if 10000 <= value <= 100000000:
                values.append(value)

        except Exception:
            continue

    if not values:
        return None

    return max(values)


# =========================================================
# TABLE ROWS
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
            clean(x)
            for x in cells
        ]

        if len(values) == 5:

            result.append(
                values
            )

    return result


# =========================================================
# SIZE CLEAN
# =========================================================

def clean_size(size):

    size = clean(size)

    size = normalize_digits(size)

    # حذف اطلاعات اضافی
    size = re.sub(
        r"\bA[123]\b",
        "",
        size,
        flags=re.I
    )

    size = re.sub(
        r"\s+",
        " ",
        size
    ).strip()

    return size


# =========================================================
# DESCRIPTION CLEAN
# =========================================================

def clean_description(description):

    description = clean(
        description
    )

    description = normalize_digits(
        description
    )

    # حذف قیمت‌های اضافی
    description = re.sub(
        r"\b\d[\d,]*\b",
        "",
        description
    )

    return " ".join(
        description.split()
    ).strip()


# =========================================================
# EXTRACT PRODUCTS
# =========================================================

def extract_products(
    html,
    source_page
):

    rows = extract_table_rows(
        html
    )

    products = []

    for values in rows:

        factory = clean(
            values[0]
        )

        size = clean_size(
            values[1]
        )

        yesterday_text = clean(
            values[2]
        )

        today_text = clean(
            values[3]
        )

        description = clean_description(
            values[4]
        )

        # -------------------------------------------------
        # حذف Header
        # -------------------------------------------------

        if "قیمت دیروز" in yesterday_text:
            continue

        if "قیمت امروز" in today_text:
            continue

        # -------------------------------------------------
        # حذف ردیف‌های غیرمحصول
        # -------------------------------------------------

        if not factory:
            continue

        if not size:
            continue

        if factory == "میلگرد":
            continue

        if "قیمت ها با احتساب" in factory:
            continue

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        old_price = price_value(
            yesterday_text
        )

        new_price = price_value(
            today_text
        )

        # اگر قیمت امروز وجود ندارد
        # این ردیف برای ما کاربردی نیست
        if new_price is None:

            continue

        # -------------------------------------------------
        # تغییر
        # -------------------------------------------------

        change = None
        change_percent = None

        if (
            old_price is not None
            and old_price > 0
        ):

            change = (
                new_price -
                old_price
            )

            change_percent = round(
                (
                    change /
                    old_price
                ) * 100,
                2
            )

        products.append({

            "factory": factory,

            "size": size,

            "yesterday": old_price,

            "today": new_price,

            "change": change,

            "change_percent":
                change_percent,

            "description":
                description,

            "source_page":
                source_page

        })

    return products


# =========================================================
# DUPLICATES
# =========================================================

def remove_duplicates(
    products
):

    unique = []

    seen = set()

    for product in products:

        key = (
            product["factory"],
            product["size"],
            product["today"],
            product["source_page"]
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
# FETCH
# =========================================================

def fetch_page(
    title,
    url
):

    print()
    print(
        "=" * 70
    )

    print(
        title
    )

    print(
        url
    )

    print(
        "=" * 70
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

        return response.text

    except Exception as e:

        print(
            "ERROR:",
            e
        )

        return ""


# =========================================================
# DISPLAY
# =========================================================

def show_sample(
    products,
    count=20
):

    print()
    print(
        "=" * 70
    )

    print(
        "CLEAN SAMPLE"
    )

    print(
        "=" * 70
    )

    for product in products[:count]:

        print()

        print(
            "🏭 کارخانه:",
            product["factory"]
        )

        print(
            "📏 سایز:",
            product["size"]
        )

        print(
            "💰 امروز:",
            product["today"]
        )

        print(
            "💰 دیروز:",
            product["yesterday"]
        )

        print(
            "📊 تغییر:",
            product["change_percent"]
        )

        print(
            "📝 توضیحات:",
            product["description"]
        )


# =========================================================
# MAIN
# =========================================================

def main():

    all_products = []

    page_counts = {}

    # =====================================================
    # سایر کارخانه‌ها
    # =====================================================

    html = fetch_page(
        "میلگرد سایر کارخانجات",
        URLS[
            "میلگرد سایر کارخانجات"
        ]
    )

    if html:

        products = extract_products(
            html,
            "میلگرد سایر کارخانجات"
        )

        print(
            "CLEAN FOUND:",
            len(products)
        )

        page_counts[
            "میلگرد سایر کارخانجات"
        ] = len(products)

        all_products.extend(
            products
        )

    else:

        page_counts[
            "میلگرد سایر کارخانجات"
        ] = 0

    # =====================================================
    # نیشابور
    # =====================================================

    html = fetch_page(
        "میلگرد نیشابور",
        URLS[
            "میلگرد نیشابور"
        ]
    )

    if html:

        products = extract_products(
            html,
            "میلگرد نیشابور"
        )

        print(
            "CLEAN FOUND:",
            len(products)
        )

        page_counts[
            "میلگرد نیشابور"
        ] = len(products)

        all_products.extend(
            products
        )

    else:

        page_counts[
            "میلگرد نیشابور"
        ] = 0

    # =====================================================
    # حذف تکراری
    # =====================================================

    all_products = remove_duplicates(
        all_products
    )

    # =====================================================
    # JSON
    # =====================================================

    data = {

        "source":
            "khorasan-steel.com",

        "updated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "count":
            len(all_products),

        "prices":
            all_products

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

    # =====================================================
    # RESULT
    # =====================================================

    print()
    print(
        "=" * 70
    )

    print(
        "JSON CREATED"
    )

    print(
        "=" * 70
    )

    print(
        "FILE: prices.json"
    )

    print(
        "TOTAL CLEAN PRODUCTS:",
        len(all_products)
    )

    print()
    print(
        "COUNT BY PAGE:"
    )

    for page, count in page_counts.items():

        print(
            f"{page}: {count}"
        )

    show_sample(
        all_products,
        20
    )

    print()
    print(
        "=" * 70
    )

    print(
        "TEST FINISHED"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":

    main()