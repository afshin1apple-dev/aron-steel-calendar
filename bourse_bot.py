import os
import re
import json
import hashlib
import requests
from datetime import datetime, timedelta, timezone

try:
    import pandas as pd
except ImportError:
    pd = None


# =========================================================
# SETTINGS
# =========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

SPAD_URL = (
    "https://spadfoulad.com/"
    "%D9%BE%D9%86%D9%84-%D9%85%D8%B9%D8%A7%D9%85%D9%84%D8%A7%D8%AA-%D8%A8%D9%88%D8%B1%D8%B3-%DA%A9%D8%A7%D9%84%D8%A7/"
)

HISTORY_FILE = "sent_history.json"

TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

MAX_POSTS_PER_RUN = 3


# =========================================================
# PRODUCTS
# =========================================================

PRODUCT_GROUPS = {
    "شمش بلوم 5SP": [
        "شمش بلوم",
        "5SP",
    ],

    "شمش بلوم 3SP": [
        "شمش بلوم",
        "3SP",
    ],

    "بیلت": [
        "بیلت",
    ],

    "اسلب": [
        "اسلب",
    ],

    "میلگرد": [
        "میلگرد",
    ],

    "ورق گرم": [
        "ورق گرم",
    ],

    "ورق سرد": [
        "ورق سرد",
    ],

    "ورق گالوانیزه": [
        "ورق گالوانیزه",
    ],
}


# =========================================================
# EXCLUDE
# =========================================================

EXCLUDE_WORDS = [
    "آلومینیوم",
    "مس",
    "روی",
    "سرب",
    "طلا",
    "نقره",
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
]


# =========================================================
# TELEGRAM
# =========================================================

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
            timeout=30,
        )

        if not response.ok:

            print(
                "TELEGRAM ERROR:",
                response.status_code,
            )

            print(
                response.text[:1000]
            )

            return False

        data = response.json()

        return bool(
            data.get("ok")
        )

    except Exception as e:

        print(
            "TELEGRAM EXCEPTION:",
            e,
        )

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

    if (
        gm2 > 1
        and gy % 4 == 0
        and (
            gy % 100 != 0
            or gy % 400 == 0
        )
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

        jy += (
            j_day_no - 1
        ) // 365

        j_day_no = (
            j_day_no - 1
        ) % 365

    for i in range(11):

        if j_day_no < j_days[i]:
            break

        j_day_no -= j_days[i]

    jm = i + 1
    jd = j_day_no + 1

    return jy, jm, jd


def today_jalali():

    iran_tz = timezone(
        timedelta(hours=3, minutes=30)
    )

    now = datetime.now(
        iran_tz
    )

    return gregorian_to_jalali(
        now.year,
        now.month,
        now.day,
    )


def jalali_string():

    y, m, d = today_jalali()

    return (
        f"{y:04d}/"
        f"{m:02d}/"
        f"{d:02d}"
    )


# =========================================================
# TEXT / NUMBER
# =========================================================

def normalize_digits(value):

    if value is None:
        return ""

    text = str(value)

    table = str.maketrans(
        "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
        "01234567890123456789",
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
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def number(value):

    if value is None:
        return None

    text = normalize_digits(
        value
    )

    text = (
        text
        .replace(",", "")
        .replace("٬", "")
        .replace(" ", "")
    )

    if not text:
        return None

    try:
        return float(text)

    except Exception:
        return None


def format_number(value):

    if value is None:
        return "-"

    try:

        value = float(value)

        if value.is_integer():

            return f"{int(value):,}"

        return f"{value:,.2f}"

    except Exception:

        return str(value)


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
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if isinstance(
            data,
            list,
        ):

            return set(
                str(x)
                for x in data
            )

    except Exception as e:

        print(
            "HISTORY ERROR:",
            e,
        )

    return set()


def save_history(history):

    data = list(history)

    if len(data) > 3000:

        data = data[-3000:]

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )


# =========================================================
# DOWNLOAD SPAD
# =========================================================

def download_page():

    print()
    print("=" * 70)
    print("SPADFOLAD DATA SOURCE")
    print("=" * 70)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        ),

        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),
    }

    try:

        response = requests.get(
            SPAD_URL,
            headers=headers,
            timeout=40,
        )

        print(
            "SPAD STATUS:",
            response.status_code,
        )

        response.raise_for_status()

        print(
            "SPAD BYTES:",
            len(response.content),
        )

        return response.text

    except Exception as e:

        print(
            "SPAD ERROR:",
            e,
        )

        return None


# =========================================================
# TABLE EXTRACTION
# =========================================================

def normalize_columns(columns):

    result = []

    for col in columns:

        if isinstance(
            col,
            tuple,
        ):

            col = " ".join(
                str(x)
                for x in col
                if str(x) != "nan"
            )

        col = clean_text(
            col
        )

        result.append(
            col
        )

    return result


def find_transaction_table(html):

    if pd is None:

        print(
            "ERROR: pandas is not installed."
        )

        return None

    try:

        tables = pd.read_html(
            html
        )

    except Exception as e:

        print(
            "READ HTML ERROR:",
            e,
        )

        return None

    print(
        "TABLES FOUND:",
        len(tables),
    )

    wanted = [
        "حجم معامله",
        "قیمت پایه",
        "قیمت میانگین",
        "درصد رقابت",
    ]

    for index, table in enumerate(
        tables
    ):

        cols = normalize_columns(
            table.columns
        )

        joined = " ".join(
            cols
        )

        print(
            f"TABLE {index}:",
            joined[:300],
        )

        score = sum(
            1
            for item in wanted
            if item in joined
        )

        if score >= 3:

            print(
                "TRANSACTION TABLE:",
                index,
            )

            table.columns = cols

            return table

    return None


# =========================================================
# ROW PARSING
# =========================================================

def get_column(
    row,
    names,
):

    for name in names:

        for col in row.index:

            col_text = clean_text(
                col
            )

            if name in col_text:

                value = row[col]

                if (
                    value is not None
                    and str(value).lower()
                    != "nan"
                ):

                    return value

    return None


def parse_rows(table):

    records = []

    for _, row in table.iterrows():

        product = clean_text(
            get_column(
                row,
                [
                    "نام کالا",
                    "نام محصول",
                    "کالا",
                    "محصول",
                ],
            )
        )

        producer = clean_text(
            get_column(
                row,
                [
                    "تولیدکننده",
                    "عرضه کننده",
                    "عرضه‌کننده",
                ],
            )
        )

        volume = number(
            get_column(
                row,
                [
                    "حجم معامله",
                ],
            )
        )

        base_price = number(
            get_column(
                row,
                [
                    "قیمت پایه",
                ],
            )
        )

        base_vat = number(
            get_column(
                row,
                [
                    "قیمت پایه (با مالیات)",
                    "پایه با مالیات",
                ],
            )
        )

        avg_price = number(
            get_column(
                row,
                [
                    "قیمت میانگین",
                    "میانگین قیمت",
                ],
            )
        )

        avg_vat = number(
            get_column(
                row,
                [
                    "قیمت میانگین (با مالیات)",
                    "میانگین با مالیات",
                ],
            )
        )

        competition = number(
            get_column(
                row,
                [
                    "درصد رقابت",
                    "رقابت",
                ],
            )
        )

        if not product:

            continue

        # فقط محصولاتی که واقعاً معامله شده‌اند
        if volume is None:
            continue

        if volume <= 0:
            continue

        # قیمت واقعی معامله باید موجود باشد
        if avg_price is None:
            continue

        records.append(
            {
                "product": product,
                "producer": producer,
                "volume": volume,
                "base_price": base_price,
                "base_vat": base_vat,
                "avg_price": avg_price,
                "avg_vat": avg_vat,
                "competition": competition,
            }
        )

    return records


# =========================================================
# PRODUCT MATCH
# =========================================================

def match_group(
    product,
    group_name,
):

    product = product.lower()

    rules = PRODUCT_GROUPS[
        group_name
    ]

    for rule in rules:

        if rule.lower() not in product:

            return False

    for bad in EXCLUDE_WORDS:

        if bad.lower() in product:

            return False

    return True


# =========================================================
# WEIGHTED AVERAGE
# =========================================================

def weighted_average(
    records,
    field,
):

    numerator = 0
    denominator = 0

    for r in records:

        volume = r["volume"]
        value = r.get(field)

        if (
            volume is None
            or value is None
        ):
            continue

        numerator += (
            volume * value
        )

        denominator += volume

    if denominator <= 0:

        return None

    return (
        numerator
        / denominator
    )


def total_volume(
    records
):

    return sum(
        r["volume"]
        for r in records
        if r["volume"] is not None
    )


# =========================================================
# ANALYSIS
# =========================================================

def analyze_group(
    group_name,
    records,
):

    if not records:

        return None

    volume = total_volume(
        records
    )

    base = weighted_average(
        records,
        "base_price",
    )

    avg = weighted_average(
        records,
        "avg_price",
    )

    avg_vat = weighted_average(
        records,
        "avg_vat",
    )

    competition = weighted_average(
        records,
        "competition",
    )

    if avg is None:

        return None

    # رقابت واقعی محاسبه‌شده
    calculated_comp = None

    if (
        base is not None
        and base > 0
    ):

        calculated_comp = (
            (avg - base)
            / base
            * 100
        )

    # اگر منبع درصد رقابت داده باشد
    # همان را هم نگه می‌داریم
    source_comp = competition

    if calculated_comp is not None:

        final_comp = calculated_comp

    else:

        final_comp = source_comp

    return {
        "group": group_name,
        "records": records,
        "volume": volume,
        "base": base,
        "avg": avg,
        "avg_vat": avg_vat,
        "competition": final_comp,
        "source_competition": source_comp,
        "calculated_competition": calculated_comp,
    }


# =========================================================
# SIGNAL
# =========================================================

def market_signal(
    competition,
):

    if competition is None:

        return (
            "⚪",
            "نامشخص",
        )

    if competition >= 5:

        return (
            "🟢",
            "رقابت شدید",
        )

    if competition >= 2:

        return (
            "🟢",
            "رقابت متوسط",
        )

    if competition > 0:

        return (
            "🟡",
            "رقابت محدود",
        )

    return (
        "⚪",
        "بدون رقابت",
    )


# =========================================================
# MESSAGE
# =========================================================

def build_message(
    analysis,
    today,
):

    group = analysis["group"]

    volume = analysis["volume"]

    base = analysis["base"]

    avg = analysis["avg"]

    avg_vat = analysis["avg_vat"]

    competition = analysis[
        "competition"
    ]

    records = analysis[
        "records"
    ]

    signal_icon, signal_text = (
        market_signal(
            competition
        )
    )

    if (
        base is not None
        and avg is not None
        and base > 0
    ):

        diff = avg - base

        diff_text = (
            f"{diff:,.0f}"
        )

    else:

        diff_text = "-"

    producer_count = len(
        set(
            r["producer"]
            for r in records
            if r["producer"]
        )
    )

    message = []

    message.append(
        f"📊 <b>تحلیل معاملات {group}</b>"
    )

    message.append("")

    message.append(
        f"📦 <b>حجم معامله:</b> "
        f"{format_number(volume)} تن"
    )

    message.append(
        f"🏭 <b>تعداد تولیدکننده:</b> "
        f"{producer_count}"
    )

    message.append("")

    if base is not None:

        message.append(
            f"💰 <b>میانگین وزنی قیمت پایه:</b> "
            f"{format_number(base)} ریال"
        )

    message.append(
        f"🔨 <b>میانگین وزنی قیمت معامله:</b> "
        f"{format_number(avg)} ریال"
    )

    if avg_vat is not None:

        message.append(
            f"🧾 <b>قیمت معامله با مالیات:</b> "
            f"{format_number(avg_vat)} ریال"
        )

    if competition is not None:

        message.append(
            f"📈 <b>رقابت:</b> "
            f"{competition:.2f}%"
        )

    if base is not None:

        message.append(
            f"🔺 <b>اختلاف معامله با پایه:</b> "
            f"{diff_text} ریال"
        )

    message.append("")

    message.append(
        f"{signal_icon} <b>وضعیت:</b> "
        f"{signal_text}"
    )

    message.append("")

    # تحلیل
    if competition is not None:

        if competition >= 5:

            analysis_text = (
                "معاملات با رقابت قابل‌توجه "
                "بالاتر از قیمت پایه انجام شده "
                "و نشان‌دهنده تقاضای قوی در "
                "این گروه کالایی است."
            )

        elif competition >= 2:

            analysis_text = (
                "معاملات با رقابت مثبت انجام شده "
                "و تقاضا نسبت به قیمت پایه "
                "مناسب ارزیابی می‌شود."
            )

        elif competition > 0:

            analysis_text = (
                "رقابت محدود بوده و قیمت معامله "
                "اندکی بالاتر از پایه قرار گرفته است."
            )

        else:

            analysis_text = (
                "معاملات بدون رقابت نسبت به "
                "قیمت پایه انجام شده است."
            )

        message.append(
            "🧠 <b>تحلیل:</b>"
        )

        message.append(
            analysis_text
        )

    message.append("")

    message.append(
        "⚠️ <i>قیمت تمام‌شده در این گزارش "
        "فقط زمانی اعلام می‌شود که تمام "
        "هزینه‌های لازم از منبع معتبر "
        "در دسترس باشد؛ از عددسازی "
        "خودداری می‌شود.</i>"
    )

    message.append("")

    message.append(
        "━━━━━━━━━━━━━━"
    )

    message.append(
        f"📆 <b>تاریخ گزارش:</b> {today}"
    )

    message.append("")

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

    return "\n".join(
        message
    )


# =========================================================
# SIGNATURE
# =========================================================

def analysis_signature(
    analysis,
    today,
):

    raw = (
        today
        + "|"
        + analysis["group"]
        + "|"
        + str(
            round(
                analysis["volume"],
                4,
            )
        )
        + "|"
        + str(
            round(
                analysis["avg"],
                4,
            )
        )
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:24]


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 70)
    print("BOURSE ANALYTIC BOT")
    print("=" * 70)

    today = jalali_string()

    print(
        "TODAY:",
        today,
    )

    history = load_history()

    html = download_page()

    if not html:

        print(
            "NO DATA SOURCE."
        )

        return

    table = find_transaction_table(
        html
    )

    if table is None:

        print(
            "TRANSACTION TABLE NOT FOUND."
        )

        print(
            "NO POST WILL BE SENT."
        )

        return

    records = parse_rows(
        table
    )

    print(
        "VALID TRANSACTION ROWS:",
        len(records),
    )

    if not records:

        print(
            "NO VALID TRANSACTIONS."
        )

        return

    analyses = []

    print()
    print("=" * 70)
    print("GROUP ANALYSIS")
    print("=" * 70)

    for group_name in PRODUCT_GROUPS:

        group_records = [
            r
            for r in records
            if match_group(
                r["product"],
                group_name,
            )
        ]

        if not group_records:

            continue

        analysis = analyze_group(
            group_name,
            group_records,
        )

        if not analysis:

            continue

        analyses.append(
            analysis
        )

        print()
        print(
            group_name
        )

        print(
            "ROWS:",
            len(group_records),
        )

        print(
            "VOLUME:",
            analysis["volume"],
        )

        print(
            "BASE:",
            analysis["base"],
        )

        print(
            "TRADE:",
            analysis["avg"],
        )

        print(
            "COMPETITION:",
            analysis["competition"],
        )

    if not analyses:

        print()
        print(
            "NO STEEL ANALYSIS AVAILABLE."
        )

        return

    sent = 0

    print()
    print("=" * 70)
    print("TELEGRAM")
    print("=" * 70)

    # اولویت شمش
    priority = {
        "شمش بلوم 5SP": 1,
        "شمش بلوم 3SP": 2,
        "بیلت": 3,
        "اسلب": 4,
        "میلگرد": 5,
        "ورق گرم": 6,
        "ورق سرد": 7,
        "ورق گالوانیزه": 8,
    }

    analyses.sort(
        key=lambda x:
        priority.get(
            x["group"],
            99,
        )
    )

    for analysis in analyses:

        if sent >= MAX_POSTS_PER_RUN:

            break

        signature = (
            analysis_signature(
                analysis,
                today,
            )
        )

        if signature in history:

            print(
                "ALREADY SENT:",
                analysis["group"],
            )

            continue

        message = build_message(
            analysis,
            today,
        )

        print(
            "SENDING:",
            analysis["group"],
        )

        success = send_telegram(
            message
        )

        if success:

            history.add(
                signature
            )

            sent += 1

            print(
                "SENT OK:",
                analysis["group"],
            )

        else:

            print(
                "SEND FAILED:",
                analysis["group"],
            )

    save_history(
        history
    )

    print()
    print("=" * 70)
    print(
        "SENT THIS RUN:",
        sent,
    )

    print(
        "HISTORY:",
        len(history),
    )

    print("=" * 70)
    print(
        "BOURSE ANALYTIC BOT FINISHED"
    )


if __name__ == "__main__":
    main()