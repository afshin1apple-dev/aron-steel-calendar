import os
import json
import requests
from datetime import datetime

# =========================================================
# CONFIG
# =========================================================

API_URL = "https://www.ibrokers.ir/api/announcements"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# تعداد رکورد در هر درخواست
LIMIT = 100

# چند صفحه آخر API بررسی شود
# با 234168 رکورد و limit=100 حدود 2342 صفحه داریم.
# بررسی 5 صفحه آخر = حداکثر 500 رکورد آخر
LAST_PAGES_TO_CHECK = 5

# فقط عرضه‌های سال‌های جدید بورس کالا
# سال 1405 = سال جاری
MIN_YEAR = 1405


# =========================================================
# کلمات مربوط به فولاد
# =========================================================

STEEL_WORDS = [
    "میلگرد",
    "میل گرد",
    "تیرآهن",
    "تیر آهن",
    "نبشی",
    "ناودانی",
    "ورق",
    "شمش",
    "بلوم",
    "بیلت",
    "اسلب",
    "فولاد",
    "مفتول",
    "لوله",
    "آهن اسفنجی",
    "آهن اسفنجی بریکت",
    "بریکت",
    "ضایعات فلزی",
    "ضایعات آهن",
    "ضایعات فولادی",
    "مقاطع فولادی",
    "سبد میلگرد",
    "سبد تیرآهن",
]


# =========================================================
# دریافت یک صفحه از API
# =========================================================

def get_page(page, limit=LIMIT):

    try:

        response = requests.get(
            API_URL,
            params={
                "page": page,
                "limit": limit
            },
            headers=HEADERS,
            timeout=30
        )

        print(
            f"API PAGE {page} | "
            f"STATUS={response.status_code}"
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            print(
                f"API SUCCESS FALSE - PAGE {page}"
            )

            return [], {}

        records = data.get("data", [])

        pagination = data.get(
            "pagination",
            {}
        )

        return records, pagination

    except Exception as e:

        print(
            f"API ERROR PAGE {page}:",
            repr(e)
        )

        return [], {}


# =========================================================
# دریافت آخرین عرضه‌ها
# =========================================================

def get_latest_announcements():

    print("=" * 70)
    print("iBROKERS - FIND LATEST ANNOUNCEMENTS")
    print("=" * 70)

    # -----------------------------------------------------
    # ابتدا صفحه اول را فقط برای گرفتن TOTAL می‌گیریم
    # -----------------------------------------------------

    first_records, pagination = get_page(
        1,
        LIMIT
    )

    if not pagination:

        print("Pagination دریافت نشد.")

        return []

    total = pagination.get("total")

    print("TOTAL:", total)

    if not total:

        print("TOTAL نامعتبر است.")

        return []

    total_pages = (
        int(total) + LIMIT - 1
    ) // LIMIT

    print("TOTAL PAGES:", total_pages)

    # -----------------------------------------------------
    # صفحات انتهایی
    # -----------------------------------------------------

    start_page = max(
        1,
        total_pages - LAST_PAGES_TO_CHECK + 1
    )

    print(
        "CHECK PAGES:",
        start_page,
        "TO",
        total_pages
    )

    all_records = []

    for page in range(
        start_page,
        total_pages + 1
    ):

        records, _ = get_page(
            page,
            LIMIT
        )

        if records:

            all_records.extend(
                records
            )

    # -----------------------------------------------------
    # حذف تکراری‌ها
    # -----------------------------------------------------

    unique = {}

    for item in all_records:

        key = (
            item.get("id")
            or item.get("external_id")
            or item.get("offerCode")
        )

        if key is not None:

            unique[str(key)] = item

    records = list(
        unique.values()
    )

    print(
        "LAST PAGE RECORDS:",
        len(records)
    )

    return records


# =========================================================
# تبدیل اعداد فارسی به انگلیسی
# =========================================================

def normalize_digits(value):

    if value is None:
        return ""

    value = str(value)

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return value.translate(table)


# =========================================================
# تبدیل تاریخ شمسی به عدد قابل مقایسه
# =========================================================

def jalali_date_number(date):

    if not date:
        return 0

    date = normalize_digits(date)

    date = date.replace(
        "-",
        "/"
    )

    parts = date.split("/")

    if len(parts) != 3:
        return 0

    try:

        y = int(parts[0])
        m = int(parts[1])
        d = int(parts[2])

        return (
            y * 10000
            + m * 100
            + d
        )

    except:

        return 0


# =========================================================
# پیدا کردن مقدار از کلیدها
# =========================================================

def get_value(item, keys):

    for key in keys:

        if key in item:

            value = item.get(key)

            if value not in [
                None,
                "",
                "null"
            ]:

                return value

    return None


# =========================================================
# تاریخ عرضه
# =========================================================

def get_offer_date(item):

    return get_value(
        item,
        [
            "offerDate",
            "offer_date",
            "date",
            "announcementDate",
            "announcement_date",
        ]
    )


# =========================================================
# تشخیص محصول فولادی
# =========================================================

def is_steel(item):

    product = get_value(
        item,
        [
            "productName",
            "product_name",
            "product",
            "commodityName",
            "commodity_name",
            "commodity",
            "title",
            "name",
        ]
    )

    if product:

        product_text = str(
            product
        ).lower()

        for word in STEEL_WORDS:

            if word.lower() in product_text:

                return True

    # -----------------------------------------------------
    # اگر در نام محصول نبود، کل رکورد بررسی شود
    # -----------------------------------------------------

    text = json.dumps(
        item,
        ensure_ascii=False
    ).lower()

    for word in STEEL_WORDS:

        if word.lower() in text:

            return True

    return False


# =========================================================
# فقط داده‌های سال 1405 به بعد
# =========================================================

def is_current_offer(item):

    date = get_offer_date(
        item
    )

    number = jalali_date_number(
        date
    )

    if number == 0:

        return False

    year = number // 10000

    return year >= MIN_YEAR


# =========================================================
# مرتب‌سازی تاریخ
# =========================================================

def sort_key(item):

    date = get_offer_date(
        item
    )

    return jalali_date_number(
        date
    )


# =========================================================
# فرمت عدد
# =========================================================

def format_number(value):

    if value is None:
        return "نامشخص"

    value = str(value)

    if not value.strip():
        return "نامشخص"

    return value


# =========================================================
# ساخت پیام
# =========================================================

def make_message(item):

    product = get_value(
        item,
        [
            "productName",
            "product_name",
            "product",
            "commodityName",
            "commodity_name",
            "commodity",
            "title",
            "name",
        ]
    )

    date = get_offer_date(
        item
    )

    offer_code = get_value(
        item,
        [
            "offerCode",
            "offer_code",
            "code",
            "external_id",
        ]
    )

    hall = get_value(
        item,
        [
            "hall",
            "market",
            "market_name",
            "marketName",
            "hall_name",
            "hallName",
        ]
    )

    producer = get_value(
        item,
        [
            "producer",
            "producer_name",
            "producerName",
        ]
    )

    supplier = get_value(
        item,
        [
            "supplier",
            "supplier_name",
            "supplierName",
        ]
    )

    # -----------------------------------------------------
    # حجم واقعی API
    # -----------------------------------------------------

    volume = get_value(
        item,
        [
            "availableVolume",
            "availableVolumeRaw",
            "initVolume",
            "volume",
            "quantity",
            "amount",
            "offerVolume",
            "offer_volume",
        ]
    )

    # -----------------------------------------------------
    # قیمت پایه واقعی API
    # -----------------------------------------------------

    base_price = get_value(
        item,
        [
            "basePrice",
            "basePriceRaw",
            "base_price",
            "price",
            "initPrice",
        ]
    )

    prepayment = get_value(
        item,
        [
            "prepaymentPercent",
            "prepaymentPercentRaw",
        ]
    )

    unit = get_value(
        item,
        [
            "unit",
        ]
    )

    settlement = get_value(
        item,
        [
            "settlementType",
            "settlement_type",
        ]
    )

    contract = get_value(
        item,
        [
            "contractType",
            "contract_type",
        ]
    )

    delivery = get_value(
        item,
        [
            "deliveryLocation",
            "delivery_location",
        ]
    )

    status = get_value(
        item,
        [
            "status",
        ]
    )

    # -----------------------------------------------------
    # مقادیر پیش‌فرض
    # -----------------------------------------------------

    if product is None:
        product = "نامشخص"

    if date is None:
        date = "نامشخص"

    if offer_code is None:
        offer_code = "نامشخص"

    if hall is None:
        hall = "نامشخص"

    if producer is None:
        producer = supplier

    if producer is None:
        producer = "نامشخص"

    if volume is None:
        volume = "نامشخص"

    if base_price is None:
        base_price = "نامشخص"

    # -----------------------------------------------------
    # ساخت پیام
    # -----------------------------------------------------

    lines = [
        "🏭 عرضه جدید بورس کالا",
        "",
        f"📦 محصول: {product}",
        "",
        f"📅 تاریخ عرضه: {date}",
        "",
        f"🔢 کد عرضه: {offer_code}",
        "",
        f"🏛 تالار: {hall}",
        "",
        f"🏭 عرضه‌کننده: {producer}",
        "",
        f"📊 حجم عرضه: {format_number(volume)}",
    ]

    if unit:
        lines.append(
            f"📏 واحد: {unit}"
        )

    lines.extend(
        [
            "",
            f"💰 قیمت پایه: {format_number(base_price)}",
        ]
    )

    if prepayment:
        lines.extend(
            [
                "",
                f"💳 پیش‌پرداخت: {prepayment}",
            ]
        )

    if settlement:
        lines.extend(
            [
                "",
                f"💵 تسویه: {settlement}",
            ]
        )

    if contract:
        lines.extend(
            [
                "",
                f"📄 قرارداد: {contract}",
            ]
        )

    if delivery:
        lines.extend(
            [
                "",
                f"📍 محل تحویل: {delivery}",
            ]
        )

    if status:
        lines.extend(
            [
                "",
                f"📌 وضعیت: {status}",
            ]
        )

    lines.extend(
        [
            "",
            "━━━━━━━━━━━━━━",
            "🏭 آروند آرون استیل",
        ]
    )

    return "\n".join(
        lines
    )


# =========================================================
# ارسال به تلگرام
# =========================================================

def send_telegram(message):

    try:

        response = requests.post(
            TELEGRAM_URL,
            json={
                "chat_id": CHANNEL_ID,
                "text": message
            },
            timeout=30
        )

        print(
            "TELEGRAM STATUS:",
            response.status_code
        )

        if response.ok:

            print(
                "TELEGRAM OK"
            )

            return True

        print(
            response.text[:1000]
        )

        return False

    except Exception as e:

        print(
            "TELEGRAM ERROR:",
            repr(e)
        )

        return False


# =========================================================
# MAIN
# =========================================================

def main():

    records = get_latest_announcements()

    if not records:

        print(
            "\nهیچ رکوردی دریافت نشد."
        )

        return

    print(
        "\n" + "=" * 70
    )

    print(
        "LATEST RECORDS"
    )

    print(
        "=" * 70
    )

    # -----------------------------------------------------
    # مرتب‌سازی از جدید به قدیم
    # -----------------------------------------------------

    records.sort(
        key=sort_key,
        reverse=True
    )

    # -----------------------------------------------------
    # فقط عرضه‌های 1405 به بعد
    # -----------------------------------------------------

    current_records = []

    for item in records:

        if is_current_offer(item):

            current_records.append(
                item
            )

    print(
        "CURRENT RECORDS:",
        len(current_records)
    )

    # -----------------------------------------------------
    # نمایش عرضه‌های جدید
    # -----------------------------------------------------

    for index, item in enumerate(
        current_records[:30],
        1
    ):

        product = get_value(
            item,
            [
                "productName",
                "product_name",
                "product",
                "commodityName",
                "commodity",
            ]
        )

        date = get_offer_date(
            item
        )

        hall = get_value(
            item,
            [
                "hall",
                "market",
                "marketName",
            ]
        )

        print(
            f"{index}. "
            f"{date} | "
            f"{product} | "
            f"{hall}"
        )

    # -----------------------------------------------------
    # فولادی‌ها
    # -----------------------------------------------------

    steel_records = [
        item
        for item in current_records
        if is_steel(item)
    ]

    print(
        "\n" + "=" * 70
    )

    print(
        "STEEL RECORDS:",
        len(steel_records)
    )

    print(
        "=" * 70
    )

    if not steel_records:

        print(
            "هیچ عرضه فولادی جدیدی پیدا نشد."
        )

        return

    # -----------------------------------------------------
    # ارسال همه عرضه‌های فولادی
    # -----------------------------------------------------

    sent = 0

    for index, item in enumerate(
        steel_records,
        1
    ):

        print(
            f"\nارسال عرضه فولادی "
            f"{index} از "
            f"{len(steel_records)}"
        )

        message = make_message(
            item
        )

        print(
            "\nMESSAGE:"
        )

        print(
            message
        )

        if send_telegram(
            message
        ):

            sent += 1

    print(
        "\n" + "=" * 70
    )

    print(
        "FINISHED"
    )

    print(
        "STEEL:",
        len(steel_records)
    )

    print(
        "SENT:",
        sent
    )

    print(
        "=" * 70
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()