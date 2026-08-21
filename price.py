import requests
import re
import json
from html import unescape
from datetime import datetime

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
    return " ".join(text.split()).strip()


def price_value(text):
    text = clean(text)

    if text in ("", "-", "—"):
        return None

    digits = re.sub(r"[^\d]", "", text)

    if not digits:
        return None

    return int(digits)


def extract_rows(html):

    tbodies = re.findall(
        r"<tbody[^>]*>(.*?)</tbody>",
        html,
        flags=re.I | re.S
    )

    products = []

    for tbody in tbodies:

        rows = re.findall(
            r"<tr[^>]*>(.*?)</tr>",
            tbody,
            flags=re.I | re.S
        )

        for row in rows:

            cells = re.findall(
                r"<td[^>]*>(.*?)</td>",
                row,
                flags=re.I | re.S
            )

            values = [clean(x) for x in cells]

            if len(values) < 5:
                continue

            # رد کردن عنوان ستون‌ها
            if (
                "قیمت دیروز" in values[2]
                or "قیمت امروز" in values[3]
                or values[0] == "میلگرد"
            ):
                continue

            factory = values[0]
            size = values[1]
            yesterday = values[2]
            today = values[3]
            description = values[4]

            if not factory or not size:
                continue

            products.append({
                "factory": factory,
                "size": size,
                "yesterday": price_value(yesterday),
                "today": price_value(today),
                "description": description
            })

    return products


def fetch_prices(title, url):

    print("\n")
    print("=" * 100)
    print(title)
    print(url)
    print("=" * 100)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print("HTTP:", response.status_code)
        print("LENGTH:", len(response.text))

        response.raise_for_status()

        products = extract_rows(response.text)

        print("FOUND:", len(products))

        return products

    except Exception as e:

        print("ERROR:", e)

        return []


def main():

    all_products = []

    for title, url in URLS.items():

        products = fetch_prices(title, url)

        all_products.extend(products)

    # حذف موارد کاملاً تکراری
    unique_products = []

    seen = set()

    for product in all_products:

        key = (
            product["factory"],
            product["size"],
            product["yesterday"],
            product["today"],
            product["description"]
        )

        if key not in seen:
            seen.add(key)
            unique_products.append(product)

    data = {
        "source": "khorasan-steel.com",
        "updated_at": datetime.utcnow().isoformat() + "Z",
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

    print("\n")
    print("=" * 100)
    print("JSON CREATED")
    print("=" * 100)

    print("FILE: prices.json")
    print("TOTAL PRODUCTS:", len(unique_products))

    print("\nFIRST 10 PRODUCTS:")

    for product in unique_products[:10]:

        print(
            f"{product['factory']} | "
            f"{product['size']} | "
            f"{product['today']} | "
            f"{product['description']}"
        )

    print("\n")
    print("=" * 100)
    print("TEST FINISHED")
    print("=" * 100)


if __name__ == "__main__":
    main()