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
        # Pivan format is usually:
        # OLD/UPPER PRICE + CURRENT PRICE
        # We need the last numeric value.
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
    print()
    print("=" * 70)
    print("CHANNEL PRICE")
    print("=" * 70)
    print(f"FACTORY: {product['factory']}")
    print(f"TYPE: {product['type']}")
    print(f"URL: {product['url']}")
    try:
        response = fetch_page(product["url"])
    except Exception as e:
        print(f"REQUEST ERROR: {e}")
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": str(e),
        }
    print(f"HTTP: {response.status_code}")
    print(f"LENGTH: {len(response.text)}")
    try:
        tables = pd.read_html(response.text)
    except Exception as e:
        print(f"TABLE READ ERROR: {e}")
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": str(e),
        }
    print(f"TABLE COUNT: {len(tables)}")
    if not tables:
        print("NO TABLE FOUND")
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "No tables found",
        }
    # -----------------------------------------------------
    # IMPORTANT:
    # The channel table is currently table 0.
    # -----------------------------------------------------
    table_index = 0
    if table_index >= len(tables):
        print("CHANNEL TABLE NOT FOUND")
        return {
            "name": product["name"],
            "factory": product["factory"],
            "type": product["type"],
            "ok": False,
            "products": [],
            "error": "Channel table not found",
        }
    df = tables[table_index]
    print(f"SELECTED CHANNEL TABLE: {table_index}")
    print(f"ROWS: {len(df)}")
    products = []
    for _, row in df.iterrows():
        values = [str(x).strip() for x in row.tolist()]
        print(f"RAW ROW: {values}")
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
        if not re.fullmatch(r"\d+(?:\.\d+)?", size_normalized):
            continue
        # -------------------------------------------------
        # Validate length
        # -------------------------------------------------
        length_normalized = normalize_number(length)
        if not re.fullmatch(r"\d+(?:\.\d+)?", length_normalized):
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
            print(f"SIZE {size}: PRICE NOT FOUND")
            continue
        item = {
            "size": size_normalized,
            "length": length_normalized,
            "delivery": delivery,
            "unit": unit,
            "price": price,
        }
        products.append(item)
        print(
            f"SIZE {size_normalized} | "
            f"LENGTH {length_normalized} | "
            f"PRICE {price:,}"
        )
    print(f"VALID CHANNEL PRODUCTS: {len(products)}")
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
    print("=" * 70)
    print("FINAL CHANNEL RESULT")
    print("=" * 70)
    for result in results:
        print()
        print(
            f"{result['name']} -> "
            f"{'ok' if result['ok'] else 'ERROR'}"
        )
        if not result["ok"]:
            if result.get("error"):
                print(f"ERROR: {result['error']}")
            continue
        for item in result["products"]:
            print(
                f"ناودانی {item['size']} - "
                f"{item['length']} متر : "
                f"{item['price']:,} تومان"
            )
# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    results = get_channel_prices()
    print_final_result(results)