import requests
from bs4 import BeautifulSoup
import re
import json


# =========================================================
# SETTINGS
# =========================================================

URL = "https://pivan.co/brands/khorasan-steel-neishabour/rebar/"

FACTORY = "فولاد خراسان نیشابور"
PRODUCT = "میلگرد"


# =========================================================
# HTTP
# =========================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}


# =========================================================
# NUMBER
# =========================================================

def normalize_digits(text):
    """
    تبدیل اعداد فارسی و عربی به انگلیسی
    """

    if not text:
        return ""

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(table)


def clean_number(text):
    """
    استخراج یک عدد از متن
    """

    text = normalize_digits(text)
    text = text.replace(",", "")
    text = text.replace("٬", "")
    text = text.strip()

    match = re.search(r"\d+(?:\.\d+)?", text)

    if not match:
        return None

    try:
        return float(match.group())
    except Exception:
        return None


# =========================================================
# PRICE
# =========================================================

def extract_price(price_cell):
    """
    قیمت بدون مالیات را از span.ex-tax می‌گیرد.

    مثال HTML:

    <span class="... in-tax">79,000</span>
    <span class="... ex-tax">71,800</span>
    """

    ex_tax = price_cell.select_one("span.ex-tax")

    if ex_tax:
        price = clean_number(ex_tax.get_text(" ", strip=True))

        if price is not None:
            return int(price)

    return None


# =========================================================
# SIZE
# =========================================================

def extract_size(text):
    """
    استخراج سایز میلگرد
    """

    text = normalize_digits(text)

    match = re.search(r"\d+", text)

    if not match:
        return None

    try:
        return int(match.group())
    except Exception:
        return None


# =========================================================
# GET PAGE
# =========================================================

def get_page():

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    response.encoding = response.apparent_encoding

    return response.text


# =========================================================
# PARSE
# =========================================================

def parse_prices(html):

    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")

    if not tables:
        raise RuntimeError("هیچ جدول قیمتی پیدا نشد.")

    price_table = None

    # پیدا کردن جدولی که ستون قیمت دارد
    for table in tables:

        text = table.get_text(" ", strip=True)

        if "قیمت" in text and "نوسان" in text:
            price_table = table
            break

    if price_table is None:
        raise RuntimeError("جدول قیمت پیدا نشد.")

    products = []

    rows = price_table.find_all("tr")

    for row in rows:

        cells = row.find_all(["td", "th"])

        if len(cells) < 5:
            continue

        # -------------------------------------------------
        # ستون‌ها
        # -------------------------------------------------

        size_text = cells[0].get_text(" ", strip=True)
        standard = cells[1].get_text(" ", strip=True)
        delivery = cells[2].get_text(" ", strip=True)
        unit = cells[3].get_text(" ", strip=True)

        price_cell = cells[4]

        # -------------------------------------------------
        # SIZE
        # -------------------------------------------------

        size = extract_size(size_text)

        if size is None:
            continue

        # -------------------------------------------------
        # PRICE
        # -------------------------------------------------

        price = extract_price(price_cell)

        # اگر قیمت موجود نیست، محصول را حذف نمی‌کنیم.
        # مقدار None یعنی "تماس بگیرید"
        # -------------------------------------------------

        product = {
            "factory": FACTORY,
            "product": PRODUCT,
            "size": size,
            "standard": standard,
            "delivery": delivery,
            "unit": unit,
            "price": price,
            "price_unit": "تومان/کیلوگرم",
        }

        products.append(product)

    return products


# =========================================================
# MAIN
# =========================================================

def get_prices():

    html = get_page()

    products = parse_prices(html)

    return products


# =========================================================
# SAVE JSON
# =========================================================

def save_json(products, filename="pivan_prices.json"):

    data = {
        "source": "Pivan",
        "factory": FACTORY,
        "product": PRODUCT,
        "url": URL,
        "prices": products,
    }

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print("=" * 70)
    print("PIVAN PRICE SCRAPER")
    print("=" * 70)

    try:

        products = get_prices()

        print()
        print(f"PRODUCTS FOUND: {len(products)}")
        print()

        for item in products:

            price = item["price"]

            if price is None:
                price_text = "تماس بگیرید"
            else:
                price_text = f"{price:,}"

            print(
                f"🏭 {item['factory']} | "
                f"📏 {item['size']} | "
                f"📋 {item['standard']} | "
                f"💰 {price_text} تومان"
            )

        save_json(products)

        print()
        print("=" * 70)
        print("JSON SAVED: pivan_prices.json")
        print("=" * 70)

    except Exception as e:

        print()
        print("❌ ERROR:")
        print(str(e))
        raise