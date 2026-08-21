import requests
from bs4 import BeautifulSoup
import re
import os

URL = "https://khorasan-steel.com/product.php?prd=5"

def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()

print("=" * 50)
print("PRICE TEST - KHORASAN STEEL")
print("=" * 50)

try:
    response = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        },
        timeout=30
    )

    print("HTTP STATUS:", response.status_code)

    if response.status_code != 200:
        raise Exception(f"Website returned status {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    text = clean_text(soup.get_text(" "))

    print("PAGE LOADED: OK")
    print("PAGE LENGTH:", len(response.text))

    print("\n--- CHECKING SIZES ---")

    sizes = [
        "6.5", "8", "10", "12", "14", "16",
        "18", "20", "22", "25", "28", "30",
        "32", "36", "38", "40", "50"
    ]

    found_sizes = []

    for size in sizes:
        if re.search(rf"(?<!\d){re.escape(size)}(?!\d)", text):
            found_sizes.append(size)

    print("FOUND SIZES:", ", ".join(found_sizes))

    print("\n--- CHECKING FACTORIES ---")

    factories = [
        "اصفهان",
        "شاهین بناب",
        "ظفر بناب",
        "راد همدان",
        "شاهرود",
        "سیادن ابهر",
        "البرزتاکستان",
        "روهینا جنوب",
        "آریان فولاد",
        "آناهیتا",
        "نیک صدرا",
        "پرشین فولاد",
        "فولادکاسپین",
        "شمس سپهر",
        "میانه",
        "کاوه تیکمه داش",
        "آذرفولادامین",
        "کویرکاشان",
        "فولاد سیرجان",
        "بافق یزد",
        "فایکو",
        "حدید سیرجان",
        "ابرکوه یزد",
        "درپاد تبریز"
    ]

    found_factories = []

    for factory in factories:
        if factory in text:
            found_factories.append(factory)

    print("FOUND FACTORIES:")

    for factory in found_factories:
        print(" -", factory)

    print("\n--- SEARCHING FOR PRICE DATA ---")

    price_patterns = [
        r"\d{1,3}(?:[,\،]\d{3})+",
        r"\d{4,7}"
    ]

    prices = set()

    for pattern in price_patterns:
        matches = re.findall(pattern, text)

        for match in matches:
            number = match.replace(",", "").replace("،", "")

            try:
                value = int(number)

                # فقط اعداد محتمل برای قیمت
                if 10000 <= value <= 10000000:
                    prices.add(value)

            except:
                pass

    if prices:
        print("POSSIBLE PRICE VALUES:")

        for price in sorted(prices)[:100]:
            print(" -", f"{price:,}")

    else:
        print("NO PRICE VALUES FOUND IN HTML TEXT")

    print("\n--- RESULT ---")

    if response.status_code == 200:
        print("✅ WEBSITE ACCESS: OK")
    else:
        print("❌ WEBSITE ACCESS: FAILED")

    if found_sizes:
        print("✅ SIZE DATA: FOUND")
    else:
        print("❌ SIZE DATA: NOT FOUND")

    if found_factories:
        print("✅ FACTORY DATA: FOUND")
    else:
        print("❌ FACTORY DATA: NOT FOUND")

    if prices:
        print("✅ PRICE DATA: FOUND")
    else:
        print("⚠️ PRICE DATA: NOT DIRECTLY VISIBLE")

    print("\nTEST FINISHED")

except Exception as e:
    print("\n❌ ERROR:")
    print(str(e))
    raise