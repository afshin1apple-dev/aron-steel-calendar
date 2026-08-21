import requests
from bs4 import BeautifulSoup
import re

URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://khorasan-steel.com/product.php?prd=3"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

for title, url in URLS.items():

    print("\n" + "=" * 70)
    print(title)
    print(url)
    print("=" * 70)

    r = requests.get(url, headers=HEADERS, timeout=30)

    print("HTTP:", r.status_code)

    if r.status_code != 200:
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    tables = soup.find_all("table")

    print("TABLES FOUND:", len(tables))

    for table_index, table in enumerate(tables):

        rows = table.find_all("tr")

        if not rows:
            continue

        print("\n--- TABLE", table_index + 1, "---")

        for row in rows:

            cells = row.find_all(["th", "td"])

            values = [
                clean(cell.get_text(" ", strip=True))
                for cell in cells
            ]

            values = [v for v in values if v]

            if values:
                print(" | ".join(values))

print("\n" + "=" * 70)
print("TEST FINISHED")
print("=" * 70)