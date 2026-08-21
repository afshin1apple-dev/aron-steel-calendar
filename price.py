import requests
import re

URLS = [
    "https://khorasan-steel.com/product.php?prd=5",
    "https://khorasan-steel.com/product.php?prd=3",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139.0 Safari/537.36",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}

for url in URLS:

    print("\n" + "=" * 80)
    print("URL:", url)
    print("=" * 80)

    r = requests.get(url, headers=HEADERS, timeout=30)

    print("STATUS:", r.status_code)
    print("LENGTH:", len(r.text))

    html = r.text

    keywords = [
        "قیمت امروز",
        "قیمت دیروز",
        "قیمت",
        "price",
        "today",
        "yesterday",
        "ajax",
        "load",
        "product"
    ]

    print("\n--- MATCHED HTML LINES ---")

    lines = html.splitlines()

    count = 0

    for line in lines:

        line_clean = re.sub(r"\s+", " ", line).strip()

        if not line_clean:
            continue

        low = line_clean.lower()

        if any(k.lower() in low for k in keywords):

            print(line_clean[:3000])

            count += 1

            if count >= 100:
                break

    print("\nMATCH COUNT:", count)

    print("\n--- SCRIPT URLS ---")

    scripts = re.findall(
        r'<script[^>]+src=["\']([^"\']+)["\']',
        html,
        re.IGNORECASE
    )

    for script in scripts:
        print(script)

    print("\n--- POSSIBLE PRICE VALUES ---")

    numbers = re.findall(
        r"(?<!\d)\d{5,8}(?!\d)",
        html
    )

    unique = []

    for n in numbers:
        if n not in unique:
            unique.append(n)

    for n in unique[:100]:
        print(n)

print("\n" + "=" * 80)
print("INVESTIGATION FINISHED")
print("=" * 80)