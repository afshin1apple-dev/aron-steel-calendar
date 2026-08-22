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

        if not response.ok:

            print(
                "TELEGRAM ERROR:",
                response.status_code
            )

            print(
                response.text[:1000]
            )

            return False

        return True

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

    jy = (
        979
        + 33 * j_np
        + 4 * (j_day_no // 1461)
    )

    j_day_no %= 1461

    if j_day_no >= 366:

        jy += (j_day_no - 1) // 365

        j_day_no = (
            j_day_no - 1
        ) % 365

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

    now = datetime.now(
        iran_tz
    )

    return gregorian_to_jalali(
        now.year,
        now.month,
        now.day
    )


def jalali_string(y, m, d):

    return (
        f"{y:04d}/"
        f"{m:02d}/"
        f"{d:02d}"
    )


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

    text = normalize_digits(
        value
    )

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

    try:

        clean = text.replace(
            ",",
            ""
        ).replace(
            "٬",
            ""
        )

        if "." in clean:

            number = float(clean)

            if number.is_integer():

                return f"{int(number):,}"

            return (
                f"{number:,.2f}"
                .rstrip("0")
                .rstrip(".")
            )

        if clean.isdigit():

            return f"{int(clean):,}"

    except Exception:
        pass

    return clean_text(value)


# =========================================================
# GENERIC FIELD FINDER
# =========================================================

def find_value(
    record,
    possible_names
):

    if not isinstance(
        record,
        dict
    ):
        return None

    # exact
    for name in possible_names:

        if name in record:

            value = record.get(
                name
            )

            if value not in (
                None,
                ""
            ):
                return value

    # insensitive
    lowered = {
        str(k).lower(): v
        for k, v in record.items()
    }

    for name in possible_names:

        key = str(name).lower()

        if key in lowered:

            value = lowered[key]

            if value not in (
                None,
                ""
            ):
                return value

    return None


# =========================================================
# API EXTRACTION
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

        value = data.get(
            key
        )

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
        "count"
    ]:

        value = data.get(
            key
        )

        if value is not None:

            try:
                return int(value)

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
# RECORD ID
# =========================================================

def record_id(record):

    fields = [
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

    value = find_value(
        record,
        fields
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
        raw.encode("utf-8")
    ).hexdigest()[:20]


# =========================================================
# FIELD EXTRACTION
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

    return clean_text(
        find_value(
            record,
            fields
        )
    )


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

    return clean_text(
        find_value(
            record,
            fields
        )
    )


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

    return format_number(
        find_value(
            record,
            fields
        )
    )


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

    return format_number(
        find_value(
            record,
            fields
        )
    )


def get_symbol(record):

    fields = [
        "symbol",
        "ticker",
        "commodityCode",
        "commodity_code",
        "symbolCode",
        "symbol_code",
    ]

    return clean_text(
        find_value(
            record,
            fields
        )
    )


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

    return clean_text(
        find_value(
            record,
            fields
        )
    )


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

    for key, value in record.items():

        if value is None:
            continue

        if isinstance(
            value,
            (dict, list)
        ):

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

            values.append(
                str(value)
            )

    return clean_text(
        " ".join(values)
    )


def is_steel(record):

    text = record_full_text(
        record
    ).lower()

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
        "فولاد",
        "ضایعات فلزی",
        "قراضه",
    ]

    # اگر محصول فولادی مشخص دارد
    for keyword in strong_steel:

        if keyword.lower() in text:
            return True

    # سایر محصولات
    for keyword in STEEL_KEYWORDS:

        if keyword.lower() in text:
            return True

    # موارد غیر فولادی
    for keyword in EXCLUDE_KEYWORDS:

        if keyword.lower() in text:
            return False

    return False


# =========================================================
# DEBUG DATE FIELDS
# =========================================================

def print_record_fields(record):

    print()
    print("--------------------------------------------------")
    print("RECORD ID:", record_id(record))
    print("PRODUCT:", get_product(record))
    print("SUPPLIER:", get_supplier(record))
    print("--------------------------------------------------")

    for key, value in record.items():

        try:

            if isinstance(
                value,
                (dict, list)
            ):

                value_text = json.dumps(
                    value,
                    ensure_ascii=False
                )

            else:

                value_text = str(
                    value
                )

            print(
                f"{key}: {value_text[:500]}"
            )

        except Exception:

            print(
                f"{key}: <UNPRINTABLE>"
            )


# =========================================================
# API
# =========================================================

def get_latest_pages():

    print("=" * 70)
    print("iBROKERS API - DEBUG MODE")
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

    all_records = []

    # چند مدل درخواست برای فهمیدن
    # رفتار واقعی API

    tests = [

        {
            "page": 1,
            "limit": 100
        },

        {
            "page": 1,
            "limit": 100,
            "sort": "desc"
        },

        {
            "page": 1,
            "limit": 100,
            "sortBy": "id",
            "sortOrder": "desc"
        },

        {
            "page": 1,
            "limit": 100,
            "order": "desc"
        },

        {
            "page": 1,
            "pageSize": 100
        },

    ]

    for number, params in enumerate(
        tests,
        1
    ):

        print()
        print("=" * 70)
        print(
            "TEST:",
            number
        )
        print(
            "PARAMS:",
            params
        )
        print("=" * 70)

        try:

            response = session.get(
                API_URL,
                params=params,
                timeout=30
            )

            print(
                "STATUS:",
                response.status_code
            )

            print(
                "URL:",
                response.url
            )

            response.raise_for_status()

            data = response.json()

            records = extract_records(
                data
            )

            print(
                "RECORDS:",
                len(records)
            )

            total = extract_total(
                data
            )

            print(
                "TOTAL:",
                total
            )

            if records:

                # چند رکورد اول
                for record in records[:5]:

                    print()
                    print(
                        "ID:",
                        record_id(record)
                    )

                    print(
                        "PRODUCT:",
                        get_product(record)
                    )

                    print(
                        "SUPPLIER:",
                        get_supplier(record)
                    )

                    print(
                        "VOLUME:",
                        get_volume(record)
                    )

                    print(
                        "PRICE:",
                        get_price(record)
                    )

                # کل فیلدهای اولین رکورد
                print()
                print(
                    "FULL FIRST RECORD FIELDS"
                )

                print_record_fields(
                    records[0]
                )

                all_records.extend(
                    records
                )

        except Exception as e:

            print(
                "REQUEST ERROR:",
                repr(e)
            )

    # -----------------------------------------------------
    # UNIQUE
    # -----------------------------------------------------

    unique = {}

    for record in all_records:

        if not isinstance(
            record,
            dict
        ):
            continue

        unique[
            record_id(record)
        ] = record

    result = list(
        unique.values()
    )

    print()
    print("=" * 70)
    print(
        "TOTAL UNIQUE RECORDS:",
        len(result)
    )
    print("=" * 70)

    return result


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

    delivery = get_delivery_date(
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

    jy, jm, jd = today_jalali()

    today = jalali_string(
        jy,
        jm,
        jd
    )

    print(
        "TODAY:",
        today
    )

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    # -----------------------------------------------------
    # API
    # -----------------------------------------------------

    records = get_latest_pages()

    print()
    print("=" * 70)
    print(
        "TOTAL DOWNLOADED:",
        len(records)
    )
    print("=" * 70)

    if not records:

        print(
            "NO RECORDS"
        )

        return

    # -----------------------------------------------------
    # UNIQUE
    # -----------------------------------------------------

    unique = {}

    for record in records:

        if isinstance(
            record,
            dict
        ):

            unique[
                record_id(record)
            ] = record

    records = list(
        unique.values()
    )

    # -----------------------------------------------------
    # STEEL
    # -----------------------------------------------------

    steel_records = []

    for record in records:

        if is_steel(
            record
        ):

            steel_records.append(
                record
            )

    print()
    print("=" * 70)
    print(
        "STEEL RECORDS:",
        len(steel_records)
    )
    print("=" * 70)

    # -----------------------------------------------------
    # نمایش فولادها
    # -----------------------------------------------------

    for record in steel_records[:20]:

        print()
        print(
            "STEEL:",
            record_id(record)
        )

        print(
            "PRODUCT:",
            get_product(record)
        )

        print(
            "SUPPLIER:",
            get_supplier(record)
        )

        print(
            "PRICE:",
            get_price(record)
        )

    # -----------------------------------------------------
    # فقط مواردی که قبلاً ارسال نشده‌اند
    # -----------------------------------------------------

    candidates = []

    for record in steel_records:

        rid = record_id(
            record
        )

        if rid in history:
            continue

        candidates.append(
            record
        )

    print()
    print("=" * 70)
    print(
        "ALREADY SENT:",
        len(steel_records) -
        len(candidates)
    )

    print(
        "NEW STEEL CANDIDATES:",
        len(candidates)
    )
    print("=" * 70)

    # -----------------------------------------------------
    # ارسال
    # -----------------------------------------------------

    sent_count = 0

    for record in candidates:

        if sent_count >= MAX_POSTS_PER_RUN:

            print(
                "MAX POSTS REACHED:",
                MAX_POSTS_PER_RUN
            )

            break

        rid = record_id(
            record
        )

        product = get_product(
            record
        )

        supplier = get_supplier(
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
            "SUPPLIER:",
            supplier
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
    # SAVE
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