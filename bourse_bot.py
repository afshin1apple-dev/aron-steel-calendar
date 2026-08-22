import os
import json
import requests
from datetime import datetime, timezone, timedelta


# =========================================================
# SETTINGS
# =========================================================

API_URL = "https://www.ibrokers.ir/api/announcements"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HISTORY_FILE = "sent_history.json"

# حداکثر تعداد پست در هر اجرا
MAX_SEND = 5

# چند صفحه از API بررسی شود
MAX_PAGES = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# تبدیل میلادی به شمسی - بدون کتابخانه اضافی
# =========================================================

def gregorian_to_jalali(gy, gm, gd):

    g_days_in_month = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    j_days_in_month = [
        31, 31, 31, 31, 31, 31,
        30, 30, 30, 30, 30, 29
    ]

    gy2 = gy - 1600
    jy = 979

    if gy2 >= 0:
        leap_adjust = gy2 // 400
    else:
        leap_adjust = (gy2 - 399) // 400

    g_day_no = (
        365 * gy2
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
        - 80
    )

    for i in range(gm - 1):
        g_day_no += g_days_in_month[i]

    if gm > 2 and (
        gy % 4 == 0
        and (gy % 100 != 0 or gy % 400 == 0)
    ):
        g_day_no += 1

    g_day_no += gd

    j_day_no = g_day_no

    jy += 33 * (j_day_no // 12053)

    j_day_no %= 12053

    jy += 4 * (j_day_no // 1461)

    j_day_no %= 1461

    if j_day_no >= 366:

        jy += (j_day_no - 1) // 365

        j_day_no = (j_day_no - 1) % 365

    i = 0

    while (
        i < 11
        and j_day_no >= j_days_in_month[i]
    ):

        j_day_no -= j_days_in_month[i]
        i += 1

    jm = i + 1
    jd = j_day_no + 1

    return jy, jm, jd


# =========================================================
# تاریخ امروز ایران
# =========================================================

def today_jalali():

    # ایران در مرداد 1405 برابر UTC+3:30 است
    iran_tz = timezone(
        timedelta(hours=3, minutes=30)
    )

    now = datetime.now(iran_tz)

    jy, jm, jd = gregorian_to_jalali(
        now.year,
        now.month,
        now.day
    )

    return f"{jy:04d}/{jm:02d}/{jd:02d}"


# =========================================================
# تبدیل تاریخ شمسی به عدد
# =========================================================

def jalali_to_number(date_string):

    if not date_string:
        return 0

    try:

        date_string = str(date_string)

        date_string = (
            date_string
            .replace("-", "/")
            .replace(".", "/")
            .strip()
        )

        parts = date_string.split("/")

        if len(parts) != 3:
            return 0

        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])

        return (
            year * 10000
            + month * 100
            + day
        )

    except Exception:

        return 0


# =========================================================
# TODAY
# =========================================================

TODAY = today_jalali()
TODAY_NUMBER = jalali_to_number(TODAY)


# =========================================================
# HISTORY
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

        print(
            "HISTORY LOAD ERROR:",
            repr(e)
        )

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

        return True

    except Exception as e:

        print(
            "HISTORY SAVE ERROR:",
            repr(e)
        )

        return False


# =========================================================
# API
# =========================================================

def get_announcements(
    page=1,
    limit=100
):

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
            f"API PAGE {page} "
            f"STATUS:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            print(
                "API SUCCESS = FALSE"
            )

            return [], {}

        records = data.get(
            "data",
            []
        )

        pagination = data.get(
            "pagination",
            {}
        )

        return (
            records,
            pagination
        )

    except Exception as e:

        print(
            f"API PAGE {page} ERROR:",
            repr(e)
        )

        return [], {}


# =========================================================
# GET VALUE
# =========================================================

def get_value(item, keys):

    for key in keys:

        if key in item:

            value = item.get(key)

            if value not in [
                None,
                "",
                "null",
                "None"
            ]:

                return value

    return None


# =========================================================
# OFFER DATE
# =========================================================

def get_offer_date(item):

    return get_value(
        item,
        [
            "date",
            "offer_date",
            "announcement_date",
            "offerDate",
            "announcementDate",
            "delivery_date",
            "deliveryDate",
            "offer_date_jalali",
            "offerDateJalali",
        ]
    )


# =========================================================
# OFFER CODE
# =========================================================

def get_offer_code(item):

    return get_value(
        item,
        [
            "offer_code",
            "offerCode",
            "code",
            "offer_id",
            "offerId",
            "id",
        ]
    )


# =========================================================
# PRODUCT
# =========================================================

def get_product(item):

    return get_value(
        item,
        [
            "product",
            "product_name",
            "commodity",
            "commodity_name",
            "title",
            "name",
            "goods_name",
            "productTitle",
            "productName",
            "commodityName",
        ]
    )


# =========================================================
# STEEL WORDS
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
    "ضایعات فولادی",
    "آهن",
    "کلاف",
    "ریل",
    "چدن",

]


# =========================================================
# IS STEEL
# =========================================================

def is_steel(item):

    text = json.dumps(
        item,
        ensure_ascii=False
    ).lower()

    for word in STEEL_WORDS:

        if word.lower() in text:

            return True

    return False


# =========================================================
# MESSAGE
# =========================================================

def make_message(item):

    product = get_product(item)

    date = get_offer_date(item)

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
            "unit_name",
            "unitName",
        ]
    )

    base_price = get_value(
        item,
        [
            "base_price",
            "basePrice",
            "price",
            "base_price_value",
            "basePriceValue",
        ]
    )

    prepayment = get_value(
        item,
        [
            "prepayment",
            "prePayment",
            "prepayment_percent",
            "prepaymentPercent",
        ]
    )

    payment = get_value(
        item,
        [
            "payment",
            "payment_type",
            "paymentType",
            "settlement",
            "settlement_type",
            "settlementType",
        ]
    )

    contract = get_value(
        item,
        [
            "contract",
            "contract_type",
            "contractType",
        ]
    )

    delivery = get_value(
        item,
        [
            "delivery",
            "delivery_place",
            "deliveryPlace",
            "delivery_location",
            "deliveryLocation",
        ]
    )

    status = get_value(
        item,
        [
            "status",
            "offer_status",
            "offerStatus",
        ]
    )

    product = product or "نامشخص"
    date = date or "نامشخص"
    offer_code = offer_code or "نامشخص"
    hall = hall or "نامشخص"
    producer = producer or "نامشخص"
    volume = volume or "نامشخص"
    unit = unit or "نامشخص"
    base_price = base_price or "نامشخص"
    prepayment = prepayment or "نامشخص"
    payment = payment or "نامشخص"
    contract = contract or "نامشخص"
    delivery = delivery or "نامشخص"
    status = status or "نامشخص"

    return f"""🏭 عرضه جدید بورس کالا

📦 محصول: {product}

📅 تاریخ عرضه: {date}

🔢 کد عرضه: {offer_code}

🏛 تالار: {hall}

🏭 عرضه‌کننده: {producer}

📊 حجم عرضه: {volume}

⚖️ واحد: {unit}

💰 قیمت پایه: {base_price}

💳 پیش‌پرداخت: {prepayment}

💵 تسویه: {payment}

📄 قرارداد: {contract}

📍 محل تحویل: {delivery}

📌 وضعیت: {status}

━━━━━━━━━━━━━━
🏭 آروند آرون استیل
"""


# =========================================================
# TELEGRAM
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

            result = response.json()

            if result.get("ok"):

                print(
                    "TELEGRAM OK"
                )

                return True

        print(
            "TELEGRAM ERROR:",
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

    print()
    print("=" * 70)
    print("BOURSE BOT START")
    print("=" * 70)

    print(
        "TODAY:",
        TODAY
    )

    print(
        "TODAY NUMBER:",
        TODAY_NUMBER
    )

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    # -----------------------------------------------------
    # دریافت صفحات
    # -----------------------------------------------------

    all_records = []

    for page in range(
        1,
        MAX_PAGES + 1
    ):

        records, pagination = get_announcements(
            page=page,
            limit=100
        )

        if not records:

            break

        all_records.extend(
            records
        )

        print(
            f"PAGE {page}: "
            f"{len(records)} records"
        )

        # اگر صفحه کمتر از 100 رکورد داشت
        if len(records) < 100:

            break

    print()
    print("=" * 70)
    print(
        "TOTAL DOWNLOADED:",
        len(all_records)
    )
    print("=" * 70)

    # -----------------------------------------------------
    # بررسی عرضه ها
    # -----------------------------------------------------

    candidates = []

    seen_codes = set()

    for item in all_records:

        # فقط فولادی
        if not is_steel(item):

            continue

        offer_code = get_offer_code(
            item
        )

        if offer_code is None:

            continue

        offer_code = str(
            offer_code
        )

        # جلوگیری از تکرار
        if offer_code in seen_codes:

            continue

        seen_codes.add(
            offer_code
        )

        offer_date = get_offer_date(
            item
        )

        offer_number = jalali_to_number(
            offer_date
        )

        # تاریخ نامعتبر
        if offer_number == 0:

            print(
                "SKIP INVALID DATE:",
                offer_code,
                offer_date
            )

            continue

        # عرضه قدیمی
        if offer_number < TODAY_NUMBER:

            print(
                "SKIP OLD:",
                offer_code,
                offer_date
            )

            continue

        # قبلاً ارسال شده
        if offer_code in history:

            print(
                "SKIP SENT:",
                offer_code
            )

            continue

        candidates.append(
            item
        )

    # -----------------------------------------------------
    # مرتب سازی
    # -----------------------------------------------------

    candidates.sort(
        key=lambda item:
        jalali_to_number(
            get_offer_date(item)
        )
    )

    print()
    print("=" * 70)
    print(
        "NEW STEEL CANDIDATES:",
        len(candidates)
    )
    print("=" * 70)

    # -----------------------------------------------------
    # هیچ عرضه جدید
    # -----------------------------------------------------

    if not candidates:

        print(
            "هیچ عرضه فولادی جدیدی "
            "برای ارسال وجود ندارد."
        )

        return

    # -----------------------------------------------------
    # فقط MAX_SEND
    # -----------------------------------------------------

    send_list = candidates[
        :MAX_SEND
    ]

    print(
        "WILL SEND:",
        len(send_list)
    )

    # -----------------------------------------------------
    # ارسال
    # -----------------------------------------------------

    sent_count = 0

    for index, item in enumerate(
        send_list,
        1
    ):

        offer_code = str(
            get_offer_code(item)
        )

        print()
        print("=" * 70)
        print(
            f"ارسال عرضه "
            f"{index} از "
            f"{len(send_list)}"
        )
        print(
            "CODE:",
            offer_code
        )
        print("=" * 70)

        message = make_message(
            item
        )

        print(
            "\nMESSAGE:"
        )

        print(message)

        success = send_telegram(
            message
        )

        if success:

            history.add(
                offer_code
            )

            save_history(
                history
            )

            sent_count += 1

            print(
                "HISTORY SAVED:",
                len(history)
            )

        else:

            print(
                "ارسال ناموفق بود."
            )

    print()
    print("=" * 70)
    print(
        "FINISHED - SENT:",
        sent_count
    )
    print("=" * 70)


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()