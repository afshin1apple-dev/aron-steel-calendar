import re
import requests
import pandas as pd
from io import StringIO
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
# SOURCE
# =========================================================
SOURCE_URL = (
    "https://pivan.co/brands/"
    "introduction-of-isfahan-steel-factory/"
    "iron-girder/"
)
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
def extract_price(value):
    if value is None:
        return None
    text = normalize_number(value)
    if "تماس" in text:
        return None
    numbers = re.findall(
        r"\d[\d,]*",
        text
    )
    if not numbers:
        return None
    try:
        return int(
            numbers[-1].replace(",", "")
        )
    except Exception:
        return None
# =========================================================
# FETCH
# =========================================================
def fetch_page():
    response = requests.get(
        SOURCE_URL,
        headers=HEADERS,
        timeout=TIMEOUT
    )
    response.raise_for_status()
    return response
# =========================================================
# PARSE
# =========================================================
def parse_ipe_prices():
    print(
        "Getting IPE prices..."
    )
    try:
        response = fetch_page()
    except Exception as e:
        print(
            "FETCH ERROR:",
            type(e).__name__,
            str(e)
        )
        return []
    try:
        tables = pd.read_html(
            StringIO(response.text)
        )
    except Exception as e:
        print(
            "TABLE ERROR:",
            type(e).__name__,
            str(e)
        )
        return []
    print(
        f"Tables found: {len(tables)}"
    )
    if not tables:
        print(
            "ERROR: No tables found"
        )
        return []
    products = []
    # -----------------------------------------------------
    # بررسی تمام جدول‌ها
    # -----------------------------------------------------
    for table_index, df in enumerate(tables):
        print(
            f"Checking table {table_index + 1}: "
            f"{df.shape}"
        )
        for _, row in df.iterrows():
            values = [
                str(x).strip()
                for x in row.tolist()
            ]
            if len(values) < 4:
                continue
            # -------------------------------------------------
            # تبدیل کل ردیف به متن برای شناسایی تیرآهن
            # -------------------------------------------------
            row_text = " | ".join(
                values
            )
            normalized_row = normalize_number(
                row_text
            )
            # -------------------------------------------------
            # سایز تیرآهن
            # -------------------------------------------------
            size_match = re.search(
                r"(?:IPE\s*)?(\d{2})",
                normalized_row,
                re.IGNORECASE
            )
            if not size_match:
                continue
            size = size_match.group(1)
            # فقط سایزهای مورد نظر
            allowed_sizes = {
                "12",
                "14",
                "16",
                "18",
                "20",
                "22",
                "24",
                "27",
                "30",
            }
            if size not in allowed_sizes:
                continue
            # -------------------------------------------------
            # محل تحویل
            # -------------------------------------------------
            delivery = ""
            for value in values:
                if (
                    "کارخانه" in value
                    or "انبار" in value
                    or "تهران" in value
                ):
                    delivery = value
                    break
            # -------------------------------------------------
            # فقط کارخانه
            # -------------------------------------------------
            if "کارخانه" not in row_text:
                continue
            # -------------------------------------------------
            # واحد
            # -------------------------------------------------
            unit = ""
            for value in values:
                if (
                    "کیلو" in value
                    or "شاخه" in value
                    or "تن" in value
                ):
                    unit = value
                    break
            # -------------------------------------------------
            # فقط قیمت کیلویی
            # -------------------------------------------------
            if "کیلو" not in unit:
                continue
            # -------------------------------------------------
            # وزن
            # -------------------------------------------------
            weight = None
            for value in values:
                normalized_value = normalize_number(
                    value
                )
                weight_match = re.search(
                    r"\d+(?:\.\d+)?",
                    normalized_value
                )
                if (
                    weight_match
                    and (
                        "وزن" in value
                        or "kg" in value.lower()
                    )
                ):
                    weight = weight_match.group(0)
                    break
            # -------------------------------------------------
            # قیمت
            # -------------------------------------------------
            price = None
            # از انتهای ردیف قیمت را پیدا می‌کنیم
            for value in reversed(values):
                candidate = extract_price(
                    value
                )
                if candidate is None:
                    continue
                # جلوگیری از اینکه سایز یا وزن به‌عنوان قیمت
                # شناسایی شود
                if candidate < 1000:
                    continue
                price = candidate
                break
            if price is None:
                continue
            products.append(
                {
                    "size": size,
                    "delivery": delivery,
                    "unit": unit,
                    "weight": weight,
                    "price": price,
                }
            )
    # -----------------------------------------------------
    # حذف رکوردهای تکراری
    # -----------------------------------------------------
    unique = {}
    for item in products:
        key = (
            item["size"],
            item["delivery"],
            item["unit"]
        )
        unique[key] = item
    products = list(
        unique.values()
    )
    # مرتب‌سازی سایز
    products.sort(
        key=lambda x: int(
            x["size"]
        )
    )
    return products
# =========================================================
# PRINT RESULTS
# =========================================================
def print_results(products):
    print(
        "========================================"
    )
    print(
        "IPE / ZOOB AHAAN ISFAHAN"
    )
    print(
        "========================================"
    )
    if not products:
        print(
            "NO VALID IPE PRODUCTS FOUND"
        )
        return
    print(
        f"VALID PRODUCTS: {len(products)}"
    )
    print()
    for item in products:
        size = item["size"]
        delivery = item["delivery"]
        unit = item["unit"]
        weight = item["weight"]
        price = item["price"]
        print(
            f"IPE {size} | "
            f"Delivery: {delivery} | "
            f"Unit: {unit} | "
            f"Weight: {weight} | "
            f"Price: {price:,} تومان"
        )
    print()
    print(
        "========================================"
    )
    print(
        "IPE TEST FINISHED"
    )
    print(
        "========================================"
    )
# =========================================================
# MAIN
# =========================================================
def main():
    print(
        "========================================"
    )
    print(
        "IPE PRICE BOT - TEST"
    )
    print(
        "========================================"
    )
    products = parse_ipe_prices()
    print_results(
        products
    )
# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    main()