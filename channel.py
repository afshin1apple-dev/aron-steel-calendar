import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
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
def extract_current_price(value):
    """
    Example:
        '88000 80000' -> 80000
        '89000 80900' -> 80900
        'تماس بگیرید تماس بگیرید' -> None
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
        # Pivan usually returns:
        # OLD/UPPER PRICE + CURRENT PRICE
        # The last number is the current price.
        price = numbers[-1].replace(",", "")
        return int(price)
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
# PARSE CHANNEL TABLE
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
            "error": f"REQUEST ERROR: {e}",
        }
    try:
        tables = pd.read_html(response.text)
    except Exception as e:
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": f"TABLE READ ERROR: {e}",
        }
    if not tables:
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "No tables found",
        }
    # -----------------------------------------------------
    # CHANNEL TABLE
    # -----------------------------------------------------
    table_index = 0
    if table_index >= len(tables):
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "Channel table not found",
        }
    df = tables[table_index]
    products = []
    for _, row in df.iterrows():
        values = [str(x).strip() for x in row.tolist()]
        if len(values) < 5:
            continue
        size = values[0]
        length = values[1]
        delivery = values[2]
        unit = values[3]
        raw_price = values[4]
        # -------------------------------------------------
        # Validate size
        # -------------------------------------------------
        size_normalized = normalize_number(size)
        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            size_normalized
        ):
            continue
        # -------------------------------------------------
        # Validate length
        # -------------------------------------------------
        length_normalized = normalize_number(length)
        if not re.fullmatch(
            r"\d+(?:\.\d+)?",
            length_normalized
        ):
            continue
        # -------------------------------------------------
        # Unit must be kilogram
        # -------------------------------------------------
        if "کیلو" not in unit:
            continue
        # -------------------------------------------------
        # Extract current price
        # -------------------------------------------------
        price = extract_current_price(raw_price)
        if price is None:
            continue
        item = {
            "size": size_normalized,
            "length": length_normalized,
            "delivery": delivery,
            "unit": unit,
            "price": price,
        }
        products.append(item)
    return {
        "name": product["name"],
        "factory": product["factory"],
        "type": product["type"],
        "ok": len(products) > 0,
        "products": products,
    }
# =========================================================
# GET ALL CHANNEL PRICES
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
    print("=" * 50)
    print("FINAL CHANNEL RESULT")
    print("=" * 50)
    total_products = 0
    successful_factories = 0
    for result in results:
        print()
        status = "OK" if result["ok"] else "ERROR"
        print(
            f"{result['name']} -> {status}"
        )
        if not result["ok"]:
            if result.get("error"):
                print(f"  {result['error']}")
            continue
        successful_factories += 1
        total_products += len(result["products"])
        print(
            f"  {len(result['products'])} قیمت پیدا شد"
        )
        for item in result["products"]:
            print(
                f"  ناودانی {item['size']} - "
                f"{item['length']} متر : "
                f"{item['price']:,} تومان"
            )
    print()
    print("=" * 50)
    print(
        f"FACTORIES OK: "
        f"{successful_factories}/{len(results)}"
    )
    print(
        f"TOTAL PRODUCTS: "
        f"{total_products}"
    )
    print("=" * 50)
# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    results = get_channel_prices()
    print_final_result(results)