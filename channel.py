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
# فایکو عمداً حذف شده است
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
def extract_current_price(value):
    """
    مثال:
    88000 80000 -> 80000
    89000 80900 -> 80900
    تماس بگیرید -> None
    """
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
    try:
        response = fetch_page(product["url"])
    except Exception as e:
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": f"Request error: {type(e).__name__}",
        }
    try:
        # مهم:
        # html را مستقیماً به read_html می‌دهیم.
        # هیچ‌وقت متن کامل HTML را داخل خطا چاپ نمی‌کنیم.
        tables = pd.read_html(response.text)
    except Exception as e:
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": f"Table error: {type(e).__name__}",
        }
    if not tables:
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "No table found",
        }
    # جدول اصلی قیمت
    df = tables[0]
    products = []
    for _, row in df.iterrows():
        values = [
            str(x).strip()
            for x in row.tolist()
        ]
        if len(values) < 5:
            continue
        size = normalize_number(values[0])
        length = normalize_number(values[1])
        delivery = values[2]
        unit = values[3]
        raw_price = values[4]
        # -------------------------------------------------
        # Size
        # -------------------------------------------------
        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            size
        ):
            continue
        # -------------------------------------------------
        # Length
        # -------------------------------------------------
        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            length
        ):
            continue
        # -------------------------------------------------
        # Unit
        # -------------------------------------------------
        if "کیلو" not in unit:
            continue
        # -------------------------------------------------
        # Price
        # -------------------------------------------------
        price = extract_current_price(raw_price)
        if price is None:
            continue
        products.append(
            {
                "size": size,
                "length": length,
                "delivery": delivery,
                "unit": unit,
                "price": price,
            }
        )
    return {
        "name": product["name"],
        "factory": product["factory"],
        "type": product["type"],
        "ok": len(products) > 0,
        "products": products,
    }
# =========================================================
# GET ALL PRICES
# =========================================================
def get_channel_prices():
    results = []
    for product in CHANNEL_PRODUCTS:
        result = parse_channel_product(product)
        results.append(result)
    return results
# =========================================================
# FINAL RESULT
# لاگ بسیار کم
# =========================================================
def print_final_result(results):
    print()
    print("=" * 45)
    print("CHANNEL PRICE TEST")
    print("=" * 45)
    factories_ok = 0
    total_products = 0
    for result in results:
        if result["ok"]:
            factories_ok += 1
            total_products += len(result["products"])
            print(
                f"{result['name']}: "
                f"OK ({len(result['products'])} قیمت)"
            )
            # فقط قیمت‌ها را چاپ می‌کنیم
            for item in result["products"]:
                print(
                    f"  ناودانی {item['size']} - "
                    f"{item['length']} متر : "
                    f"{item['price']:,} تومان"
                )
        else:
            print(
                f"{result['name']}: ERROR"
            )
            # فقط نوع خطا، بدون HTML
            if result.get("error"):
                print(
                    f"  علت: {result['error']}"
                )
    print()
    print("=" * 45)
    print(
        f"FACTORIES: "
        f"{factories_ok}/{len(CHANNEL_PRODUCTS)}"
    )
    print(
        f"PRODUCTS: {total_products}"
    )
    print("=" * 45)
# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    results = get_channel_prices()
    print_final_result(results)