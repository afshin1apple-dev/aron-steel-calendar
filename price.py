import requests
import re
from html import unescape

URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://khorasan-steel.com/product.php?prd=3",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139.0 Safari/537.36"
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

    # فقط عدد
    digits = re.sub(r"[^\d]", "", text)

    if not digits:
        return None

    return int(digits)


def extract_rows(html):

    # فقط tbodyها را بررسی می‌کنیم
    tbodies = re.findall(
        r"<tbody[^>]*>(.*?)</tbody>",
        html,
        flags=re.I | re.S
    )

    print("TBODY COUNT:", len(tbodies))

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

            # باید دقیقاً 5 ستون قیمت داشته باشیم
            if len(values) < 5:
                continue

            # header
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

            # قیمت‌ها
            yesterday_price = price_value(yesterday)
            today_price = price_value(today)

            # اگر ردیف محصول نیست
            if not factory or not size:
                continue

            # اگر هر دو قیمت خالی هستند، باز هم محصول را نگه می‌داریم
            # چون ممکن است "-" باشد
            products.append({
                "factory": factory,
                "size": size,
                "yesterday": yesterday_price,
                "today": today_price,
                "description": description
            })

    return products


def test(title, url):

    print("\n")
    print("=" * 100)
    print(title)
    print(url)
    print("=" * 100)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    print("HTTP:", response.status_code)
    print("LENGTH:", len(response.text))

    if response.status_code != 200:
        print("ERROR: HTTP STATUS")
        return

    products = extract_rows(response.text)

    print("\n")
    print("-" * 100)
    print("EXTRACTED PRODUCTS")
    print("-" * 100)

    for i, product in enumerate(products, 1):

        print(
            f"{i:03d} | "
            f"FACTORY={product['factory']} | "
            f"SIZE={product['size']} | "
            f"YESTERDAY={product['yesterday']} | "
            f"TODAY={product['today']} | "
            f"DESC={product['description']}"
        )

    print("\nFOUND:", len(products))


for title, url in URLS.items():
    test(title, url)


print("\n")
print("=" * 100)
print("TEST FINISHED")
print("=" * 100)