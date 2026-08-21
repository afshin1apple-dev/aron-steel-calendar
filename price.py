import requests
import re
import json
from html import unescape
from datetime import datetime, timezone


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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
}


def clean(text):
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")
    return " ".join(text.split()).strip()


def price_value(text):
    text = clean(text)

    if text in ("", "-", "—", "–"):
        return None

    digits = re.sub(r"[^\d]", "", text)

    if not digits:
        return None

    return int(digits)


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

        values = [clean(x) for x in cells]

        if len(values) == 5:
            result.append(values)

    return result


def extract_products(html, source_page):

    rows = extract_table_rows(html)

    products = []

    for values in rows:

        factory = values[0]
        size = values[1]
        yesterday = values[2]
        today = values[3]
        description = values[4]

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

        products.append({
            "factory": factory,
            "size": size,
            "yesterday": price_value(yesterday),
            "today": price_value(today),
            "description": description,
            "source_page": source_page
        })

    return products


def extract_nishabur(html):

    """
    استخراج مخصوص صفحه نیشابور.
    چون ساختار صفحه نیشابور با صفحه سایر کارخانجات
    متفاوت است، جدول‌ها را مستقیم از تمام tr ها می‌خوانیم.
    """

    products = []

    rows = extract_table_rows(html)

    for values in rows:

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

        # فقط ردیف‌هایی که حداقل یکی از قیمت‌ها عدد باشد
        old_price = price_value(yesterday)
        new_price = price_value(today)

        if old_price is None and new_price is None:
            continue

        products.append({
            "factory": factory,
            "size": size,
            "yesterday": old_price,
            "today": new_price,
            "description": description,
            "source_page": "میلگرد نیشابور"
        })

    return products


def fetch_page(title, url):

    print()
    print("=" * 70)
    print(title)
    print(url)
    print("=" * 70)

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print("HTTP:", response.status_code)
        print("LENGTH:", len(response.text))

        response.raise_for_status()

        return response.text

    except Exception as e:

        print("ERROR:", e)

        return ""


def remove_duplicates(products):

    unique = []
    seen = set()

    for product in products:

        key = (
            product["factory"],
            product["size"],
            product["yesterday"],
            product["today"],
            product["description"],
            product["source_page"]
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(product)

    return unique


def main():

    all_products = []

    # -----------------------------
    # سایر کارخانجات
    # -----------------------------

    html = fetch_page(
        "میلگرد سایر کارخانجات",
        URLS["میلگرد سایر کارخانجات"]
    )

    if html:

        products = extract_products(
            html,
            "میلگرد سایر کارخانجات"
        )

        print("FOUND:", len(products))

        all_products.extend(products)

    # -----------------------------
    # نیشابور
    # -----------------------------

    html = fetch_page(
        "میلگرد نیشابور",
        URLS["میلگرد نیشابور"]
    )

    if html:

        products = extract_nishabur(html)

        print("FOUND:", len(products))

        all_products.extend(products)

    # -----------------------------
    # حذف تکراری
    # -----------------------------

    all_products = remove_duplicates(
        all_products
    )

    # -----------------------------
    # JSON
    # -----------------------------

    data = {
        "source": "khorasan-steel.com",
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "count": len(all_products),
        "prices": all_products
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

    # -----------------------------
    # خروجی
    # -----------------------------

    print()
    print("=" * 70)
    print("JSON CREATED")
    print("=" * 70)

    print("FILE: prices.json")
    print("TOTAL PRODUCTS:", len(all_products))

    print()
    print("COUNT BY PAGE:")

    for page in URLS:

        count = sum(
            1
            for p in all_products
            if p["source_page"] == page
        )

        print(
            f"{page}: {count}"
        )

    print()
    print("=" * 70)
    print("SAMPLE")
    print("=" * 70)

    for product in all_products[:10]:

        print(
            f"{product['factory']} | "
            f"سایز {product['size']} | "
            f"امروز {product['today']} | "
            f"{product['description']}"
        )

    print()
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()