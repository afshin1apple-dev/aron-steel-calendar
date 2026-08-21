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
    )
}


def clean(text):
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")
    return " ".join(text.split()).strip()


def price_value(text):
    text = clean(text)

    if not text or text in ("-", "—", "–"):
        return None

    digits = re.sub(r"[^\d]", "", text)

    if not digits:
        return None

    return int(digits)


def extract_all_rows(html):
    """
    همه tr های صفحه را پیدا می‌کند.
    دیگر وابسته به وجود tbody نیست.
    """

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

        values = [clean(cell) for cell in cells]

        if len(values) != 5:
            continue

        result.append(values)

    return result


def is_header_row(values):

    if len(values) != 5:
        return True

    text = " ".join(values)

    if "قیمت دیروز" in text:
        return True

    if "قیمت امروز" in text:
        return True

    if values[0] == "میلگرد":
        return True

    return False


def is_empty_row(values):

    if not values:
        return True

    return all(
        not value or value in ("-", "—", "–")
        for value in values
    )


def extract_rows(html, page_title):

    rows = extract_all_rows(html)

    products = []

    for values in rows:

        if is_header_row(values):
            continue

        if is_empty_row(values):
            continue

        factory = clean(values[0])
        size = clean(values[1])
        yesterday = price_value(values[2])
        today = price_value(values[3])
        description = clean(values[4])

        # ردیف‌هایی که مربوط به عنوان بخش هستند
        if not factory:
            continue

        # اگر سایز وجود نداشته باشد، محصول نیست
        if not size:
            continue

        # جلوگیری از ورود متن‌های توضیحی
        if "قیمت ها با احتساب" in factory:
            continue

        if "قیمت میلگرد" in factory:
            continue

        # اگر هر دو قیمت خالی هستند ولی ردیف توضیح محصول است،
        # همچنان نگه می‌داریم چون ممکن است محصول موجود نباشد.
        products.append({
            "factory": factory,
            "size": size,
            "yesterday": yesterday,
            "today": today,
            "description": description,
            "source_page": page_title
        })

    return products


def fetch_prices(title, url):

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

        print(f"HTTP: {response.status_code}")
        print(f"LENGTH: {len(response.text)}")

        response.raise_for_status()

        products = extract_rows(
            response.text,
            title
        )

        print(f"FOUND: {len(products)}")

        return products

    except Exception as e:

        print(f"ERROR: {e}")

        return []


def remove_duplicates(products):

    unique_products = []
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
        unique_products.append(product)

    return unique_products


def main():

    all_products = []

    for title, url in URLS.items():

        products = fetch_prices(
            title,
            url
        )

        all_products.extend(products)

    unique_products = remove_duplicates(
        all_products
    )

    data = {
        "source": "khorasan-steel.com",
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "count": len(unique_products),
        "prices": unique_products
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

    print()
    print("=" * 70)
    print("JSON CREATED")
    print("=" * 70)

    print("FILE: prices.json")
    print(f"TOTAL PRODUCTS: {len(unique_products)}")

    print()
    print("COUNT BY PAGE:")

    for title in URLS:

        count = sum(
            1
            for product in unique_products
            if product["source_page"] == title
        )

        print(
            f"{title}: {count}"
        )

    print()
    print("=" * 70)
    print("SAMPLE")
    print("=" * 70)

    for product in unique_products[:10]:

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