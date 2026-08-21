import requests
from bs4 import BeautifulSoup
import re

URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://khorasan-steel.com/product.php?prd=3",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def clean(text):
    return " ".join(text.replace("\xa0", " ").split())


def normalize_number(text):
    text = clean(text)

    if text in ("-", "—", ""):
        return None

    digits = re.sub(r"[^\d]", "", text)

    return int(digits) if digits else None


def extract_prices(html):
    soup = BeautifulSoup(html, "html.parser")

    products = []
    current_factory = None

    # تمام ردیف‌های جدول
    for tr in soup.find_all("tr"):

        cells = tr.find_all("td")

        if not cells:
            continue

        values = [clean(td.get_text(" ", strip=True)) for td in cells]

        # ------------------------------------------
        # تشخیص عنوان کارخانه
        # مثال:
        # (میلگرد اصفهان) ESCO قیمت ها ...
        # ------------------------------------------
        full_text = " ".join(values)

        if len(values) == 1 or any("میلگرد" in v for v in values):

            m = re.search(
                r"\(میلگرد\s*([^)]+)\)",
                full_text
            )

            if m:
                current_factory = clean(m.group(1))
                continue

        # ------------------------------------------
        # ردیف واقعی قیمت
        # ------------------------------------------
        if len(values) < 5:
            continue

        # رد کردن header
        if "قیمت دیروز" in full_text or "قیمت امروز" in full_text:
            continue

        factory = values[0]
        size = values[1]
        yesterday = values[2]
        today = values[3]
        description = values[4]

        # ردیف‌های خالی
        if not factory or not size:
            continue

        # اگر کارخانه از خود ردیف معتبر بود استفاده کن
        if factory in ("میلگرد", "سایز", "سایزa"):
            continue

        # قیمت‌ها
        yesterday_price = normalize_number(yesterday)
        today_price = normalize_number(today)

        # اگر هیچ قیمتی ندارد، هنوز محصول است
        if (
            yesterday_price is None
            and today_price is None
            and description == ""
        ):
            continue

        # اگر عنوان کارخانه پیدا نشده، از ستون کارخانه استفاده کن
        if not current_factory:
            current_factory = factory

        products.append({
            "factory": factory,
            "section": current_factory,
            "size": size,
            "yesterday": yesterday_price,
            "today": today_price,
            "description": description,
        })

    return products


def test_url(title, url):

    print("\n" + "=" * 90)
    print(title)
    print(url)
    print("=" * 90)

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    print("HTTP:", response.status_code)
    print("LENGTH:", len(response.text))

    if response.status_code != 200:
        return

    products = extract_prices(response.text)

    print("\n" + "-" * 90)
    print("EXTRACTED PRODUCTS")
    print("-" * 90)

    for i, p in enumerate(products, 1):

        print(
            f"{i:03d} | "
            f"FACTORY={p['factory']} | "
            f"SIZE={p['size']} | "
            f"YESTERDAY={p['yesterday']} | "
            f"TODAY={p['today']} | "
            f"DESC={p['description']}"
        )

    print("\nFOUND:", len(products))


for title, url in URLS.items():
    test_url(title, url)

print("\n" + "=" * 90)
print("TEST FINISHED")
print("=" * 90)