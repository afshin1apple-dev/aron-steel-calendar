import os
import json
import requests

# =========================================================
# SETTINGS
# =========================================================

API_URL = "https://www.ibrokers.ir/api/announcements"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HISTORY_FILE = "sent_offers.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# تاریخچه ارسال‌ها
# =========================================================

def load_history():

    try:

        if not os.path.exists(HISTORY_FILE):
            return set()

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, list):
            return set()

        return set(str(x) for x in data)

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

        print("HISTORY SAVED:", len(history))

    except Exception as e:

        print("HISTORY SAVE ERROR:", repr(e))


# =========================================================
# دریافت اطلاعات بورس کالا
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

            print(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2
                )
            )

            return []

        records = data.get("data", [])

        print(
            "TOTAL:",
            data.get("pagination", {}).get("total")
        )

        print(
            "RECORDS:",
            len(records)
        )

        return records

    except Exception as e:

        print("=" * 70)
        print("API ERROR")
        print("=" * 70)

        print(repr(e))

        return []


# =========================================================
# دریافت مقدار واقعی از API
# =========================================================

def get_value(item, keys):

    for key in keys:

        value = item.get(key)

        if value is not None and value != "":

            return value

    return None


# =========================================================
# تشخیص فولادی بودن
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
    "بریکت",
]


def is_steel(item):

    product = str(
        get_value(
            item,
            [
                "productName",
                "product",
                "commodityName",
                "commodity",
                "title",
                "name"
            ]
        ) or ""
    ).lower()

    for word in STEEL_WORDS:

        if word.lower() in product:
            return True

    return False


# =========================================================
# شناسه یکتای عرضه
# =========================================================

def get_offer_id(item):

    value = get_value(
        item,
        [
            "offerCode",
            "external_id",
            "id"
        ]
    )

    if value is None:
        return None

    return str(value)


# =========================================================
# تبدیل عدد به فارسی
# =========================================================

def persian_number(value):

    if value is None:
        return "نامشخص"

    text = str(value)

    english = "0123456789"
    persian = "۰۱۲۳۴۵۶۷۸۹"

    table = str.maketrans(
        english,
        persian
    )

    return text.translate(table)


# =========================================================
# ساخت پیام
# =========================================================

def make_message(item):

    product = get_value(
        item,
        [
            "productName",
            "product",
            "commodityName",
            "commodity",
            "title",
            "name"
        ]
    )

    offer_date = get_value(
        item,
        [
            "offerDate",
            "offer_date",
            "date"
        ]
    )

    offer_code = get_value(
        item,
        [
            "offerCode",
            "offer_code",
            "external_id",
            "id"
        ]
    )

    hall = get_value(
        item,
        [
            "hall",
            "market",
            "marketName"
        ]
    )

    supplier = get_value(
        item,
        [
            "supplier",
            "supplierName",
            "producer",
            "producerName"
        ]
    )

    volume = get_value(
        item,
        [
            "availableVolume",
            "availableVolumeRaw",
            "initVolume",
            "volume"
        ]
    )

    unit = get_value(
        item,
        [
            "unit"
        ]
    )

    base_price = get_value(
        item,
        [
            "basePrice",
            "basePriceRaw",
            "base_price"
        ]
    )

    prepayment = get_value(
        item,
        [
            "prepaymentPercent",
            "prepaymentPercentRaw"
        ]
    )

    settlement = get_value(
        item,
        [
            "settlementType"
        ]
    )

    contract = get_value(
        item,
        [
            "contractType"
        ]
    )

    delivery = get_value(
        item,
        [
            "deliveryLocation"
        ]
    )

    status = get_value(
        item,
        [
            "status"
        ]
    )

    # -------------------------
    # مقدارهای پیش‌فرض
    # -------------------------

    product = product or "نامشخص"
    offer_date = offer_date or "نامشخص"
    offer_code = offer_code or "نامشخص"
    hall = hall or "نامشخص"
    supplier = supplier or "نامشخص"

    # -------------------------
    # حجم
    # -------------------------

    if volume is None:

        volume_text = "نامشخص"

    else:

        volume_text = persian_number(volume)

        if unit:
            volume_text += f"\n⚖️ واحد: {unit}"

    # -------------------------
    # قیمت
    # -------------------------

    if base_price is None:

        price_text = "نامشخص"

    else:

        price_text = persian_number(base_price)

    # -------------------------
    # پیش پرداخت
    # -------------------------

    if prepayment is not None:

        prepayment_text = persian_number(
            prepayment
        )

        if "%" not in str(prepayment_text):
            prepayment_text += "%"

    else:

        prepayment_text = "نامشخص"

    # -------------------------
    # پیام
    # -------------------------

    message = f"""🏭 عرضه جدید بورس کالا

📦 محصول: {product}

📅 تاریخ عرضه: {offer_date}

🔢 کد عرضه: {offer_code}

🏛 تالار: {hall}

🏭 عرضه‌کننده: {supplier}

📊 حجم عرضه: {volume_text}

💰 قیمت پایه: {price_text}

💳 پیش‌پرداخت: {prepayment_text}

💵 تسویه: {settlement or "نامشخص"}

📄 قرارداد: {contract or "نامشخص"}

📍 محل تحویل: {delivery or "نامشخص"}

📌 وضعیت: {status or "نامشخص"}

━━━━━━━━━━━━━━
🏭 آروند آرون استیل"""

    return message


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

        print("\n" + "=" * 70)
        print("TELEGRAM")
        print("=" * 70)

        print(
            "STATUS:",
            response.status_code
        )

        print(
            response.text[:1000]
        )

        if response.ok:

            data = response.json()

            if data.get("ok"):

                print("TELEGRAM OK")

                return True

        print("TELEGRAM FAILED")

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

    print("\n")
    print("=" * 70)
    print("BOURSE BOT START")
    print("=" * 70)

    # -------------------------
    # تاریخچه
    # -------------------------

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    # -------------------------
    # دریافت API
    # -------------------------

    records = get_announcements(
        limit=100
    )

    if not records:

        print(
            "\nهیچ رکوردی دریافت نشد."
        )

        return

    # -------------------------
    # فولادی‌ها
    # -------------------------

    steel_records = []

    for item in records:

        if is_steel(item):

            steel_records.append(
                item
            )

    print("\n" + "=" * 70)

    print(
        "STEEL RECORDS:",
        len(steel_records)
    )

    print("=" * 70)

    # -------------------------
    # پیدا کردن اولین عرضه جدید
    # -------------------------

    new_offer = None

    for item in steel_records:

        offer_id = get_offer_id(item)

        if not offer_id:

            continue

        if offer_id in history:

            continue

        new_offer = item

        break

    # -------------------------
    # هیچ عرضه جدیدی نیست
    # -------------------------

    if new_offer is None:

        print(
            "\nهیچ عرضه فولادی جدیدی برای ارسال وجود ندارد."
        )

        return

    # -------------------------
    # فقط یک ارسال
    # -------------------------

    offer_id = get_offer_id(
        new_offer
    )

    print("\n")
    print(
        "ارسال فقط یک عرضه جدید:",
        offer_id
    )

    message = make_message(
        new_offer
    )

    print("\nMESSAGE:")
    print(message)

    # -------------------------
    # ارسال
    # -------------------------

    success = send_telegram(
        message
    )

    # -------------------------
    # فقط در صورت موفقیت ذخیره شود
    # -------------------------

    if success:

        history.add(
            offer_id
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
            "عرضه در تاریخچه ذخیره نشد."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()