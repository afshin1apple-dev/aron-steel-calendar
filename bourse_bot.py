import os
import json
import re
import hashlib
import requests
from datetime import datetime, timedelta, timezone


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

API_URL = "https://www.ibrokers.ir/api/announcements"

HISTORY_FILE = "sent_history.json"

MAX_POSTS_PER_RUN = 10

# فقط عرضه‌هایی که تاریخشان امروز یا آینده است
ALLOW_TODAY_AND_FUTURE_ONLY = True


# =========================================================
# STEEL KEYWORDS
# =========================================================

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
    "dri",
    "hrc",
    "crc",
    "تختال",
    "کویل",
    "رول",
    "لوله",
    "پروفیل",
    "ضایعات",
    "قراضه",
    "سنگ آهن",
]


# مواردی که به‌تنهایی نباید فولادی حساب شوند
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

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        if response.ok:
            return True

        print(
            "TELEGRAM ERROR:",
            response.status_code,
            response.text[:500]
        )

        return False

    except Exception as e:

        print(
            "TELEGRAM EXCEPTION:",
            e
        )

        return False


# =========================================================
# JALALI DATE
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

    iran_tz = timezone(
        timedelta(
            hours=3,
            minutes=30
        )
    )

    now = datetime.now(iran_tz)

    return gregorian_to_jalali(
        now.year,
        now.month,
        now.day
    )


def jalali_string(y, m, d):

    return f"{y:04d}/{m:02d}/{d:02d}"


def jalali_number(y, m, d):

    return y * 10000 + m * 100 + d


# =========================================================
# TEXT HELPERS
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

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = text.replace(
        "\\n",
        "\n"
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def format_number(value):

    if value is None:
        return "-"

    text = normalize_digits(
        value
    ).strip()

    if not text:
        return "-"

    # اعداد فارسی با جداکننده
    text = text.replace(
        "٬",
        ""
    )

    text = text.replace(
        ",",
        ""
    )

    try:

        if "." in text:

            number = float(text)

            if number.is_integer():
                return f"{int(number):,}"

            return (
                f"{number:,.2f}"
                .rstrip("0")
                .rstrip(".")
            )

        if text.isdigit():

            return f"{int(text):,}"

    except Exception:
        pass

    return clean_text(
        value
    )


# =========================================================
# FIELD FINDER
# =========================================================

def find_value(
    record,
    names
):

    if not isinstance(
        record,
        dict
    ):
        return None

    # مستقیم
    for name in names:

        if name in record:

            value = record.get(name)

            if value not in (
                None,
                ""
            ):
                return value

    # بدون حساسیت به حروف
    lowered = {
        str(k).lower(): v
        for k, v in record.items()
    }

    for name in names:

        key = str(
            name
        ).lower()

        if key in lowered:

            value = lowered[key]

            if value not in (
                None,
                ""
            ):
                return value

    return None


# =========================================================
# API RESPONSE
# =========================================================

def extract_records(data):

    if isinstance(
        data,
        list
    ):
        return data

    if not isinstance(
        data,
        dict
    ):
        return []

    for key in [
        "data",
        "items",
        "records",
        "results",
        "announcements",
        "rows",
        "content",
    ]:

        value = data.get(key)

        if isinstance(
            value,
            list
        ):
            return value

        if isinstance(
            value,
            dict
        ):

            nested = extract_records(
                value
            )

            if nested:
                return nested

    result = data.get(
        "result"
    )

    if isinstance(
        result,
        list
    ):
        return result

    if isinstance(
        result,
        dict
    ):
        return extract_records(
            result
        )

    return []


def extract_total(data):

    if not isinstance(
        data,
        dict
    ):
        return None

    for key in [
        "total",
        "totalCount",
        "total_count",
        "count",
    ]:

        value = data.get(
            key
        )

        if value is not None:

            try:
                return int(
                    value
                )

            except Exception:
                pass

    for key in [
        "data",
        "result"
    ]:

        value = data.get(
            key
        )

        if isinstance(
            value,
            dict
        ):

            result = extract_total(
                value
            )

            if result is not None:
                return result

    return None


# =========================================================
# DATE PARSER
# =========================================================

def parse_jalali_date(value):

    if value is None:
        return None

    text = normalize_digits(
        str(value)
    )

    # 1405/05/31
    # 1405-05-31
    # 14050531

    match = re.search(
        r"(14\d{2})[/-]?(\d{1,2})[/-]?(\d{1,2})",
        text
    )

    if not match:
        return None

    y = int(
        match.group(1)
    )

    m = int(
        match.group(2)
    )

    d = int(
        match.group(3)
    )

    # اعتبارسنجی ساده
    if not (
        1 <= m <= 12
        and
        1 <= d <= 31
    ):
        return None

    return y, m, d


def date_to_number(value):

    parsed = parse_jalali_date(
        value
    )

    if not parsed:
        return None

    y, m, d = parsed

    return jalali_number(
        y,
        m,
        d
    )


# =========================================================
# IMPORTANT:
# تاریخ واقعی عرضه را از فیلدهای واقعی API می‌خوانیم
# =========================================================

def get_offer_date(record):

    value = find_value(
        record,
        [
            "offerDate",
            "offer_date",
            "offerDateRaw",
            "offer_date_raw",
        ]
    )

    return parse_jalali_date(
        value
    )


def get_delivery_date(record):

    value = find_value(
        record,
        [
            "delivery_date",
            "deliveryDate",
        ]
    )

    return parse_jalali_date(
        value
    )


def get_relevant_date(record):

    """
    برای تشخیص جدید بودن عرضه:
    تاریخ عرضه مهم‌تر از delivery_date است.
    """

    offer = get_offer_date(
        record
    )

    if offer:
        return offer

    delivery = get_delivery_date(
        record
    )

    if delivery:
        return delivery

    return None


# =========================================================
# STEEL FILTER
# =========================================================

def record_full_text(record):

    if not isinstance(
        record,
        dict
    ):
        return ""

    values = []

    # فیلدهای مهم را عمداً اضافه می‌کنیم
    important_fields = [
        "productName",
        "product",
        "commodity",
        "symbol",
        "supplier",
        "supplierName",
        "producer",
        "producerName",
        "hall",
        "description",
    ]

    for field in important_fields:

        value = record.get(
            field
        )

        if value not in (
            None,
            ""
        ):

            values.append(
                str(value)
            )

    return clean_text(
        " ".join(values)
    ).lower()


def is_steel(record):

    text = record_full_text(
        record
    )

    if not text:
        return False

    # موارد غیر فولادی
    for keyword in EXCLUDE_KEYWORDS:

        if keyword.lower() in text:

            strong = [
                "میلگرد",
                "تیرآهن",
                "شمش",
                "اسلب",
                "بیلت",
                "بلوم",
                "گندله",
                "کنسانتره",
                "آهن اسفنجی",
                "فولاد",
            ]

            if not any(
                x.lower() in text
                for x in strong
            ):
                return False

    for keyword in STEEL_KEYWORDS:

        if keyword.lower() in text:
            return True

    return False


# =========================================================
# RECORD ID
# =========================================================

def record_id(record):

    value = find_value(
        record,
        [
            "id",
            "offerCode",
            "external_id",
            "externalId",
            "announcementId",
            "announcement_id",
        ]
    )

    if value is not None:
        return str(
            value
        )

    raw = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True
    )

    return hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()[:24]


# =========================================================
# HISTORY
# =========================================================

def load_history():

    if not os.path.exists(
        HISTORY_FILE
    ):
        return set()

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(
                f
            )

        if isinstance(
            data,
            list
        ):

            return set(
                str(x)
                for x in data
            )

    except Exception as e:

        print(
            "HISTORY LOAD ERROR:",
            e
        )

    return set()


def save_history(history):

    items = list(
        history
    )

    # محدود کردن حجم تاریخچه
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
# API DOWNLOAD
# =========================================================

def get_latest_records():

    print()
    print("=" * 70)
    print("iBROKERS API")
    print("=" * 70)

    session = requests.Session()

    session.headers.update({
        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36",

        "Accept":
            "application/json",
    })

    try:

        response = session.get(
            API_URL,
            params={
                "page": 1,
                "limit": 100,
            },
            timeout=30
        )

        print(
            "API STATUS:",
            response.status_code
        )

        response.raise_for_status()

        data = response.json()

    except Exception as e:

        print(
            "API ERROR:",
            e
        )

        return []

    records = extract_records(
        data
    )

    total = extract_total(
        data
    )

    print(
        "API TOTAL:",
        total
    )

    print(
        "RECORDS RECEIVED:",
        len(records)
    )

    return records


# =========================================================
# FIELDS
# =========================================================

def get_product(record):

    value = find_value(
        record,
        [
            "productName",
            "product_name",
            "product",
            "commodity",
            "commodityName",
            "commodity_name",
            "goods",
            "goodsName",
            "itemName",
            "title",
            "name",
        ]
    )

    return clean_text(
        value
    )


def get_supplier(record):

    value = find_value(
        record,
        [
            "supplier",
            "supplierName",
            "supplier_name",
            "seller",
            "sellerName",
            "seller_name",
            "producer",
            "producerName",
            "producer_name",
            "company",
            "companyName",
            "company_name",
        ]
    )

    return clean_text(
        value
    )


def get_volume(record):

    value = find_value(
        record,
        [
            "availableVolume",
            "availableVolumeRaw",
            "volume",
            "quantity",
            "amount",
            "offerVolume",
            "offer_volume",
            "initVolume",
            "init_volume",
        ]
    )

    return format_number(
        value
    )


def get_price(record):

    value = find_value(
        record,
        [
            "basePrice",
            "basePriceRaw",
            "base_price",
            "price",
            "offerPrice",
            "offer_price",
        ]
    )

    return format_number(
        value
    )


def get_symbol(record):

    value = find_value(
        record,
        [
            "symbol",
            "ticker",
            "offerSymbol",
            "commodityCode",
            "commodity_code",
        ]
    )

    return clean_text(
        value
    )


def get_hall(record):

    value = find_value(
        record,
        [
            "hall",
            "offerRing",
            "tradingHall",
            "trading_hall",
        ]
    )

    return clean_text(
        value
    )


# =========================================================
# MESSAGE
# =========================================================

def build_message(
    record,
    today
):

    product = get_product(
        record
    )

    supplier = get_supplier(
        record
    )

    volume = get_volume(
        record
    )

    price = get_price(
        record
    )

    symbol = get_symbol(
        record
    )

    hall = get_hall(
        record
    )

    offer_date = get_offer_date(
        record
    )

    delivery_date = get_delivery_date(
        record
    )

    rid = record_id(
        record
    )

    message = []

    message.append(
        "🏭 <b>عرضه جدید بورس کالا</b>"
    )

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

    if hall:

        message.append(
            f"🏛 <b>تالار:</b> {hall}"
        )

    if volume != "-":

        message.append(
            f"⚖️ <b>حجم عرضه:</b> {volume}"
        )

    if price != "-":

        message.append(
            f"💰 <b>قیمت پایه:</b> {price}"
        )

    if offer_date:

        message.append(
            "📅 <b>تاریخ عرضه:</b> "
            + jalali_string(
                *offer_date
            )
        )

    if delivery_date:

        message.append(
            "🚚 <b>تاریخ تحویل:</b> "
            + jalali_string(
                *delivery_date
            )
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

    return "\n".join(
        message
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print("BOURSE BOT START")
    print("=" * 70)

    # -----------------------------------------------------
    # TODAY
    # -----------------------------------------------------

    jy, jm, jd = today_jalali()

    today = jalali_string(
        jy,
        jm,
        jd
    )

    today_num = jalali_number(
        jy,
        jm,
        jd
    )

    print(
        "TODAY:",
        today
    )

    print(
        "TODAY NUMBER:",
        today_num
    )

    # -----------------------------------------------------
    # HISTORY
    # -----------------------------------------------------

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    # -----------------------------------------------------
    # API
    # -----------------------------------------------------

    records = get_latest_records()

    print()
    print("=" * 70)
    print(
        "ANALYZING RECORDS:",
        len(records)
    )
    print("=" * 70)

    if not records:

        print(
            "NO RECORDS FROM API"
        )

        return

    # -----------------------------------------------------
    # UNIQUE
    # -----------------------------------------------------

    unique = {}

    for record in records:

        if not isinstance(
            record,
            dict
        ):
            continue

        rid = record_id(
            record
        )

        unique[rid] = record

    records = list(
        unique.values()
    )

    print(
        "UNIQUE RECORDS:",
        len(records)
    )

    # -----------------------------------------------------
    # ANALYSIS
    # -----------------------------------------------------

    steel_count = 0
    valid_date_count = 0
    old_count = 0
    already_sent_count = 0

    candidates = []

    for record in records:

        rid = record_id(
            record
        )

        # فولادی؟
        if not is_steel(
            record
        ):
            continue

        steel_count += 1

        # تاریخ واقعی عرضه
        relevant_date = get_relevant_date(
            record
        )

        if not relevant_date:

            print(
                "SKIP - NO VALID OFFER/DELIVERY DATE:",
                rid,
                get_product(record)
            )

            continue

        valid_date_count += 1

        record_date_num = jalali_number(
            *relevant_date
        )

        # -------------------------------------------------
        # مهم‌ترین فیلتر
        # -------------------------------------------------

        if (
            ALLOW_TODAY_AND_FUTURE_ONLY
            and
            record_date_num < today_num
        ):

            old_count += 1

            print(
                "SKIP OLD:",
                rid,
                "|",
                get_product(record),
                "|",
                jalali_string(
                    *relevant_date
                )
            )

            continue

        # قبلاً ارسال شده؟
        if rid in history:

            already_sent_count += 1

            continue

        candidates.append(
            (
                record_date_num,
                rid,
                record
            )
        )

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    candidates.sort(
        key=lambda x: (
            x[0],
            x[1]
        )
    )

    print()
    print("=" * 70)
    print(
        "STEEL RECORDS:",
        steel_count
    )

    print(
        "VALID DATE RECORDS:",
        valid_date_count
    )

    print(
        "OLD RECORDS BLOCKED:",
        old_count
    )

    print(
        "ALREADY SENT:",
        already_sent_count
    )

    print(
        "NEW STEEL CANDIDATES:",
        len(candidates)
    )

    print("=" * 70)

    # -----------------------------------------------------
    # هیچ عرضه جدیدی نیست
    # -----------------------------------------------------

    if not candidates:

        print(
            "هیچ عرضه فولادی جدیدی برای ارسال وجود ندارد."
        )

        save_history(
            history
        )

        return

    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------

    sent_count = 0

    for (
        record_date,
        rid,
        record
    ) in candidates:

        if (
            sent_count
            >= MAX_POSTS_PER_RUN
        ):

            print(
                "MAX POSTS REACHED:",
                MAX_POSTS_PER_RUN
            )

            break

        product = get_product(
            record
        )

        print()
        print(
            "SENDING:",
            rid
        )

        print(
            "PRODUCT:",
            product
        )

        print(
            "DATE:",
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

            history.add(
                rid
            )

            sent_count += 1

        else:

            print(
                "SEND FAILED:",
                rid
            )

    # -----------------------------------------------------
    # SAVE HISTORY
    # -----------------------------------------------------

    save_history(
        history
    )

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
    print(
        "BOURSE BOT FINISHED"
    )
    print("=" * 70)


if __name__ == "__main__":

    main()