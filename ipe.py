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
# ALLOWED SIZES
# =========================================================
ALLOWED_SIZES = {
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
# CLEAN TEXT
# =========================================================
def clean_text(value):
    text = normalize_number(value)
    text = text.replace(
        "\u200c",
        " "
    )
    text = text.replace(
        "\n",
        " "
    )
    text = re.sub(
        r"\s+",
        " ",
        text
    )
    return text.strip()
# =========================================================
# EXTRACT NUMBERS
# =========================================================
def extract_numbers(value):
    text = normalize_number(value)
    text = text.replace(
        "٬",
        ","
    )
    return re.findall(
        r"\d[\d,]*(?:\.\d+)?",
        text
    )
# =========================================================
# EXTRACT PRICE
# =========================================================
def extract_price(value):
    if value is None:
        return None
    text = clean_text(value)
    if "تماس" in text:
        return None
    numbers = extract_numbers(
        text
    )
    if not numbers:
        return None
    candidates = []
    for number in numbers:
        try:
            number_clean = (
                number
                .replace(",", "")
            )
            value_int = int(
                float(number_clean)
            )
            if value_int >= 1000:
                candidates.append(
                    value_int
                )
        except Exception:
            continue
    if not candidates:
        return None
    return candidates[-1]
# =========================================================
# EXTRACT SIZE
# =========================================================
def extract_size(row_text):
    text = clean_text(
        row_text
    )
    # حالت‌هایی مثل:
    # تیرآهن 14
    # IPE 14
    # 14
    patterns = [
        r"IPE\s*(\d{2})",
        r"تیرآهن\s*(\d{2})",
        r"\b(\d{2})\b",
    ]
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )
        if not match:
            continue
        size = match.group(1)
        if size in ALLOWED_SIZES:
            return size
    return None
# =========================================================
# DETECT DELIVERY
# =========================================================
def detect_delivery(row_text):
    text = clean_text(
        row_text
    )
    if "کارخانه" in text:
        return "کارخانه"
    if (
        "تهران" in text
        or "انبار" in text
    ):
        return "تهران"
    return None
# =========================================================
# DETECT UNIT
# =========================================================
def detect_unit(row_text):
    text = clean_text(
        row_text
    )
    if "کیلوگرم" in text:
        return "کیلوگرم"
    if "کیلو" in text:
        return "کیلوگرم"
    if "شاخه" in text:
        return "شاخه"
    return None
# =========================================================
# EXTRACT WEIGHT
# =========================================================
def extract_weight(values):
    # ابتدا دنبال سلولی می‌گردیم که
    # وزن یا کیلو در آن ذکر شده باشد.
    for value in values:
        text = clean_text(
            value
        )
        if (
            "وزن" not in text
            and "کیلو" not in text
            and "kg" not in text.lower()
        ):
            continue
        numbers = extract_numbers(
            text
        )
        if not numbers:
            continue
        try:
            number = (
                numbers[0]
                .replace(",", "")
            )
            weight = float(
                number
            )
            if 1 <= weight <= 500:
                return weight
        except Exception:
            continue
    return None
# =========================================================
# PARSE TABLE ROW
# =========================================================
def parse_row(values):
    if len(values) < 4:
        return None
    row_text = " | ".join(
        values
    )
    size = extract_size(
        row_text
    )
    if size is None:
        return None
    delivery = detect_delivery(
        row_text
    )
    if delivery is None:
        return None
    unit = detect_unit(
        row_text
    )
    if unit is None:
        return None
    # -----------------------------------------------------
    # وزن
    # -----------------------------------------------------
    weight = extract_weight(
        values
    )
    # -----------------------------------------------------
    # قیمت
    # -----------------------------------------------------
    price = None
    # قیمت معمولاً در انتهای ردیف است،
    # بنابراین از آخر به اول بررسی می‌کنیم.
    for value in reversed(values):
        candidate = extract_price(
            value
        )
        if candidate is None:
            continue
        # جلوگیری از اشتباه گرفتن وزن،
        # سایز یا اعداد کوچک با قیمت
        if candidate < 10000:
            continue
        price = candidate
        break
    if price is None:
        return None
    return {
        "size": size,
        "delivery": delivery,
        "unit": unit,
        "weight": weight,
        "price": price,
    }
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
# PARSE IPE
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
            StringIO(
                response.text
            )
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
    factory_prices = {}
    tehran_prices = {}
    # =====================================================
    # CHECK ALL TABLES
    # =====================================================
    for table_index, df in enumerate(
        tables
    ):
        print(
            f"Checking table {table_index + 1}: "
            f"{df.shape}"
        )
        for _, row in df.iterrows():
            values = [
                clean_text(x)
                for x in row.tolist()
            ]
            result = parse_row(
                values
            )
            if result is None:
                continue
            size = result[
                "size"
            ]
            delivery = result[
                "delivery"
            ]
            # -------------------------------------------------
            # کارخانه
            # -------------------------------------------------
            if delivery == "کارخانه":
                factory_prices[
                    size
                ] = result
            # -------------------------------------------------
            # تهران
            # -------------------------------------------------
            elif delivery == "تهران":
                tehran_prices[
                    size
                ] = result
    # =====================================================
    # BUILD FINAL RESULT
    # =====================================================
    results = []
    for size in sorted(
        ALLOWED_SIZES,
        key=lambda x: int(x)
    ):
        factory = factory_prices.get(
            size
        )
        tehran = tehran_prices.get(
            size
        )
        if factory is None and tehran is None:
            continue
        results.append(
            {
                "size": size,
                "factory": (
                    factory
                    if factory
                    else None
                ),
                "tehran": (
                    tehran
                    if tehran
                    else None
                ),
            }
        )
    return results
# =========================================================
# PRINT RESULTS
# =========================================================
def print_results(results):
    print(
        "========================================"
    )
    print(
        "IPE / ZOOB AHAAN ISFAHAN"
    )
    print(
        "========================================"
    )
    if not results:
        print(
            "NO VALID IPE PRODUCTS FOUND"
        )
        return
    print(
        f"VALID SIZES: {len(results)}"
    )
    print()
    for item in results:
        size = item[
            "size"
        ]
        factory = item[
            "factory"
        ]
        tehran = item[
            "tehran"
        ]
        print(
            f"---------- IPE {size} ----------"
        )
        # -------------------------------------------------
        # کارخانه
        # -------------------------------------------------
        if factory:
            print(
                "FACTORY:"
            )
            print(
                f"  Delivery: "
                f"{factory['delivery']}"
            )
            print(
                f"  Unit: "
                f"{factory['unit']}"
            )
            print(
                f"  Weight: "
                f"{factory['weight']}"
            )
            print(
                f"  Price: "
                f"{factory['price']:,} تومان"
            )
        else:
            print(
                "FACTORY: NOT FOUND"
            )
        # -------------------------------------------------
        # تهران
        # -------------------------------------------------
        if tehran:
            print(
                "TEHRAN:"
            )
            print(
                f"  Delivery: "
                f"{tehran['delivery']}"
            )
            print(
                f"  Unit: "
                f"{tehran['unit']}"
            )
            print(
                f"  Weight: "
                f"{tehran['weight']}"
            )
            print(
                f"  Price: "
                f"{tehran['price']:,} تومان"
            )
        else:
            print(
                "TEHRAN: NOT FOUND"
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
    results = parse_ipe_prices()
    print_results(
        results
    )
# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    main()