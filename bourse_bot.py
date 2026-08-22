import os
import json
import requests

API_URL = "https://www.ibrokers.ir/api/announcements"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


# =========================================================
# دریافت اطلاعات از iBROKERS
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
            print(json.dumps(data, ensure_ascii=False, indent=2))
            return []

        records = data.get("data", [])

        print("TOTAL:",
              data.get("pagination", {}).get("total"))

        print("RECORDS:", len(records))

        # =====================================================
        # نمایش ساختار واقعی رکورد
        # =====================================================

        if records:

            print("\n" + "=" * 70)
            print("FIRST RECORD - REAL API STRUCTURE")
            print("=" * 70)

            print(
                json.dumps(
                    records[0],
                    ensure_ascii=False,
                    indent=2
                )
            )

            print("=" * 70)

        return records

    except Exception as e:

        print("=" * 70)
        print("API ERROR")
        print("=" * 70)

        print(repr(e))

        return []


# =========================================================
# تشخیص محصول فولادی
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
]


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
# پیدا کردن مقدار از بین کلیدهای احتمالی
# =========================================================

def get_value(item, keys):

    for key in keys:

        if key in item:

            value = item.get(key)

            if value not in [None, "", "null"]:

                return value

    return None


# =========================================================
# ساخت پیام
# =========================================================

def make_message(item):

    product = get_value(
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

    date = get_value(
        item,
        [
            "date",
            "offer_date",
            "announcement_date",
            "offerDate",
            "announcementDate",
            "delivery_date",
            "deliveryDate",
        ]
    )

    offer_code = get_value(
        item,
        [
            "offer_code",
            "offerCode",
            "code",
            "offer_id",
            "offerId",
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

    if base_price is None:
        base_price = "نامشخص"

    message = f"""
🏭 عرضه جدید بورس کالا

📦 محصول: {product}

📅 تاریخ عرضه: {date}

🔢 کد عرضه: {offer_code}

🏛 تالار: {hall}

🏭 عرضه‌کننده: {producer}

📊 حجم عرضه: {volume}

💰 قیمت پایه: {base_price}

━━━━━━━━━━━━━━
🏭 آروند آرون استیل
"""

    return message.strip()


# =========================================================
# ارسال پیام به تلگرام
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

        print("STATUS:", response.status_code)
        print(response.text[:1000])

        return response.ok

    except Exception as e:

        print("TELEGRAM ERROR:", repr(e))

        return False


# =========================================================
# اجرای اصلی
# =========================================================

def main():

    records = get_announcements(100)

    if not records:

        print("\nهیچ رکوردی دریافت نشد.")
        return

    print("\n" + "=" * 70)
    print("ANNOUNCEMENTS")
    print("=" * 70)

    steel_records = []

    for index, item in enumerate(records, 1):

        date = get_value(
            item,
            [
                "date",
                "offer_date",
                "announcement_date",
                "offerDate",
                "announcementDate",
                "delivery_date",
                "deliveryDate",
            ]
        )

        product = get_value(
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

        print(
            f"{index}. "
            f"DATE={date} | "
            f"PRODUCT={product} | "
            f"HALL={hall}"
        )

        if is_steel(item):

            steel_records.append(item)

    print("\n" + "=" * 70)
    print("STEEL RECORDS:", len(steel_records))
    print("=" * 70)

    # =====================================================
    # فعلاً فقط برای تست اولین رکورد فولادی ارسال می‌شود
    # =====================================================

    if steel_records:

        print("\nارسال اولین عرضه فولادی به تلگرام...")

        message = make_message(
            steel_records[0]
        )

        print("\nMESSAGE:")
        print(message)

        send_telegram(message)

    else:

        print(
            "در 100 رکورد اول، عرضه فولادی پیدا نشد."
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()