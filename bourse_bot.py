import os
import json
import re
import math
import requests
from datetime import datetime, timedelta, timezone


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

API_URL = "https://www.ibrokers.ir/api/announcements"

HISTORY_FILE = "sent_history.json"

# چند صفحه آخر API بررسی شود
# چون API از قدیمی به جدید مرتب شده است.
LAST_PAGES_TO_CHECK = 10

# حداکثر تعداد پست در هر اجرای ربات
MAX_POSTS_PER_RUN = 10

# اگر بخواهیم فقط فولاد را بگیریم
STEEL_KEYWORDS = [
    "فولاد",
    "آهن",
    "میلگرد",
    "تیرآهن",
    "نبشی",
    "ناودانی",
    "ورق",
    "اسلب",
    "بلوم",
    "بیلت",
    "شمش",
    "گندله",
    "کنسانتره",
    "آهن اسفنجی",
    "DRI",
    "HRC",
    "CRC",
    "تختال",
    "کویل",
    "رول",
    "لوله",
    "پروفیل",
    "ضایعات",
    "قراضه",
    "سنگ آهن",
]

# مواردی که نباید به عنوان عرضه فولادی منتشر شوند
EXCLUDE_KEYWORDS = [
    "زعفران",
    "پسته",
    "برنج",
    "گندم",
    "جو",
    "ذرت",
    "شکر",
    "روغن",
    "نفت",
    "قیر",
    "خودرو",
    "مس",
    "آلومینیوم",
    "روی",
    "سرب",
    "طلا",
    "نقره",
]


# =========================================================
# TELEGRAM
# =========================================================

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def send_telegram(text):
    url = f"{TELEGRAM_URL}/sendMessage"

    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=30
    )

    if not response.ok:
        print("TELEGRAM ERROR:", response.status_code)
        print(response.text[:1000])
        return False

    return True


# =========================================================
# JALALI DATE
# =========================================================

def gregorian_to_jalali(gy, gm, gd):
    """
    تبدیل میلادی به شمسی
    بدون نیاز به pytz یا کتابخانه خارجی
    """

    g_days_in_month = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    j_days_in_month = [
        31, 31, 31, 31, 31, 31,
        30, 30, 30, 30, 30, 29
    ]

    gy2 = gy - 1600
    gm2 = gm - 1
    gd2 = gd - 1

    g_day_no = (
        365 * gy2
        + (gy2 + 3) // 4
        - (gy2 + 99) // 100
        + (gy2 + 399) // 400
    )

    for i in range(gm2):
        g_day_no += g_days_in_month[i]

    if gm2 > 1 and (
        gy % 4 == 0 and
        (gy % 100 != 0 or gy % 400 == 0)
    ):
        g_day_no += 1

    g_day_no += gd2

    j_day_no = g_day_no - 79

    j_np = j_day_no // 12053
    j_day_no %= 12053

    jy = 979 + 33 * j_np + 4 * (j_day_no // 1461)

    j_day_no %= 1461

    if j_day_no >= 366:
        jy += (j_day_no - 1) // 365
        j_day_no = (j_day_no - 1) % 365

    for i in range(11):
        if j_day_no < j_days_in_month[i]:
            break
        j_day_no -= j_days_in_month[i]

    jm = i + 1
    jd = j_day_no + 1

    return jy, jm, jd


def today_jalali():
    """
    ساعت ایران = UTC+3:30
    """

    iran_tz = timezone(timedelta(hours=3, minutes=30))

    now = datetime.now(iran_tz)

    jy, jm, jd = gregorian_to_jalali(
        now.year,
        now.month,
        now.day
    )

    return jy, jm, jd


def jalali_string(y, m, d):
    return f"{y:04d}/{m:02d}/{d:02d}"


# =========================================================
# NUMBER / TEXT HELPERS
# =========================================================

def normalize_digits(value):
    if value is None:
        return ""

    text = str(value)

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789"
    )

    return text.translate(table)


def clean_text(value):
    if value is None:
        return ""

    text = normalize_digits(value)

    text = re.sub(r"<[^>]+>", " ", text)

    text = text.replace("\\n", "\n")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def format_number(value):
    if value is None:
        return "-"

    text = normalize_digits(value).strip()

    if not text:
        return "-"

    # اعداد اعشاری
    try:
        if "." in text:
            number = float(text)

            if number.is_integer():
                return f"{int(number):,}"

            return f"{number:,.2f}".rstrip("0").rstrip(".")

        if text.replace(",", "").isdigit():
            return f"{int(text.replace(',', '')):,}"

    except Exception:
        pass

    return clean_text(value)


# =========================================================
# GENERIC FIELD FINDER
# =========================================================

def find_value(record, possible_names):
    """
    پیدا کردن مقدار از بین نام‌های مختلف فیلد.
    چون API ممکن است نام فیلدها را تغییر دهد.
    """

    if not isinstance(record, dict):
        return None

    # حالت عادی
    for name in possible_names:
        if name in record:
            value = record.get(name)

            if value not in (None, ""):
                return value

    # حالت insensitive
    lowered = {
        str(k).lower(): v
        for k, v in record.items()
    }

    for name in possible_names:
        key = str(name).lower()

        if key in lowered:
            value = lowered[key]

            if value not in (None, ""):
                return value

    return None


# =========================================================
# API DATA EXTRACTION
# =========================================================

def extract_records(data):
    """
    ساختار پاسخ API را به لیست رکورد تبدیل می‌کند.
    """

    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    possible_keys = [
        "data",
        "items",
        "records",
        "results",
        "announcements",
        "rows",
        "content",
    ]

    for key in possible_keys:
        value = data.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            nested = extract_records(value)

            if nested:
                return nested

    # بعضی APIها داده را داخل result می‌گذارند
    result = data.get("result")

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        return extract_records(result)

    return []


def extract_total(data):
    if not isinstance(data, dict):
        return None

    possible = [
        "total",
        "totalCount",
        "total_count",
        "count",
    ]

    for key in possible:
        value = data.get(key)

        if value is not None:
            try:
                return int(value)
            except Exception:
                pass

    # nested
    for key in ["data", "result"]:
        value = data.get(key)

        if isinstance(value, dict):
            result = extract_total(value)

            if result:
                return result

    return None


# =========================================================
# DATE EXTRACTION
# =========================================================

DATE_FIELDS = [
    "date",
    "announcementDate",
    "announcement_date",
    "publishDate",
    "publish_date",
    "releaseDate",
    "release_date",
    "offerDate",
    "offer_date",
    "tradeDate",
    "trade_date",
    "deliveryDate",
    "delivery_date",
    "startDate",
    "start_date",
    "createdAt",
    "created_at",
]


def extract_date_strings(record):
    result = []

    if not isinstance(record, dict):
        return result

    for field in DATE_FIELDS:
        value = find_value(record, [field])

        if value is None:
            continue

        text = normalize_digits(str(value))

        if text:
            result.append(text)

    # اگر API تاریخ را در هر فیلد دیگری هم گذاشته باشد
    for key, value in record.items():

        key_text = str(key).lower()

        if any(
            word in key_text
            for word in [
                "date",
                "tarikh",
                "تاریخ"
            ]
        ):
            text = normalize_digits(str(value))

            if text and text not in result:
                result.append(text)

    return result


def parse_jalali_date(text):
    """
    از متن، تاریخ شمسی مثل:
    1405/05/31
    1405-05-31
    1405/5/31
    را پیدا می‌کند.
    """

    if not text:
        return None

    text = normalize_digits(str(text))

    match = re.search(
        r"(14\d{2})[/-](\d{1,2})[/-](\d{1,2})",
        text
    )

    if not match:
        return None

    y = int(match.group(1))
    m = int(match.group(2))
    d = int(match.group(3))

    return y, m, d


def date_number(date_tuple):
    if not date_tuple:
        return 0

    y, m, d = date_tuple

    return y * 10000 + m * 100 + d


def record_date_number(record):
    dates = extract_date_strings(record)

    candidates = []

    for text in dates:
        parsed = parse_jalali_date(text)

        if parsed:
            candidates.append(date_number(parsed))

    if not candidates:
        return None

    # جدیدترین تاریخ داخل رکورد
    return max(candidates)


# =========================================================
# STEEL FILTER
# =========================================================

def record_full_text(record):
    if not isinstance(record, dict):
        return ""

    values = []

    for key, value in record.items():

        if value is None:
            continue

        if isinstance(value, (dict, list)):
            try:
                values.append(
                    json.dumps(
                        value,
                        ensure_ascii=False
                    )
                )
            except Exception:
                pass
        else:
            values.append(str(value))

    return clean_text(" ".join(values))


def is_steel(record):
    text = record_full_text(record).lower()

    # ابتدا موارد کاملاً غیرمرتبط حذف شوند
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in text:
            # اگر همزمان عبارت فولادی قوی وجود داشت،
            # اجازه بدهیم بررسی ادامه پیدا کند.
            strong_steel = [
                "میلگرد",
                "تیرآهن",
                "شمش",
                "اسلب",
                "بیلت",
                "بلوم",
                "گندله",
                "کنسانتره",
                "آهن اسفنجی",
                "فولاد"
            ]

            if not any(k.lower() in text for k in strong_steel):
                return False

    for keyword in STEEL_KEYWORDS:
        if keyword.lower() in text:
            return True

    return False


# =========================================================
# RECORD ID
# =========================================================

def record_id(record):
    possible = [
        "id",
        "ID",
        "announcementId",
        "announcement_id",
        "offerId",
        "offer_id",
        "code",
        "announcementCode",
        "announcement_code",
    ]

    value = find_value(record, possible)

    if value is not None:
        return str(value)

    # fallback
    raw = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True
    )

    import hashlib

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:20]


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
            return set(str(x) for x in data)

    except Exception as e:
        print("HISTORY LOAD ERROR:", e)

    return set()


def save_history(history):
    # تاریخچه را محدود می‌کنیم تا فایل بی‌نهایت بزرگ نشود
    items = list(history)

    if len(items) > 5000:
        items = items[-5000:]

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            items,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# API
# =========================================================

def get_latest_pages():

    print("=" * 70)
    print("iBROKERS API")
    print("=" * 70)

    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        ),
        "Accept": "application/json",
    })

    # -----------------------------------------------------
    # اول فقط یک درخواست برای فهمیدن TOTAL
    # -----------------------------------------------------

    try:

        response = session.get(
            API_URL,
            params={
                "page": 1,
                "limit": 100
            },
            timeout=30
        )

        print(
            "API PAGE 1 STATUS:",
            response.status_code
        )

        response.raise_for_status()

        first_data = response.json()

    except Exception as e:

        print("API ERROR:", e)

        return []

    first_records = extract_records(first_data)

    total = extract_total(first_data)

    if not total:
        # اگر total موجود نبود، حداقل از تعداد رکوردها استفاده کن
        total = len(first_records)

    print("TOTAL:", total)

    if total <= 0:
        return []

    total_pages = math.ceil(total / 100)

    print("TOTAL PAGES:", total_pages)

    # -----------------------------------------------------
    # فقط آخرین صفحات
    # -----------------------------------------------------

    start_page = max(
        1,
        total_pages - LAST_PAGES_TO_CHECK + 1
    )

    pages = range(
        total_pages,
        start_page - 1,
        -1
    )

    all_records = []

    for page in pages:

        if page == 1:
            records = first_records

        else:

            try:

                response = session.get(
                    API_URL,
                    params={
                        "page": page,
                        "limit": 100
                    },
                    timeout=30
                )

                print(
                    f"API PAGE {page} STATUS:",
                    response.status_code
                )

                response.raise_for_status()

                data = response.json()

                records = extract_records(data)

            except Exception as e:

                print(
                    f"PAGE {page} ERROR:",
                    e
                )

                continue

        print(
            f"PAGE {page}:",
            len(records),
            "records"
        )

        all_records.extend(records)

    return all_records


# =========================================================
# ANNOUNCEMENT FIELDS
# =========================================================

def get_product(record):

    fields = [
        "product",
        "productName",
        "product_name",
        "commodity",
        "commodityName",
        "commodity_name",
        "goods",
        "goodsName",
        "goods_name",
        "title",
        "name",
        "itemName",
        "item_name",
    ]

    value = find_value(
        record,
        fields
    )

    return clean_text(value)


def get_supplier(record):

    fields = [
        "seller",
        "sellerName",
        "seller_name",
        "supplier",
        "supplierName",
        "supplier_name",
        "producer",
        "producerName",
        "producer_name",
        "company",
        "companyName",
        "company_name",
        "offerer",
        "offererName",
    ]

    value = find_value(
        record,
        fields
    )

    return clean_text(value)


def get_volume(record):

    fields = [
        "volume",
        "quantity",
        "amount",
        "offerVolume",
        "offer_volume",
        "volumeTons",
        "volume_tons",
        "quantityTons",
        "quantity_tons",
        "amountTons",
        "amount_tons",
    ]

    value = find_value(
        record,
        fields
    )

    return format_number(value)


def get_price(record):

    fields = [
        "price",
        "basePrice",
        "base_price",
        "priceBase",
        "price_base",
        "basePriceRial",
        "base_price_rial",
        "offerPrice",
        "offer_price",
    ]

    value = find_value(
        record,
        fields
    )

    return format_number(value)


def get_symbol(record):

    fields = [
        "symbol",
        "ticker",
        "code",
        "commodityCode",
        "commodity_code",
        "symbolCode",
        "symbol_code",
    ]

    value = find_value(
        record,
        fields
    )

    return clean_text(value)


def get_delivery_date(record):

    fields = [
        "deliveryDate",
        "delivery_date",
        "delivery",
        "settlementDate",
        "settlement_date",
        "offerDate",
        "offer_date",
    ]

    value = find_value(
        record,
        fields
    )

    return clean_text(value)


# =========================================================
# MESSAGE
# =========================================================

def build_message(record, today):

    product = get_product(record)
    supplier = get_supplier(record)
    volume = get_volume(record)
    price = get_price(record)
    symbol = get_symbol(record)
    delivery = get_delivery_date(record)

    rid = record_id(record)

    message = []

    message.append("🏭 <b>عرضه جدید بورس کالا</b>")
    message.append("")
    
    if product:
        message.append(
            f"📦 <b>کالا:</b> {product}"
        )

    if symbol:
        message.append(
            f"🔖 <b>نماد:</b> {symbol}"
        )

    if supplier:
        message.append(
            f"🏢 <b>عرضه‌کننده:</b> {supplier}"
        )

    if volume != "-":
        message.append(
            f"⚖️ <b>حجم عرضه:</b> {volume}"
        )

    if price != "-":
        message.append(
            f"💰 <b>قیمت پایه:</b> {price}"
        )

    if delivery:
        message.append(
            f"📅 <b>تاریخ عرضه/تحویل:</b> {delivery}"
        )

    message.append("")
    message.append(
        f"📆 <b>تاریخ بررسی:</b> {today}"
    )

    message.append("")
    message.append(
        "━━━━━━━━━━━━━━"
    )

    message.append(
        "🏭 آروند آرون استیل"
    )

    message.append(
        "👤 مدیریت: افشین آورزمانی"
    )

    message.append(
        "📞 021-22122239"
    )

    message.append(
        "🆔 @arvand_aron_steel"
    )

    message.append("")
    message.append(
        f"🆔 <code>{rid}</code>"
    )

    return "\n".join(message)


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print("BOURSE BOT START")
    print("=" * 70)

    jy, jm, jd = today_jalali()

    today = jalali_string(
        jy,
        jm,
        jd
    )

    today_num = jy * 10000 + jm * 100 + jd

    print("TODAY:", today)
    print("TODAY NUMBER:", today_num)

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    # -----------------------------------------------------
    # دریافت آخرین صفحات
    # -----------------------------------------------------

    records = get_latest_pages()

    print()
    print("=" * 70)
    print(
        "LATEST RECORDS DOWNLOADED:",
        len(records)
    )
    print("=" * 70)

    if not records:

        print(
            "هیچ رکوردی از API دریافت نشد."
        )

        return

    # -----------------------------------------------------
    # حذف رکوردهای تکراری
    # -----------------------------------------------------

    unique = {}

    for record in records:

        if not isinstance(record, dict):
            continue

        rid = record_id(record)

        unique[rid] = record

    records = list(unique.values())

    print(
        "UNIQUE RECORDS:",
        len(records)
    )

    # -----------------------------------------------------
    # فیلتر تاریخ
    # -----------------------------------------------------

    candidates = []

    date_found = 0

    for record in records:

        rid = record_id(record)

        record_date = record_date_number(
            record
        )

        if record_date is None:
            continue

        date_found += 1

        # فقط امروز و آینده
        if record_date < today_num:
            continue

        # فولادی
        if not is_steel(record):
            continue

        # قبلاً ارسال شده
        if rid in history:
            continue

        candidates.append(
            (
                record_date,
                rid,
                record
            )
        )

    # جدیدترین‌ها اول
    candidates.sort(
        key=lambda x: (
            x[0],
            x[1]
        )
    )

    print()
    print("=" * 70)
    print(
        "DATE FIELDS FOUND:",
        date_found
    )

    print(
        "NEW STEEL CANDIDATES:",
        len(candidates)
    )
    print("=" * 70)

    # -----------------------------------------------------
    # اگر چیزی نیست
    # -----------------------------------------------------

    if not candidates:

        print(
            "هیچ عرضه فولادی جدیدی برای ارسال وجود ندارد."
        )

        # تاریخچه را هم ذخیره کن
        save_history(history)

        return

    # -----------------------------------------------------
    # ارسال
    # -----------------------------------------------------

    sent_count = 0

    for record_date, rid, record in candidates:

        if sent_count >= MAX_POSTS_PER_RUN:
            print(
                "MAX POSTS PER RUN REACHED:",
                MAX_POSTS_PER_RUN
            )
            break

        product = get_product(record)

        print(
            "SENDING:",
            rid,
            "|",
            product,
            "|",
            record_date
        )

        message = build_message(
            record,
            today
        )

        success = send_telegram(
            message
        )

        if success:

            print(
                "SENT OK:",
                rid
            )

            history.add(rid)

            sent_count += 1

        else:

            print(
                "SEND FAILED:",
                rid
            )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_history(history)

    print()
    print("=" * 70)
    print(
        "SENT THIS RUN:",
        sent_count
    )

    print(
        "HISTORY TOTAL:",
        len(history)
    )

    print("=" * 70)
    print("BOURSE BOT FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()