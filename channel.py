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
        return ""
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
# PARSE ONE FACTORY
# =========================================================
def parse_channel_product(product):
    try:
        response = fetch_page(product["url"])
        tables = pd.read_html(response.text)
        if not tables:
            return {
                "name": product["name"],
                "factory": product["factory"],
                "type": product["type"],
                "ok": False,
                "products": [],
                "error": "جدول قیمت پیدا نشد",
            }
        df = tables[0]
        products = []
        for _, row in df.iterrows():
            values = [str(x).strip() for x in row.tolist()]
            if len(values) < 5:
                continue
            size = normalize_number(values[0])
            length = normalize_number(values[1])
            delivery = values[2].strip()
            unit = values[3].strip()
            raw_price = values[4]
            # -------------------------------------------------
            # فقط سایز عددی
            # -------------------------------------------------
            if not re.fullmatch(r"\d+(?:\.\d+)?", size):
                continue
            # -------------------------------------------------
            # فقط طول عددی
            # -------------------------------------------------
            if not re.fullmatch(r"\d+(?:\.\d+)?", length):
                continue
            # -------------------------------------------------
            # فقط کیلوگرم
            # -------------------------------------------------
            if "کیلو" not in unit:
                continue
            # -------------------------------------------------
            # حذف تمام قیمت‌های انبار تهران
            # -------------------------------------------------
            delivery_normalized = delivery.replace("‌", " ").strip()
            if "تهران" in delivery_normalized:
                continue
            if "انبار" in delivery_normalized:
                continue
            # -------------------------------------------------
            # قیمت جاری
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
    except Exception as e:
        error_text = str(e)
        # کوتاه کردن خطا برای جلوگیری از لاگ چند هزار خطی
        if len(error_text) > 300:
            error_text = error_text[:300] + "..."
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": error_text,
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
                f"{result['name']}: OK "
                f"({len(result['products'])} قیمت)"
            )
            # فقط خروجی نهایی، بدون RAW ROW
            for item in result["products"]:
                print(
                    f"  {item['size']}×{item['length']} متر : "
                    f"{item['price']:,} تومان"
                )
        else:
            print(f"{result['name']}: ERROR")
            if result.get("error"):
                print(f"  علت: {result['error']}")
    print()
    print("=" * 45)
    print(f"FACTORIES: {factories_ok}/{len(results)}")
    print(f"PRODUCTS: {total_products}")
    print("=" * 45)
# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    results = get_channel_prices()
    print_final_result(results)