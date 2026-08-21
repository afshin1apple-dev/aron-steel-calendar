import requests
import re
from urllib.parse import urljoin

BASE = "https://khorasan-steel.com/"
JS_URL = urljoin(BASE, "js/filter-products.js")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139.0 Safari/537.36",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}

print("=" * 80)
print("KHORASAN STEEL - FILTER SCRIPT TEST")
print("=" * 80)

try:
    r = requests.get(
        JS_URL,
        headers=HEADERS,
        timeout=30
    )

    print("JS URL:", JS_URL)
    print("HTTP STATUS:", r.status_code)
    print("JS LENGTH:", len(r.text))

    if r.status_code != 200:
        raise Exception("Could not download filter-products.js")

    js = r.text

    print("\n" + "-" * 70)
    print("FILTER-PRODUCTS.JS")
    print("-" * 70)

    print(js[:30000])

    print("\n" + "-" * 70)
    print("POSSIBLE AJAX / API / PRICE URLS")
    print("-" * 70)

    patterns = [
        r"""url\s*:\s*["']([^"']+)["']""",
        r"""["']([^"']*(?:ajax|api|product|price|filter)[^"']*)["']""",
        r"""(?:get|post)\s*\(\s*["']([^"']+)["']""",
        r"""fetch\s*\(\s*["']([^"']+)["']""",
    ]

    found = set()

    for pattern in patterns:

        matches = re.findall(
            pattern,
            js,
            re.IGNORECASE
        )

        for match in matches:
            found.add(match)

    if found:

        for item in sorted(found):
            print(item)

    else:

        print("NO DIRECT URL FOUND")

    print("\n" + "-" * 70)
    print("IMPORTANT KEYWORDS")
    print("-" * 70)

    keywords = [
        "ajax",
        "url",
        "post",
        "get",
        "price",
        "product",
        "filter",
        "size",
        "factory",
        "prd",
        "load"
    ]

    lines = js.splitlines()

    count = 0

    for line in lines:

        line = line.strip()

        if not line:
            continue

        low = line.lower()

        if any(k in low for k in keywords):

            print(line[:3000])

            count += 1

            if count >= 150:
                break

    print("\nMATCHED LINES:", count)

    print("\n" + "=" * 80)
    print("TEST FINISHED")
    print("=" * 80)

except Exception as e:

    print("\n❌ ERROR")
    print(type(e).__name__, str(e))
    raise