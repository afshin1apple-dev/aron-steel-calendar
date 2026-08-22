import os
import json
import requests
from datetime import datetime

# =========================================================
# SETTINGS
# =========================================================

API_URL = "https://www.ibrokers.ir/api/announcements"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HISTORY_FILE = "sent_history.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# =========================================================
# VERY IMPORTANT
# حداکثر یک پیام در هر اجرای ربات
# =========================================================

MAX_SEND_PER_RUN = 1

# =========================================================
# کلمات مربوط به فولاد
# =========================================================

STEEL_WORDS = [
    "میلگرد",
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
    "ضایعات فلزی",
    "ضایعات آهن",
    "آهن اسفنجی",
]


# =========================================================
# تاریخ امروز شمسی
# =========================================================

def get_today_jalali():

    # GitHub معمولاً UTC است.
    # برای ایران UTC+3:30 در نظر گرفته می‌شود.

    from datetime import timedelta, timezone

    iran_tz = timezone(timedelta(hours=3, minutes=30))

    now = datetime.now(iran_tz)

    gy = now.year
    gm = now.month
    gd = now.day

    # تبدیل میلادی به شمسی
    g_d_m = [0, 31, 59, 90, 120, 151,
             181, 212, 243, 273, 304, 334]

    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621

    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy

    days = (
        365 * gy
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        - 80
        + gd
        + g_d_m[gm - 1]
    )

    jy += 33 * (days // 12053)
    days %= 12053

    jy += 4 * (days // 1461)
    days %= 1461

    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365

    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30

    return f"{jy:04d}/{jm:02d}/{jd:02d}"


# =========================================================
# تبدیل تاریخ شمسی به عدد قابل مقایسه
# =========================================================

def jalali_to_int(date_value):

    if not date_value:
        return None

    text = str(date_value).strip()

    text = (
        text.replace("-", "/")
        .replace(".", "/")
        .replace("\\", "/")
    )

    parts = text.split("/")

    if len(parts) != 3:
        return None

    try:

        y = int(parts[0])
        m = int(parts[1])
        d = int(parts[2])

        return y * 10000 + m * 100 + d

    except Exception:
        return None


# =========================================================
# پیدا کردن مقدار از کلیدها
# =========================================================

def get_value(item, keys):

    for key in keys:

        if key in item:

            value = item.get(key)

            if value not in [None, "", "null"]:

                return value

    return None


# =========================================================
# دریافت API
# =========================================================

def get_announcements(limit=100):

    try:

        response = requests.get(
            API_URL,
            params={
                "page": 1,
                "limit": limit
            },
            headers=HEADERS,
            timeout=30
        )

        print("=" * 70)
        print("iBROKERS API")
        print("=" * 70)

        print("STATUS:", response.status_code)
        print("URL:", response.url)

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            print("API SUCCESS = FALSE")

            return []

        records = data.get("data", [])

        print(
            "TOTAL:",
            data.get("pagination", {}).get("total")
        )

        print("RECORDS:", len(records))

        return records

    except Exception as e:

        print("=" * 70)
        print("API ERROR")
        print("=" * 70)

        print(repr(e))

        return []


# =========================================================
# تشخیص فولادی بودن
# =========================================================

def is_steel(item):

    product = str(
        get_value(
            item,
            [
                "productName",
                "product",
                "product_name",
                "commodity",
                "commodity_name",
                "title",
                "name",
            ]
        ) or ""
    ).lower()

    for word in STEEL_WORDS:

        if word.lower() in product:

            return True

    return False


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
            "announcement_date",
            "announcementDate",
        ]
    )


# =========================================================
# کد عرضه
# =========================================================

def get_offer_code(item):

    return get_value(
        item,
        [
            "offerCode",
            "offer_code",
            "code",
            "external_id",
            "id",
        ]
    )


# =========================================================
# تاریخچه ارسال‌ها
# =========================================================

def load_history():

    if not os.path.exists(HISTORY_FILE):

        return set()

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, list):

            return set(
                str(x)
                for x in data
            )

        return set()

    except Exception as e:

        print("HISTORY LOAD ERROR:", repr(e))

        return set()


def save_history(history):

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                sorted(list(history)),
                f,
                ensure_ascii=False,
                indent=2
            )

        print(
            "HISTORY SAVED:",
            len(history)
        )

    except Exception as e:

        print(
            "HISTORY SAVE ERROR:",
            repr(e)
        )


# =========================================================
# ساخت پیام
# =========================================================

def make_message(item):

    product = get_value(
        item,
        [
            "productName",
            "product",
            "product_name",
            "commodity",
            "commodity_name",
            "title",
            "name",
        ]
    )

    date = get_value(
        item,
        [
            "offerDate",
            "offer_date",
            "date",
            "announcement_date",
            "announcementDate",
        ]
    )

    offer_code = get_offer_code(item)

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
            "supplier",
            "supplier_name",
            "supplierName",
        ]
    )

    volume = get_value(
        item,
        [
            "availableVolume",
            "availableVolumeRaw",
            "volume",
            "quantity",
            "amount",
            "offer_volume",
            "offerVolume",
        ]
    )

    unit = get_value(
        item,
        [
            "unit",
            "measureUnit",
            "measure_unit",
        ]
    )

    base_price = get_value(
        item,
        [
            "basePrice",
            "basePriceRaw",
            "base_price",
            "price",
        ]
    )

    prepayment = get_value(
        item,
        [
            "prepaymentPercent",
            "prepaymentPercentRaw",
            "prepayment_percent",
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
            "tradeStatus",
        ]
    )

    message = f"""
🏭 عرضه جدید بورس کالا

📦 محصول: {product or "نامشخص"}

📅 تاریخ عرضه: {date or "نامشخص"}

🔢 کد عرضه: {offer_code or "نامشخص"}

🏛 تالار: {hall or "نامشخص"}

🏭 عرضه‌کننده: {producer or "نامشخص"}

📊 حجم عرضه: {volume or "نامشخص"}

⚖️ واحد: {unit or "نامشخص"}

💰 قیمت پایه: {base_price or "نامشخص"}

💳 پیش‌پرداخت: {prepayment or "نامشخص"}

💵 تسویه: {settlement or "نامشخص"}

📄 قرارداد: {contract or "نامشخص"}

📍 محل تحویل: {delivery or "نامشخص"}

📌 وضعیت: {status or "نامشخص"}

━━━━━━━━━━━━━━
🏭 آروند آرون استیل
"""

    return message.strip()


# =========================================================
# ارسال تلگرام
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

        print("=" * 70)
        print("TELEGRAM")
        print("=" * 70)

        print("STATUS:", response.status_code)

        if response.ok:

            print("TELEGRAM OK")

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
# اجرای اصلی
# =========================================================

def main():

    print("\n")
    print("=" * 70)
    print("BOURSE BOT START")
    print("=" * 70)

    today = get_today_jalali()

    today_int = jalali_to_int(today)

    print("TODAY:", today)

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    records = get_announcements(100)

    if not records:

        print(
            "\nهیچ رکوردی دریافت نشد."
        )

        return

    # =====================================================
    # پیدا کردن عرضه‌های فولادی معتبر
    # =====================================================

    candidates = []

    for item in records:

        if not is_steel(item):

            continue

        offer_code = get_offer_code(item)

        offer_date = get_offer_date(item)

        if not offer_code:

            continue

        offer_code = str(
            offer_code
        )

        # قبلاً ارسال شده؟
        if offer_code in history:

            print(
                "SKIP ALREADY SENT:",
                offer_code
            )

            continue

        date_int = jalali_to_int(
            offer_date
        )

        # تاریخ نامعتبر؟
        if date_int is None:

            print(
                "SKIP INVALID DATE:",
                offer_code,
                offer_date
            )

            continue

        # =================================================
        # فقط عرضه امروز یا آینده
        # =================================================

        if date_int < today_int:

            print(
                "SKIP OLD:",
                offer_code,
                offer_date
            )

            continue

        candidates.append(
            item
        )

    print("\n")
    print("=" * 70)
    print(
        "NEW STEEL CANDIDATES:",
        len(candidates)
    )
    print("=" * 70)

    # =====================================================
    # هیچ عرضه جدیدی نیست
    # =====================================================

    if not candidates:

        print(
            "\nهیچ عرضه فولادی جدیدی برای ارسال وجود ندارد."
        )

        return

    # =====================================================
    # مرتب‌سازی بر اساس تاریخ عرضه
    # =====================================================

    candidates.sort(
        key=lambda x: (
            jalali_to_int(
                get_offer_date(x)
            ) or 99999999
        )
    )

    # =====================================================
    # فقط یک مورد
    # =====================================================

    item = candidates[0]

    offer_code = str(
        get_offer_code(item)
    )

    print("\n")
    print("=" * 70)
    print(
        "SENDING ONLY ONE NEW OFFER:",
        offer_code
    )
    print("=" * 70)

    message = make_message(item)

    print("\nMESSAGE:")
    print(message)

    # =====================================================
    # ارسال
    # =====================================================

    success = send_telegram(
        message
    )

    # =====================================================
    # فقط در صورت موفقیت تاریخچه ذخیره شود
    # =====================================================

    if success:

        history.add(
            offer_code
        )

        save_history(
            history
        )

        print(
            "\nعرضه با موفقیت ثبت شد."
        )

    else:

        print(
            "\nارسال ناموفق بود؛ "
            "در تاریخچه ثبت نمی‌شود."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()