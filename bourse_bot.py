import os
import re
import json
import hashlib
import requests
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser


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

# فقط یک پست تحلیلی در هر اجرا
MAX_POSTS_PER_RUN = 1


# =========================================================
# PRODUCT GROUPS
# =========================================================

PRODUCT_GROUPS = {
    "شمش بلوم 5SP": ["شمش بلوم", "5SP"],
    "شمش بلوم 3SP": ["شمش بلوم", "3SP"],
    "بیلت": ["بیلت"],
    "اسلب": ["اسلب"],
    "میلگرد": ["میلگرد"],
    "ورق گرم": ["ورق گرم"],
    "ورق سرد": ["ورق سرد"],
    "ورق گالوانیزه": ["ورق گالوانیزه"],
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
# HTML TABLE PARSER
# بدون pandas
# =========================================================

class TableParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.tables = []
        self.current_table = None
        self.current_row = None
        self.current_cell = None
        self.cell_text = []

    def handle_starttag(self, tag, attrs):

        tag = tag.lower()

        if tag == "table":

            self.current_table = []

        elif tag == "tr" and self.current_table is not None:

            self.current_row = []

        elif tag in ("td", "th") and self.current_row is not None:

            self.current_cell = []
            self.cell_text = []

    def handle_data(self, data):

        if self.current_cell is not None:

            self.cell_text.append(data)

    def handle_endtag(self, tag):

        tag = tag.lower()

        if tag in ("td", "th"):

            if self.current_cell is not None:

                text = "".join(
                    self.cell_text
                )

                text = clean_text(text)

                self.current_row.append(text)

                self.current_cell = None
                self.cell_text = []

        elif tag == "tr":

            if (
                self.current_row is not None
                and self.current_table is not None
            ):

                if any(
                    str(x).strip()
                    for x in self.current_row
                ):

                    self.current_table.append(
                        self.current_row
                    )

            self.current_row = None

        elif tag == "table":

            if self.current_table is not None:

                if self.current_table:

                    self.tables.append(
                        self.current_table
                    )

            self.current_table = None


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

    text = normalize_digits(value)

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def number(value):

    if value is None:
        return None

    text = normalize_digits(value)

    text = (
        text
        .replace(",", "")
        .replace("٬", "")
        .replace(" ", "")
    )

    if not text:
        return None

    # حذف کاراکترهای اضافی ولی حفظ اعشار
    text = re.sub(
        r"[^\d.\-]",
        "",
        text,
    )

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

        return f"{value:,.0f}"

    except Exception:

        return str(value)


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

    now = datetime.now(iran_tz)

    return gregorian_to_jalali(
        now.year,
        now.month,
        now.day,
    )


def jalali_string():

    y, m, d = today_jalali()

    return f"{y:04d}/{m:02d}/{d:02d}"


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

        print(
            "TELEGRAM STATUS:",
            response.status_code,
        )

        if not response.ok:

            print(
                "TELEGRAM ERROR:",
                response.text[:1000],
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
# DOWNLOAD
# =========================================================

def download_page():

    print()
    print("=" * 70)
    print("SPADFOLAD DATA SOURCE")
    print("=" * 70)

    headers = {

        "User-Agent":
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120 Safari/537.36",

        "Accept":
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8",

        "Accept-Language":
            "fa-IR,fa;q=0.9,en;q=0.8",
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

        print(
            "SPAD BYTES:",
            len(response.content),
        )

        response.raise_for_status()

        # اجازه بده requests encoding سایت را تعیین کند
        response.encoding = response.apparent_encoding or "utf-8"

        return response.text

    except Exception as e:

        print(
            "SPAD ERROR:",
            e,
        )

        return None


# =========================================================
# READ TABLES
# =========================================================

def read_tables(html):

    print(
        "PARSING HTML DIRECTLY..."
    )

    parser = TableParser()

    try:

        parser.feed(html)

    except Exception as e:

        print(
            "HTML PARSER ERROR:",
            e,
        )

        return []

    print(
        "TABLES FOUND:",
        len(parser.tables),
    )

    for i, table in enumerate(
        parser.tables
    ):

        if table:

            print(
                f"TABLE {i}: "
                f"ROWS={len(table)} "
                f"COLS={max(len(x) for x in table)}"
            )

            print(
                "HEADER:",
                " | ".join(
                    table[0][:12]
                )
            )

    return parser.tables


# =========================================================
# FIND TRANSACTION TABLE
# =========================================================

def find_transaction_table(
    tables
):

    best = None
    best_score = 0

    wanted = [
        "نام کالا",
        "تولیدکننده",
        "حجم معامله",
        "قیمت پایه",
        "قیمت میانگین",
        "درصد رقابت",
    ]

    for index, table in enumerate(
        tables
    ):

        if not table:
            continue

        header = " ".join(
            table[0]
        )

        score = 0

        for item in wanted:

            if item in header:

                score += 1

        print(
            f"TABLE {index} SCORE:",
            score,
        )

        if score > best_score:

            best_score = score
            best = table

    if best is not None:

        print(
            "TRANSACTION TABLE FOUND"
        )

        print(
            "MATCH SCORE:",
            best_score,
        )

    return best


# =========================================================
# MAP COLUMNS
# =========================================================

def make_column_map(header):

    mapping = {}

    for index, name in enumerate(
        header
    ):

        name = clean_text(name)

        if "نام کالا" in name:
            mapping["product"] = index

        elif "تولیدکننده" in name:
            mapping["producer"] = index

        elif "حجم معامله" in name:
            mapping["volume"] = index

        elif "قیمت پایه (با مالیات)" in name:
            mapping["base_vat"] = index

        elif "قیمت پایه" in name:
            mapping["base"] = index

        elif "قیمت میانگین (با مالیات)" in name:
            mapping["avg_vat"] = index

        elif "قیمت میانگین" in name:
            mapping["avg"] = index

        elif "درصد رقابت" in name:
            mapping["competition"] = index

    return mapping


def get_cell(row, mapping, key):

    index = mapping.get(key)

    if index is None:
        return ""

    if index >= len(row):
        return ""

    return clean_text(
        row[index]
    )


# =========================================================
# PARSE TRANSACTIONS
# =========================================================

def parse_transactions(table):

    if not table or len(table) < 2:

        return []

    header = table[0]

    mapping = make_column_map(
        header
    )

    print(
        "COLUMN MAP:",
        mapping,
    )

    required = [
        "product",
        "volume",
        "base",
        "avg",
    ]

    missing = [
        x
        for x in required
        if x not in mapping
    ]

    if missing:

        print(
            "MISSING COLUMNS:",
            missing,
        )

        return []

    records = []

    for row in table[1:]:

        product = get_cell(
            row,
            mapping,
            "product",
        )

        if not product:
            continue

        volume = number(
            get_cell(
                row,
                mapping,
                "volume",
            )
        )

        base = number(
            get_cell(
                row,
                mapping,
                "base",
            )
        )

        avg = number(
            get_cell(
                row,
                mapping,
                "avg",
            )
        )

        avg_vat = number(
            get_cell(
                row,
                mapping,
                "avg_vat",
            )
        )

        competition = number(
            get_cell(
                row,
                mapping,
                "competition",
            )
        )

        producer = get_cell(
            row,
            mapping,
            "producer",
        )

        if volume is None:
            continue

        if volume <= 0:
            continue

        if avg is None:
            continue

        # اگر سایت درصد رقابت نداده باشد،
        # خودمان دقیقاً از قیمت پایه و معامله حساب می‌کنیم.
        if (
            competition is None
            and base is not None
            and base > 0
        ):

            competition = (
                (avg - base)
                / base
                * 100
            )

        records.append(
            {
                "product": product,
                "producer": producer,
                "volume": volume,
                "base": base,
                "avg": avg,
                "avg_vat": avg_vat,
                "competition": competition,
            }
        )

    print(
        "VALID TRANSACTIONS:",
        len(records),
    )

    return records


# =========================================================
# MATCH PRODUCT
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

    total_value = 0
    total_volume = 0

    for record in records:

        volume = record.get(
            "volume"
        )

        value = record.get(
            field
        )

        if (
            volume is None
            or value is None
        ):

            continue

        total_value += (
            volume * value
        )

        total_volume += volume

    if total_volume <= 0:

        return None

    return (
        total_value
        / total_volume
    )


# =========================================================
# ANALYZE GROUP
# =========================================================

def analyze_group(
    group_name,
    records,
):

    if not records:

        return None

    total_volume = sum(
        r["volume"]
        for r in records
    )

    base = weighted_average(
        records,
        "base",
    )

    avg = weighted_average(
        records,
        "avg",
    )

    avg_vat = weighted_average(
        records,
        "avg_vat",
    )

    if avg is None:

        return None

    if (
        base is not None
        and base > 0
    ):

        competition = (
            (avg - base)
            / base
            * 100
        )

    else:

        competition = None

    producers = sorted(
        set(
            r["producer"]
            for r in records
            if r["producer"]
        )
    )

    return {
        "group": group_name,
        "records": records,
        "volume": total_volume,
        "base": base,
        "avg": avg,
        "avg_vat": avg_vat,
        "competition": competition,
        "producers": producers,
    }


# =========================================================
# SIGNAL
# =========================================================

def signal(
    competition
):

    if competition is None:

        return (
            "⚪",
            "قابل ارزیابی نیست",
        )

    if competition >= 5:

        return (
            "🟢",
            "تقاضای قوی",
        )

    if competition >= 2:

        return (
            "🟢",
            "تقاضای مناسب",
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
# BUILD ONE COMBINED POST
# =========================================================

def build_message(
    analyses,
    today,
):

    lines = []

    lines.append(
        "📊 <b>گزارش تحلیلی معاملات بورس کالا</b>"
    )

    lines.append(
        f"📆 {today}"
    )

    lines.append("")

    lines.append(
        "🔎 <b>خلاصه بازار فولاد</b>"
    )

    lines.append(
        "قیمت‌ها بر اساس معاملات ثبت‌شده "
        "و میانگین وزنی حجم معاملات محاسبه شده‌اند."
    )

    lines.append("")

    for analysis in analyses:

        group = analysis["group"]
        volume = analysis["volume"]
        base = analysis["base"]
        avg = analysis["avg"]
        avg_vat = analysis["avg_vat"]
        competition = analysis["competition"]

        icon, status = signal(
            competition
        )

        if (
            base is not None
            and avg is not None
        ):

            difference = avg - base

        else:

            difference = None

        lines.append(
            f"━━━━━━━━━━━━━━"
        )

        lines.append(
            f"🏷 <b>{group}</b>"
        )

        lines.append(
            f"📦 حجم معامله: "
            f"<b>{format_number(volume)}</b> تن"
        )

        if base is not None:

            lines.append(
                f"💰 قیمت پایه: "
                f"<b>{format_number(base)}</b> ریال"
            )

        lines.append(
            f"🔨 قیمت معامله: "
            f"<b>{format_number(avg)}</b> ریال"
        )

        if avg_vat is not None:

            lines.append(
                f"🧾 قیمت معامله با مالیات: "
                f"<b>{format_number(avg_vat)}</b> ریال"
            )

        if competition is not None:

            lines.append(
                f"📈 میزان رقابت: "
                f"<b>{competition:.2f}%</b>"
            )

        if difference is not None:

            lines.append(
                f"🔺 افزایش نسبت به پایه: "
                f"<b>{format_number(difference)}</b> ریال"
            )

        lines.append(
            f"{icon} وضعیت تقاضا: <b>{status}</b>"
        )

        lines.append("")

    # =====================================================
    # MARKET INTERPRETATION
    # =====================================================

    lines.append(
        "🧠 <b>جمع‌بندی تحلیلی</b>"
    )

    valid = [
        x
        for x in analyses
        if x["competition"] is not None
    ]

    if valid:

        strongest = max(
            valid,
            key=lambda x:
            x["competition"]
        )

        weakest = min(
            valid,
            key=lambda x:
            x["competition"]
        )

        lines.append(
            f"• بیشترین رقابت: "
            f"<b>{strongest['group']}</b> "
            f"با {strongest['competition']:.2f}%"
        )

        lines.append(
            f"• کمترین رقابت: "
            f"<b>{weakest['group']}</b> "
            f"با {weakest['competition']:.2f}%"
        )

        positive = [
            x
            for x in valid
            if x["competition"] > 0
        ]

        if positive:

            lines.append(
                "• در گروه‌های دارای رقابت، "
                "قیمت معامله بالاتر از قیمت پایه "
                "تعیین شده است."
            )

        else:

            lines.append(
                "• در گروه‌های بررسی‌شده "
                "رقابت معناداری بالاتر از پایه "
                "ثبت نشده است."
            )

    lines.append("")

    lines.append(
        "💡 <b>نکته مهم:</b> "
        "قیمت «تمام‌شده نهایی» شامل مالیات، "
        "هزینه کارگزاری، انبار، حمل و سایر "
        "هزینه‌ها فقط در صورت وجود داده معتبر "
        "محاسبه می‌شود؛ هیچ عددی حدسی وارد گزارش نمی‌شود."
    )

    lines.append("")

    lines.append(
        "━━━━━━━━━━━━━━"
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
# SIGNATURE
# =========================================================

def make_signature(
    analyses,
    today,
):

    parts = [today]

    for a in analyses:

        parts.extend(
            [
                a["group"],
                str(
                    round(
                        a["volume"],
                        3,
                    )
                ),
                str(
                    round(
                        a["avg"],
                        3,
                    )
                ),
            ]
        )

    raw = "|".join(parts)

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:32]


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

    print(
        "HISTORY:",
        len(history),
    )

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    html = download_page()

    if not html:

        print(
            "NO DATA SOURCE."
        )

        return

    # -----------------------------------------------------
    # TABLES
    # -----------------------------------------------------

    tables = read_tables(
        html
    )

    if not tables:

        print(
            "NO HTML TABLE FOUND."
        )

        return

    transaction_table = (
        find_transaction_table(
            tables
        )
    )

    if transaction_table is None:

        print(
            "TRANSACTION TABLE NOT FOUND."
        )

        return

    # -----------------------------------------------------
    # TRANSACTIONS
    # -----------------------------------------------------

    records = parse_transactions(
        transaction_table
    )

    if not records:

        print(
            "NO VALID TRANSACTIONS."
        )

        return

    # -----------------------------------------------------
    # GROUP ANALYSIS
    # -----------------------------------------------------

    analyses = []

    print()
    print("=" * 70)
    print("GROUP ANALYSIS")
    print("=" * 70)

    # اولویت
    priority = [
        "شمش بلوم 5SP",
        "شمش بلوم 3SP",
        "بیلت",
        "اسلب",
        "میلگرد",
        "ورق گرم",
        "ورق سرد",
        "ورق گالوانیزه",
    ]

    for group_name in priority:

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

        if analysis is None:

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

    # -----------------------------------------------------
    # NO STEEL
    # -----------------------------------------------------

    if not analyses:

        print()
        print(
            "NO STEEL ANALYSIS AVAILABLE."
        )

        return

    # حداکثر 5 گروه برای اینکه پست بیش از حد طولانی نشود
    analyses = analyses[:5]

    # -----------------------------------------------------
    # SIGNATURE
    # -----------------------------------------------------

    signature = make_signature(
        analyses,
        today,
    )

    print()
    print(
        "SIGNATURE:",
        signature,
    )

    if signature in history:

        print(
            "THIS ANALYSIS WAS ALREADY SENT."
        )

        return

    # -----------------------------------------------------
    # BUILD
    # -----------------------------------------------------

    message = build_message(
        analyses,
        today,
    )

    print()
    print("=" * 70)
    print("SENDING TELEGRAM")
    print("=" * 70)

    print(
        message
    )

    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------

    success = send_telegram(
        message
    )

    if success:

        history.add(
            signature
        )

        save_history(
            history
        )

        print(
            "POST SENT SUCCESSFULLY."
        )

    else:

        print(
            "POST FAILED."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()