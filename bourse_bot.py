import requests
import json
from datetime import datetime


# =========================================================
# تنظیمات
# =========================================================

BASE_URL = "https://www.ibrokers.ir"

API_URL = f"{BASE_URL}/api/announcements"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
}


# =========================================================
# تبدیل عدد فارسی به انگلیسی
# =========================================================

def normalize_number(value):

    if value is None:
        return None

    text = str(value)

    persian_numbers = "۰۱۲۳۴۵۶۷۸۹"
    arabic_numbers = "٠١٢٣٤٥٦٧٨٩"

    for i in range(10):
        text = text.replace(persian_numbers[i], str(i))
        text = text.replace(arabic_numbers[i], str(i))

    text = text.replace(",", "")
    text = text.replace("٬", "")

    return text


# =========================================================
# دریافت اطلاعات API
# =========================================================

def get_announcements():

    print("\n" + "=" * 70)
    print("GET ANNOUNCEMENTS")
    print("=" * 70)

    try:

        response = requests.get(
            API_URL,
            headers=HEADERS,
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("CONTENT-TYPE:", response.headers.get("content-type"))
        print("SIZE:", len(response.content))

        if response.status_code != 200:

            print("\n❌ API جواب 200 نداد.")
            print(response.text[:3000])

            return []

        data = response.json()

        print("\nSUCCESS:", data.get("success"))

        announcements = data.get("data", [])

        print("TOTAL RECORDS:", len(announcements))

        return announcements

    except requests.exceptions.Timeout:

        print("\n❌ TIMEOUT")

        return []

    except requests.exceptions.RequestException as e:

        print("\n❌ REQUEST ERROR:")
        print(e)

        return []

    except json.JSONDecodeError:

        print("\n❌ پاسخ JSON نیست.")

        return []

    except Exception as e:

        print("\n❌ ERROR:")
        print(e)

        return []


# =========================================================
# نمایش اطلاعات کلی
# =========================================================

def show_summary(items):

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if not items:

        print("هیچ رکوردی دریافت نشد.")

        return

    print("تعداد کل عرضه‌ها:", len(items))

    dates = []

    for item in items:

        date = item.get("offerDateRaw")

        if date:

            dates.append(str(date))

    if dates:

        print("قدیمی‌ترین تاریخ:", min(dates))
        print("جدیدترین تاریخ:", max(dates))


# =========================================================
# مرتب‌سازی بر اساس تاریخ عرضه
# =========================================================

def sort_by_date(items):

    def get_date(item):

        value = item.get("offerDateRaw")

        if not value:

            return "00000000"

        return str(value)

    return sorted(
        items,
        key=get_date,
        reverse=True
    )


# =========================================================
# نمایش چند عرضه جدید
# =========================================================

def show_latest(items, count=10):

    print("\n" + "=" * 70)
    print(f"LATEST {count} ANNOUNCEMENTS")
    print("=" * 70)

    sorted_items = sort_by_date(items)

    for index, item in enumerate(
        sorted_items[:count],
        1
    ):

        print("\n" + "-" * 70)

        print(f"#{index}")

        print(
            "کد عرضه:",
            item.get("offerCode")
        )

        print(
            "تاریخ عرضه:",
            item.get("offerDate")
        )

        print(
            "offerDateRaw:",
            item.get("offerDateRaw")
        )

        print(
            "کالا:",
            item.get("productName")
        )

        print(
            "نماد:",
            item.get("symbol")
        )

        print(
            "تالار:",
            item.get("hall")
        )

        print(
            "عرضه کننده:",
            item.get("supplier")
        )

        print(
            "تولیدکننده:",
            item.get("producer")
        )

        print(
            "حجم عرضه:",
            item.get("availableVolume")
        )

        print(
            "حداقل خرید:",
            item.get("minimumOffer")
        )

        print(
            "قیمت پایه:",
            item.get("basePrice")
        )

        print(
            "درصد پیش پرداخت:",
            item.get("prepaymentPercent")
        )

        print(
            "محل تحویل:",
            item.get("deliveryLocation")
        )

        print(
            "نوع تسویه:",
            item.get("settlementType")
        )

        print(
            "وضعیت:",
            item.get("status")
        )


# =========================================================
# پیدا کردن عرضه های فولادی
# =========================================================

def find_steel(items):

    print("\n" + "=" * 70)
    print("STEEL PRODUCTS")
    print("=" * 70)

    keywords = [

        "فولاد",
        "میلگرد",
        "تیرآهن",
        "ورق",
        "شمش",
        "بلوم",
        "بیلت",
        "آهن",
        "نبشی",
        "ناودانی",
        "مفتول",
        "اسلب",
        "گندله",
        "آهن اسفنجی",
        "کویل",
        "کنسانتره",
        "تختال",
        "سنگ آهن",

    ]

    steel_items = []

    for item in items:

        text = " ".join([

            str(item.get("productName") or ""),
            str(item.get("symbol") or ""),
            str(item.get("producer") or ""),
            str(item.get("supplier") or ""),
            str(item.get("hall") or ""),

        ])

        text = text.lower()

        for keyword in keywords:

            if keyword.lower() in text:

                steel_items.append(item)

                break

    print(
        "تعداد عرضه های مرتبط با فولاد:",
        len(steel_items)
    )

    for index, item in enumerate(
        sort_by_date(steel_items)[:20],
        1
    ):

        print("\n" + "-" * 60)

        print(f"#{index}")

        print(
            "کد عرضه:",
            item.get("offerCode")
        )

        print(
            "تاریخ:",
            item.get("offerDate")
        )

        print(
            "کالا:",
            item.get("productName")
        )

        print(
            "نماد:",
            item.get("symbol")
        )

        print(
            "عرضه کننده:",
            item.get("supplier")
        )

        print(
            "تولیدکننده:",
            item.get("producer")
        )

        print(
            "حجم:",
            item.get("availableVolume")
        )

        print(
            "قیمت پایه:",
            item.get("basePrice")
        )

        print(
            "وضعیت:",
            item.get("status")
        )

    return steel_items


# =========================================================
# ذخیره اطلاعات خام برای بررسی
# =========================================================

def save_json(items):

    filename = "announcements.json"

    try:

        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                items,
                file,
                ensure_ascii=False,
                indent=2
            )

        print("\n✅ اطلاعات در فایل ذخیره شد:")
        print(filename)

    except Exception as e:

        print("\n❌ خطا در ذخیره فایل:")
        print(e)


# =========================================================
# بررسی پارامترهای احتمالی API
# =========================================================

def test_parameters():

    print("\n" + "=" * 70)
    print("TESTING API PARAMETERS")
    print("=" * 70)

    tests = [

        ("page=1", "?page=1"),

        ("limit=10", "?limit=10"),

        (
            "page=1&limit=10",
            "?page=1&limit=10"
        ),

        (
            "page=1&pageSize=10",
            "?page=1&pageSize=10"
        ),

        (
            "limit=100",
            "?limit=100"
        ),

        (
            "date=today",
            "?date=today"
        ),

        (
            "page=1&limit=100",
            "?page=1&limit=100"
        ),

    ]

    for name, query in tests:

        print("\n" + "-" * 60)

        print("TEST:", name)

        try:

            response = requests.get(
                API_URL + query,
                headers=HEADERS,
                timeout=20
            )

            print(
                "STATUS:",
                response.status_code
            )

            if response.status_code == 200:

                try:

                    data = response.json()

                    records = data.get(
                        "data",
                        []
                    )

                    print(
                        "RECORDS:",
                        len(records)
                    )

                except Exception:

                    print(
                        "پاسخ JSON قابل خواندن نیست."
                    )

            else:

                print(
                    response.text[:500]
                )

        except Exception as e:

            print(
                "ERROR:",
                e
            )


# =========================================================
# بررسی صفحات API
# =========================================================

def test_pages():

    print("\n" + "=" * 70)
    print("TESTING API PAGES")
    print("=" * 70)

    for page in range(1, 11):

        print("\n" + "-" * 70)

        print(
            f"PAGE {page}"
        )

        try:

            response = requests.get(

                API_URL,

                params={
                    "page": page,
                    "limit": 10
                },

                headers=HEADERS,

                timeout=30
            )

            print(
                "STATUS:",
                response.status_code
            )

            if response.status_code != 200:

                print("❌ خطا")

                continue

            data = response.json()

            items = data.get(
                "data",
                []
            )

            print(
                "RECORDS:",
                len(items)
            )

            if not items:

                print(
                    "❌ این صفحه خالی است."
                )

                continue

            # -------------------------------------------------
            # اولین رکورد
            # -------------------------------------------------

            first = items[0]

            print("\nاولین رکورد صفحه:")

            print(
                "کد عرضه:",
                first.get("offerCode")
            )

            print(
                "تاریخ:",
                first.get("offerDate")
            )

            print(
                "offerDateRaw:",
                first.get("offerDateRaw")
            )

            print(
                "کالا:",
                first.get("productName")
            )

            # -------------------------------------------------
            # آخرین رکورد
            # -------------------------------------------------

            last = items[-1]

            print("\nآخرین رکورد صفحه:")

            print(
                "کد عرضه:",
                last.get("offerCode")
            )

            print(
                "تاریخ:",
                last.get("offerDate")
            )

            print(
                "offerDateRaw:",
                last.get("offerDateRaw")
            )

            print(
                "کالا:",
                last.get("productName")
            )

        except Exception as e:

            print(
                "❌ ERROR:",
                e
            )


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n")

    print("=" * 70)

    print(
        "IBROKERS - BOURSE COMMODITY "
        "ANNOUNCEMENTS TEST"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # دریافت اطلاعات
    # -----------------------------------------------------

    items = get_announcements()

    if not items:

        print(
            "\n❌ هیچ اطلاعاتی دریافت نشد."
        )

        return

    # -----------------------------------------------------
    # خلاصه
    # -----------------------------------------------------

    show_summary(items)

    # -----------------------------------------------------
    # آخرین عرضه ها
    # -----------------------------------------------------

    show_latest(
        items,
        count=10
    )

    # -----------------------------------------------------
    # عرضه های فولادی
    # -----------------------------------------------------

    steel_items = find_steel(items)

    # -----------------------------------------------------
    # ذخیره اطلاعات
    # -----------------------------------------------------

    save_json(items)

    # -----------------------------------------------------
    # تست پارامترهای API
    # -----------------------------------------------------

    test_parameters()

    # -----------------------------------------------------
    # تست صفحات API
    # -----------------------------------------------------

    test_pages()

    # -----------------------------------------------------
    # پایان
    # -----------------------------------------------------

    print("\n" + "=" * 70)

    print(
        "TEST FINISHED"
    )

    print("=" * 70)

    print(
        "\n✅ تست کامل شد."
    )

    print(
        "بخش مهم برای ارسال:"
    )

    print(
        "1. SUMMARY"
    )

    print(
        "2. LATEST 10 ANNOUNCEMENTS"
    )

    print(
        "3. STEEL PRODUCTS"
    )

    print(
        "4. TESTING API PARAMETERS"
    )

    print(
        "5. TESTING API PAGES"
    )


# =========================================================
# اجرای برنامه
# =========================================================

if __name__ == "__main__":

    main()