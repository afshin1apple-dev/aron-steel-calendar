import requests
from bs4 import BeautifulSoup
import re

URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://khorasan-steel.com/product.php?prd=3",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139.0 Safari/537.36",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}

for title, url in URLS.items():

    print("\n" + "=" * 90)
    print(title)
    print(url)
    print("=" * 90)

    r = requests.get(url, headers=HEADERS, timeout=30)

    print("HTTP:", r.status_code)
    print("LENGTH:", len(r.text))

    soup = BeautifulSoup(r.text, "html.parser")

    # تمام tr ها
    rows = soup.find_all("tr")

    print("\nTR COUNT:", len(rows))

    print("\n" + "-" * 90)
    print("PRICE ROWS")
    print("-" * 90)

    found = 0

    for row in rows:

        text = row.get_text(" ", strip=True)

        if not text:
            continue

        # فقط ردیف‌هایی که احتمالاً قیمت دارند
        if (
            "قیمت" in text
            or "ریال" in text
            or re.search(r"\d{5,}", text)
        ):

            print(text[:2000])

            found += 1

            if found >= 150:
                break

    print("\nFOUND ROWS:", found)

    print("\n" + "-" * 90)
    print("TABLE-LIKE ELEMENTS")
    print("-" * 90)

    # هر چیزی که نقش جدول دارد
    for tag in soup.find_all(["div", "ul", "li", "section"]):

        text = tag.get_text(" ", strip=True)

        if not text:
            continue

        if (
            "قیمت امروز" in text
            or "قیمت دیروز" in text
        ):

            print("\nELEMENT:", tag.name)
            print(text[:3000])

            found += 1

            if found >= 180:
                break

    print("\n" + "=" * 90)

print("EXTRACTION TEST FINISHED")