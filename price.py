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

            if len(values) != 5:
                continue

            if (
                "قیمت دیروز" in values[2]
                or "قیمت امروز" in values[3]
                or values[0] == "میلگرد"
            ):
                continue

            factory = clean(values[0])
            size = clean(values[1])
            yesterday = price_value(values[2])
            today = price_value(values[3])
            description = clean(values[4])

            if not factory or not size:
                continue

            products.append({
                "factory": factory,
                "size": size,
                "yesterday": yesterday,
                "today": today,
                "description": description
            })

    return products


def fetch_prices(title, url):

    print(f"\n[{title}]")

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print(f"HTTP: {response.status_code}")

        response.raise_for_status()

        products = extract_rows(response.text)

        print(f"FOUND: {len(products)}")

        return products

    except Exception as e:

        print(f"ERROR: {e}")

        return []


def main():

    all_products = []

    for title, url in URLS.items():

        products = fetch_prices(title, url)

        all_products.extend(products)

    # حذف ردیف‌های کاملاً تکراری
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

        if key in seen:
            continue

        seen.add(key)
        unique_products.append(product)

    data = {
        "source": "khorasan-steel.com",
        "updated_at": datetime.now(timezone.utc).isoformat(),
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

    print("\n==============================")
    print("JSON CREATED")
    print("==============================")
    print("FILE: prices.json")
    print(f"TOTAL: {len(unique_products)}")

    print("\nSAMPLE:")

    for product in unique_products[:5]:

        print(
            f"{product['factory']} | "
            f"سایز {product['size']} | "
            f"امروز {product['today']} | "
            f"{product['description']}"
        )

    print("\n==============================")
    print("TEST FINISHED")
    print("==============================")


if __name__ == "__main__":
    main()