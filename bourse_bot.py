import os
import requests
from datetime import datetime

API_URL = "https://www.ibrokers.ir/api/announcements"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

# =========================================================
# گرفتن اطلاعات بورس کالا
# =========================================================

def get_announcements(limit=100):
    try:
        r = requests.get(
            API_URL,
            params={"page": 1, "limit": limit},
            headers=HEADERS,
            timeout=30
        )

        r.raise_for_status()
        data = r.json()

        if not data.get("success"):
            print("API success=False")
            return []

        records = data.get("data", [])

        print("=" * 60)
        print("iBROKERS")
        print("STATUS:", r.status_code)
        print("TOTAL:", data.get("pagination", {}).get("total"))
        print("RECORDS:", len(records))
        print("=" * 60)

        return records

    except Exception as e:
        print("API ERROR:", e)
        return []


# =========================================================
# تشخیص محصولات فولادی
# =========================================================

STEEL_WORDS = [
    "میلگرد",
    "تیرآهن",
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
    text = str(item).lower()

    for word in STEEL_WORDS:
        if word.lower() in text:
            return True

    return False


# =========================================================
# تبدیل اطلاعات به پیام تلگرام
# =========================================================

def make_message(item):

    product = (
        item.get("product")
        or item.get("product_name")
        or item.get("commodity")
        or item.get("title")
        or "نامشخص"
    )

    date = (
        item.get("date")
        or item.get("offer_date")
        or item.get("delivery_date")
        or "نامشخص"
    )

    offer_code = (
        item.get("offer_code")
        or item.get("offerCode")
        or item.get("code")
        or "نامشخص"
    )

    hall = (
        item.get("hall")
        or item.get("market_name")
        or item.get("market")
        or "نامشخص"
    )

    producer = (
        item.get("producer")
        or item.get("supplier")
        or "نامشخص"
    )

    volume = (
        item.get("volume")
        or item.get("quantity")
        or "نامشخص"
    )

    base_price = (
        item.get("base_price")
        or item.get("basePrice")
        or "نامشخص"
    )

    message = f"""🏭 عرضه جدید بورس کالا

📦 محصول: {product}

📅 تاریخ عرضه: {date}

🔢 کد عرضه: {offer_code}

🏛 تالار: {hall}

🏭 عرضه‌کننده: {producer}

📊 حجم عرضه: {volume}

💰 قیمت پایه: {base_price}

━━━━━━━━━━━━━━
آروند آرون استیل
"""

    return message


# =========================================================
# ارسال تلگرام
# =========================================================

def send_telegram(message):

    try:
        r = requests.post(
            TELEGRAM_URL,
            json={
                "chat_id": CHANNEL_ID,
                "text": message
            },
            timeout=30
        )

        print("TELEGRAM:", r.status_code)
        print(r.text[:500])

        return r.ok

    except Exception as e:
        print("TELEGRAM ERROR:", e)
        return False


# =========================================================
# اجرای اصلی
# =========================================================

def main():

    records = get_announcements(100)

    if not records:
        print("هیچ رکوردی دریافت نشد.")
        return

    print("\nآخرین عرضه‌ها:")

    steel_records = []

    for i, item in enumerate(records, 1):

        product = (
            item.get("product")
            or item.get("product_name")
            or item.get("commodity")
            or item.get("title")
        )

        date = (
            item.get("date")
            or item.get("offer_date")
            or item.get("delivery_date")
        )

        hall = (
            item.get("hall")
            or item.get("market_name")
            or item.get("market")
        )

        print(
            f"{i}. DATE={date} | "
            f"PRODUCT={product} | "
            f"HALL={hall}"
        )

        if is_steel(str(item)):
            steel_records.append(item)

    print("\nفولادی‌ها:", len(steel_records))

    # فعلاً فقط تست؛ اولین مورد فولادی ارسال شود
    if steel_records:
        message = make_message(steel_records[0])
        send_telegram(message)
    else:
        print("عرضه فولادی در 100 رکورد اول پیدا نشد.")


if __name__ == "__main__":
    main()