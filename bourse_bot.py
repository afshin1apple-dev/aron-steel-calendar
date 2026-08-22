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

MAX_POSTS_PER_RUN = 1

# فقط عرضه‌هایی که تاریخشان از این بازه عقب‌تر نباشد
# جلوگیری قطعی از ورود رکوردهای 1401 و قدیمی
MIN_VALID_JALALI_YEAR = 1404


# =========================================================
# STEEL KEYWORDS
# =========================================================

STEEL_KEYWORDS = [
    "فولاد",
    "میلگرد",
    "میل گرد",
    "تیرآهن",
    "تیر آهن",
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
    "آهن اسفنجی بریکت",
    "بریکت",
    "تختال",
    "کویل",
    "رول",
    "لوله",
    "پروفیل",
    "ضایعات فلزی",
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

    try:

        response = requests.post(
            f"{TELEGRAM_URL}/sendMessage",
            json={
                "chat_id": CHANNEL_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )

        print("TELEGRAM STATUS:", response.status_code)

        if not response.ok:
            print(response.text[:1000])
            return False

        return True

    except Exception as e:

        print("TELEGRAM ERROR:", e)
        return False


# =========================================================
# JALALI
# =========================================================

def gregorian_to_jalali(gy, gm, gd):

    g_days = [
        31, 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31
    ]

    j_days = [
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
        g_day_no += g_days[i]

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

        if j_day_no < j_days[i]:
            break

        j_day_no -= j_days[i]

    jm = i + 1
    jd = j_day_no + 1

    return jy, jm, jd


def today_jalali():

    iran = timezone(
        timedelta(hours=3, minutes=30)
    )

    now = datetime.now(iran)

    return gregorian_to_jalali(
        now.year,
        now.month,
        now.day
    )


def jalali_number(y, m, d):

    return y * 10000 + m * 100 + d


def jalali_string(y, m, d):

    return f"{y:04d}/{m:02d}/{d:02d}"


# =========================================================
# TEXT
# =========================================================

def normalize_digits(value):

    if value is None:
        return ""

    return str(value).translate(
        str.maketrans(
            "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
            "01234567890123456789"
        )
    )


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

    text = normalize_digits(value).strip()

    if not text:
        return "-"

    text = text.replace(
        "٬",
        ""
    ).replace(
        ",",
        ""
    )

    try:

        if "." in text:

            number = float(text)

            if number.is_integer():
                return f"{int(number):,}"

            return f"{number:,.2f}".rstrip(
                "0"
            ).rstrip(".")

        if text.isdigit():
            return f"{int(text):,}"

    except Exception:
        pass

    return clean_text(value)


# =========================================================
# FIELD FINDER
# =========================================================

def find_value(record, names):

    if not isinstance(record, dict):
        return None

    for name in names:

        if name in record:

            value = record.get(name)

            if value not in (
                None,
                ""
            ):
                return value

    lowered = {
        str(k).lower(): v
        for k, v in record.items()
    }

    for name in names:

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
# RECORD ID
# =========================================================

def record_id(record):

    names = [
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
        names
    )

    if value is not None:
        return str(value)

    raw = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True
    )

    return hashlib.sha256(
        raw.encode()
    ).hexdigest()[:20]


# =========================================================
# FULL TEXT
# =========================================================

def record_full_text(record):

    values = []

    if not isinstance(record, dict):
        return ""

    for value in record.values():

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


# =========================================================
# STEEL
# =========================================================

def is_steel(record):

    text = record_full_text(
        record
    ).lower()

    strong = any(
        k.lower() in text
        for k in STEEL_KEYWORDS
    )

    if not strong:
        return False

    for keyword in EXCLUDE_KEYWORDS:

        if keyword.lower() in text:

            # محصولات فولادی قوی اولویت دارند
            if not any(
                x.lower() in text
                for x in [
                    "میلگرد",
                    "تیرآهن",
                    "شمش",
                    "اسلب",
                    "بیلت",
                    "بلوم",
                    "فولاد",
                    "آهن اسفنجی",
                    "ضایعات فلزی",
                ]
            ):
                return False

    return True


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

    "datePersian",
    "persianDate",

]


def extract_all_dates(record):

    found = []

    if not isinstance(record, dict):
        return found

    # فیلدهای شناخته‌شده
    for field in DATE_FIELDS:

        value = find_value(
            record,
            [field]
        )

        if value is not None:

            text = normalize_digits(
                value
            )

            found.append(
                text
            )

    # هر فیلدی که نامش شبیه تاریخ است
    for key, value in record.items():

        key_text = str(
            key
        ).lower()

        if any(
            word in key_text
            for word in [
                "date",
                "tarikh",
                "تاریخ"
            ]
        ):

            text = normalize_digits(
                value
            )

            if text and text not in found:
                found.append(text)

    return found


def parse_jalali(text):

    if not text:
        return None

    text = normalize_digits(
        text
    )

    match = re.search(
        r"(14\d{2})\s*[/\-.]\s*(\d{1,2})\s*[/\-.]\s*(\d{1,2})",
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

    if not (
        1 <= m <= 12
        and
        1 <= d <= 31
    ):
        return None

    return y, m, d


def extract_valid_dates(record):

    result = []

    for text in extract_all_dates(
        record
    ):

        parsed = parse_jalali(
            text
        )

        if parsed:
            result.append(
                parsed
            )

    return result


def record_date(record):

    dates = extract_valid_dates(
        record
    )

    if not dates:
        return None

    # مهم:
    # قدیمی‌ترین/جدیدترین تاریخ به‌صورت کور انتخاب نمی‌شود.
    # برای جلوگیری از 1401، ابتدا سال معتبر را جدا می‌کنیم.

    valid = [
        d for d in dates
        if d[0] >= MIN_VALID_JALALI_YEAR
    ]

    if not valid:
        return None

    return max(
        valid,
        key=lambda x:
        jalali_number(*x)
    )


# =========================================================
# PRODUCT FIELDS
# =========================================================

def get_product(record):

    return clean_text(
        find_value(
            record,
            [
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
        )
    )


def get_supplier(record):

    return clean_text(
        find_value(
            record,
            [
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
        )
    )


def get_volume(record):

    return format_number(
        find_value(
            record,
            [
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
        )
    )


def get_price(record):

    return format_number(
        find_value(
            record,
            [
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
        )
    )


def get_contract(record):

    return clean_text(
        find_value(
            record,
            [
                "contractType",
                "contract_type",
                "transactionType",
                "transaction_type",
                "type",
                "settlementType",
                "settlement_type",
            ]
        )
    )


def get_delivery_date(record):

    return clean_text(
        find_value(
            record,
            [
                "deliveryDate",
                "delivery_date",
                "delivery",
                "settlementDate",
                "settlement_date",
            ]
        )
    )


# =========================================================
# API
# =========================================================

def get_records():

    print("=" * 70)
    print("iBROKERS API")
    print("=" * 70)

    try:

        response = requests.get(
            API_URL,
            params={
                "page": 1,
                "limit": 100,
            },
            headers={
                "User-Agent":
                    "Mozilla/5.0",
                "Accept":
                    "application/json",
            },
            timeout=30,
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

    records = []

    if isinstance(
        data,
        list
    ):

        records = data

    elif isinstance(
        data,
        dict
    ):

        for key in [
            "data",
            "items",
            "records",
            "results",
            "announcements",
            "rows",
            "content",
        ]:

            value = data.get(
                key
            )

            if isinstance(
                value,
                list
            ):

                records = value
                break

    print(
        "RECORDS RECEIVED:",
        len(records)
    )

    return records


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

            data = json.load(f)

        return set(
            str(x)
            for x in data
        )

    except Exception:

        return set()


def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            list(history)[-5000:],
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# MESSAGE
# =========================================================

def build_message(
    candidates,
    today
):

    lines = []

    lines.append(
        "🏭 <b>عرضه‌های فولادی بورس کالا</b>"
    )

    lines.append(
        f"📅 <b>{today}</b>"
    )

    lines.append(
        "━━━━━━━━━━━━━━━━"
    )

    total_volume = 0
    valid_volume_count = 0

    for index, item in enumerate(
        candidates,
        1
    ):

        record = item["record"]

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

        contract = get_contract(
            record
        )

        delivery = get_delivery_date(
            record
        )

        date_tuple = item["date"]

        offer_date = jalali_string(
            *date_tuple
        )

        lines.append("")

        lines.append(
            f"🔹 <b>{index}. {product or 'محصول فولادی'}</b>"
        )

        if supplier:
            lines.append(
                f"🏢 تولیدکننده: {supplier}"
            )

        if volume != "-":
            lines.append(
                f"⚖️ حجم عرضه: <b>{volume}</b> تن"
            )

            try:
                total_volume += int(
                    volume.replace(",", "")
                )
                valid_volume_count += 1
            except Exception:
                pass

        if price != "-":
            lines.append(
                f"💰 قیمت پایه: <b>{price}</b> ریال"
            )

        if contract:
            lines.append(
                f"💳 قرارداد: {contract}"
            )

        lines.append(
            f"📆 تاریخ عرضه: {offer_date}"
        )

        if delivery:
            lines.append(
                f"🚚 تاریخ تحویل: {delivery}"
            )

        lines.append(
            "──────────────"
        )

    lines.append("")

    lines.append(
        "📊 <b>خلاصه عرضه</b>"
    )

    lines.append(
        f"🔸 تعداد عرضه: <b>{len(candidates)}</b>"
    )

    if valid_volume_count:
        lines.append(
            f"🔸 مجموع حجم: <b>{total_volume:,}</b> تن"
        )

    lines.append("")

    lines.append(
        "━━━━━━━━━━━━━━━━"
    )

    lines.append(
        "🏭 <b>آروند آرون استیل</b>"
    )

    lines.append(
        "👤 مدیریت: افشین آورزمانی"
    )

    lines.append(
        "📞 021-22122239"
    )

    lines.append(
        "🆔 @arvand_aron_steel"
    )

    return "\n".join(
        lines
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

    history = load_history()

    print(
        "SENT HISTORY:",
        len(history)
    )

    records = get_records()

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

        if not isinstance(
            record,
            dict
        ):
            continue

        unique[
            record_id(record)
        ] = record

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

    candidates = []

    steel_count = 0
    old_count = 0
    no_date_count = 0
    sent_count = 0

    print()
    print("=" * 70)
    print(
        "ANALYZING RECORDS"
    )
    print("=" * 70)

    for record in records:

        rid = record_id(
            record
        )

        product = get_product(
            record
        )

        # فولاد؟
        if not is_steel(
            record
        ):
            continue

        steel_count += 1

        # تاریخ معتبر؟
        d = record_date(
            record
        )

        if d is None:

            no_date_count += 1

            print(
                "SKIP NO VALID DATE:",
                rid,
                "|",
                product
            )

            continue

        d_num = jalali_number(
            *d
        )

        # تاریخ قدیمی
        if d_num < today_num:

            old_count += 1

            print(
                "SKIP OLD:",
                rid,
                "|",
                product,
                "|",
                jalali_string(*d)
            )

            continue

        # قبلاً ارسال شده؟
        if rid in history:

            sent_count += 1

            continue

        candidates.append({
            "id": rid,
            "record": record,
            "date": d,
        })

    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    candidates.sort(
        key=lambda x: (
            jalali_number(
                *x["date"]
            ),
            x["id"]
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
        steel_count - no_date_count
    )

    print(
        "OLD RECORDS BLOCKED:",
        old_count
    )

    print(
        "ALREADY SENT:",
        sent_count
    )

    print(
        "NEW STEEL CANDIDATES:",
        len(candidates)
    )

    print("=" * 70)

    # -----------------------------------------------------
    # NO DATA
    # -----------------------------------------------------

    if not candidates:

        print(
            "هیچ عرضه فولادی معتبر و جدیدی پیدا نشد."
        )

        save_history(
            history
        )

        return

    # -----------------------------------------------------
    # SEND ONE AGGREGATED POST
    # -----------------------------------------------------

    selected = candidates[
        :MAX_POSTS_PER_RUN
    ]

    message = build_message(
        selected,
        today
    )

    print()
    print(
        "SENDING AGGREGATED POST..."
    )

    success = send_telegram(
        message
    )

    if success:

        for item in selected:

            history.add(
                item["id"]
            )

        save_history(
            history
        )

        print(
            "POST SENT SUCCESSFULLY"
        )

    else:

        print(
            "POST FAILED - HISTORY NOT UPDATED"
        )

    print()
    print("=" * 70)
    print("BOURSE BOT FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()