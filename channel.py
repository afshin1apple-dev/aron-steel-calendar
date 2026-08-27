import re
import requests
import pandas as pd
# =========================================================
# SETTINGS
# =========================================================
TIMEOUT = 30
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )
}
# =========================================================
# CHANNEL PRODUCTS
# =========================================================
CHANNEL_PRODUCTS = [
    {
        "name": "سبک ناب",
        "factory": "ناودانی سبک ناب تبریز",
        "type": "سبک",
        "url": "https://pivan.co/brands/tabriz-pure-steel/uchannel/",
    },
    {
        "name": "سبک شکفته",
        "factory": "ناودانی سبک شکفته",
        "type": "سبک",
        "url": "https://pivan.co/brands/shekofteh-steel/uchannel/",
    },
    {
        "name": "سنگین ناب",
        "factory": "ناودانی سنگین ناب تبریز",
        "type": "سنگین",
        "url": "https://pivan.co/brands/tabriz-pure-steel/uchannel/",
    },
    {
        "name": "سنگین فایکو",
        "factory": "ناودانی سنگین فایکو",
        "type": "سنگین",
        "url": "https://pivan.co/brands/iranian-alborz-steel-factory-faiko/uchannel/",
    },
    {
        "name": "سنگین ابهر",
        "factory": "ناودانی سنگین ابهر",
        "type": "سنگین",
        "url": "https://pivan.co/brands/west-alborz-steel-complex-and-factory/uchannel/",
    },
    {
        "name": "سنگین شکفته",
        "factory": "ناودانی سنگین شکفته",
        "type": "سنگین",
        "url": "https://pivan.co/brands/shekofteh-steel/uchannel/",
    },
]
# =========================================================
# NUMBER
# =========================================================
def normalize_number(value):
    if value is None:
        return None
    text = str(value)
    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"
    for i, ch in enumerate(persian):
        text = text.replace(ch, str(i))
    for i, ch in enumerate(arabic):
        text = text.replace(ch, str(i))
    return text
# =========================================================
# PRICE
# =========================================================
def extract_current_price(value):
    if value is None:
        return None
    text = normalize_number(value)
    if "تماس" in text:
        return None
    numbers = re.findall(r"\d[\d,]*", text)
    if not numbers:
        return None
    try:
        return int(numbers[-1].replace(",", ""))
    except Exception:
        return None
# =========================================================
# FETCH
# =========================================================
def fetch_page(url):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response
# =========================================================
# PARSE
# =========================================================
def parse_channel_product(product):
    name = product["name"]
    try:
        response = fetch_page(product["url"])
    except Exception:
        return {
            "name": name,
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "Request failed",
        }
    try:
        tables = pd.read_html(response.text)
    except Exception:
        # مهم:
        # خطای pandas ممکن است شامل کل HTML صفحه باشد.
        # عمداً متن خطا را چاپ نمی‌کنیم.
        return {
            "name": name,
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "Could not read price table",
        }
    if not tables:
        return {
            "name": name,
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "No table found",
        }
    # =====================================================
    # TABLE 0
    # =====================================================
    df = tables[0]
    products = []
    # =====================================================
    # READ ROWS
    # =====================================================
    for _, row in df.iterrows():
        values = [
            str(x).strip()
            for x in row.tolist()
        ]
        if len(values) < 5:
            continue
        size = values[0]
        length = values[1]
        delivery = values[2]
        unit = values[3]
        raw_price = values[4]
        # =================================================
        # فقط کارخانه
        # انبار تهران حذف
        # انبار اختصاصی پیوان حذف
        # =================================================
        if delivery.strip() != "کارخانه":
            continue
        # =================================================
        # SIZE
        # =================================================
        size = normalize_number(size)
        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            size
        ):
            continue
        # =================================================
        # LENGTH
        # =================================================
        length = normalize_number(length)
        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            length
        ):
            continue
        # =================================================
        # UNIT
        # =================================================
        if "کیلو" not in unit:
            continue
        # =================================================
        # PRICE
        # =================================================
        price = extract_current_price(raw_price)
        if price is None:
            continue
        products.append({
            "size": size,
            "length": length,
            "delivery": "کارخانه",
            "unit": unit,
            "price": price,
        })
    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================
    unique = {}
    for item in products:
        key = (
            item["size"],
            item["length"],
        )
        unique[key] = item
    products = list(unique.values())
    # =====================================================
    # SORT
    # =====================================================
    products.sort(
        key=lambda x: (
            float(x["size"]),
            float(x["length"]),
        )
    )
    return {
        "name": name,
        "factory": product["factory"],
        "type": product["type"],
        "ok": len(products) > 0,
        "products": products,
    }
# =========================================================
# GET ALL
# =========================================================
def get_channel_prices():
    results = []
    for product in CHANNEL_PRODUCTS:
        result = parse_channel_product(product)
        results.append(result)
    return results
# =========================================================
# FINAL RESULT
# =========================================================
def print_final_result(results):
    factories_ok = 0
    total_products = 0
    print()
    print("========================================")
    print("CHANNEL PRICE TEST")
    print("========================================")
    for result in results:
        name = result["name"]
        if not result["ok"]:
            print(f"{name}: ERROR")
            continue
        factories_ok += 1
        count = len(result["products"])
        total_products += count
        print(f"{name}: OK ({count})")
        for item in result["products"]:
            print(
                f"  {item['size']}x{item['length']} "
                f"-> {item['price']:,}"
            )
    print()
    print("========================================")
    print(
        f"FACTORIES: "
        f"{factories_ok}/{len(results)}"
    )
    print(
        f"PRODUCTS: "
        f"{total_products}"
    )
    print("========================================")
# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    results = get_channel_prices()
    print_final_result(results)