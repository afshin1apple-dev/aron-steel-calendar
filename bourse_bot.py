import os
import json
import requests
from datetime import datetime

import pytz
import jdatetime


# =========================================================
# SETTINGS
# =========================================================

API_URL = "https://www.ibrokers.ir/api/announcements"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HISTORY_FILE = "sent_history.json"

# حداکثر تعداد پست در هر اجرای ربات
MAX_SEND = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

TEHRAN = pytz.timezone("Asia/Tehran")


# =========================================================
# تاریخ امروز ایران
# =========================================================

def today_jalali():

    now = datetime.now(TEHRAN)

    jdate = jdatetime.date.fromgregorian(
        year=now.year,
        month=now.month,
        day=now.day
    )

    return jdate.strftime("%Y/%m/%d")


# =========================================================
# تبدیل تاریخ شمسی به عدد قابل مقایسه
# =========================================================

def jalali_to_number(date_string):

    if not date_string:
        return 0

    try:

        parts = str(date_string).replace("-", "/").split("/")

        if len(parts) != 3:
            return 0

        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])

        return year * 10000 + month * 100 + day

    except Exception:

        return 0


# =========================================================
# تاریخ امروز
# =========================================================

TODAY = today_jalali()
TODAY_NUMBER = jalali_to_number(TODAY)


# =========================================================
# سابقه ارسال
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

                return set(str(x) for x in data)

            return set()

    except Exception:

        return set()


def save_history(history):

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


# =========================================================
# دریافت API
# =========================================================

def get_announcements(page=1, limit=100):

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

        print("=" * 70)
        print("iBROKERS API")
        print("=" * 70)

        print("STATUS:", response.status_code)
        print("URL:", response.url)

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            print("API SUCCESS = FALSE")

            return [], {}

        records = data.get("data", [])

        pagination = data.get(
            "pagination",
            {}
        )

        print(
            "TOTAL:",
            pagination.get("total")
        )

        print(
            "PAGE:",
            pagination.get("page")
        )

        print(
            "RECORDS:",
            len(records)
        )

        return records, pagination

    except Exception as e:

        print(
            "API ERROR:",
            repr(e)
        )

        return [], {}


# =========================================================
# پیدا کردن مقدار
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
# تشخیص تاریخ عرضه
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
# تشخیص کد عرضه
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
# کلمات فولادی
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
# تشخیص فولادی
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
# اطلاعات محصول
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
# ساخت پیام
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

    if product is None:
        product = "نامشخص"

    if date is None:
        date = "نامشخص"

    if offer_code is None:
        offer_code = "نامشخص"

    if hall is None:
        hall = "نامشخص"

    if producer is None:
        producer = "نامشخص"

    if volume is None:
        volume = "نامشخص"

    if unit is None:
        unit = ""

    if base_price is None:
        base_price = "نامشخص"

    if payment is None:
        payment = "نامشخص"

    if contract is None:
        contract = "نامشخص"

    if delivery is None:
        delivery = "نامشخص"

    if status is None:
        status = "نامشخص"

    message = f"""🏭 عرضه جدید بورس کالا

📦 محصول: {product}

📅 تاریخ عرضه: {date}

🔢 کد عرضه: {offer_code}

🏛 تالار: {hall}

🏭 عرضه‌کننده: {producer}

📊 حجم عرضه: {volume}

⚖️ واحد: {unit}

💰 قیمت پایه: {base_price}

💳 پیش‌پرداخت: {get_value(item, ["prepayment", "prePayment", "prepayment_percent", "prepaymentPercent"]) or "نامشخص"}

💵 تسویه: {payment}

📄 قرارداد: {contract}

📍 محل تحویل: {delivery}

📌 وضعیت: {status}

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

        print(
            "TELEGRAM STATUS:",
            response.status_code
        )

        if response.ok:

            result = response.json()

            if result.get("ok"):

                print("TELEGRAM OK")

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
# اجرای اصلی
# =========================================================

def main():

    print("\n")
    print("=" * 70)
    print("BOURSE BOT START")
    print("=" * 70)

    print("TODAY:", TODAY)

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    # -----------------------------------------------------
    # فقط چند صفحه اول را بررسی می‌کنیم
    # -----------------------------------------------------

    all_records = []

    MAX_PAGES = 10

    for page in range(1, MAX_PAGES + 1):

        records, pagination = get_announcements(
            page=page,
            limit=100
        )

        if not records:

            break

        all_records.extend(records)

        # اگر API تعداد صفحات را اعلام کرده
        total_pages = pagination.get(
            "totalPages"
        )

        if total_pages:

            if page >= int(total_pages):

                break

    print("\n")
    print("=" * 70)
    print("TOTAL DOWNLOADED:", len(all_records))
    print("=" * 70)

    # -----------------------------------------------------
    # پیدا کردن عرضه های فولادی جدید
    # -----------------------------------------------------

    candidates = []

    seen_codes = set()

    for item in all_records:

        if not is_steel(item):

            continue

        offer_code = get_offer_code(item)

        if offer_code is None:

            continue

        offer_code = str(offer_code)

        # جلوگیری از تکرار داخل API
        if offer_code in seen_codes:

            continue

        seen_codes.add(offer_code)

        offer_date = get_offer_date(item)

        offer_number = jalali_to_number(
            offer_date
        )

        # -------------------------------------------------
        # عرضه قدیمی
        # -------------------------------------------------

        if offer_number < TODAY_NUMBER:

            continue

        # -------------------------------------------------
        # قبلاً ارسال شده
        # -------------------------------------------------

        if offer_code in history:

            continue

        candidates.append(item)

    # -----------------------------------------------------
    # مرتب سازی بر اساس تاریخ عرضه
    # -----------------------------------------------------

    candidates.sort(
        key=lambda x: jalali_to_number(
            get_offer_date(x)
        )
    )

    print("\n")
    print("=" * 70)
    print(
        "NEW STEEL CANDIDATES:",
        len(candidates)
    )
    print("=" * 70)

    if not candidates:

        print(
            "هیچ عرضه فولادی جدیدی برای ارسال وجود ندارد."
        )

        return

    # -----------------------------------------------------
    # محدود کردن تعداد ارسال
    # -----------------------------------------------------

    send_list = candidates[:MAX_SEND]

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

        print("\n")
        print(
            "=" * 70
        )

        print(
            f"ارسال عرضه {index} از {len(send_list)}"
        )

        print(
            "CODE:",
            offer_code
        )

        message = make_message(item)

        print("\nMESSAGE:")
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
                "ارسال ناموفق بود؛ در History ثبت نشد."
            )

    print("\n")
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