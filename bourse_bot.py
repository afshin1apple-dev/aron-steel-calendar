import requests
import json
import time


# =========================================================
# تنظیمات
# =========================================================

API_URL = "https://www.ibrokers.ir/api/announcements"

LIMIT = 10

# آخرین صفحات موجود طبق API
PAGES_TO_CHECK = [
    23417,
    23416,
    23415,
    23414,
    23413,
]


# =========================================================
# دریافت اطلاعات یک صفحه
# =========================================================

def get_page(page):

    params = {
        "page": page,
        "limit": LIMIT
    }

    print("=" * 80)
    print(f"PAGE: {page}")
    print("=" * 80)

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        print("URL:")
        print(response.url)

        print("STATUS:", response.status_code)
        print("SIZE:", len(response.content))

        response.raise_for_status()

        result = response.json()

        # -------------------------------------------------
        # Pagination
        # -------------------------------------------------

        pagination = result.get("pagination", {})

        print()
        print("PAGINATION:")
        print(json.dumps(
            pagination,
            ensure_ascii=False,
            indent=2
        ))

        # -------------------------------------------------
        # Data
        # -------------------------------------------------

        records = result.get("data", [])

        print()
        print("RECORDS:", len(records))
        print()

        if not records:
            print("NO DATA")
            return []

        # -------------------------------------------------
        # نمایش رکوردها
        # -------------------------------------------------

        for index, item in enumerate(records, 1):

            print("-" * 80)

            print("RECORD:", index)

            print(
                "ID:",
                item.get("id")
            )

            print(
                "OFFER CODE:",
                item.get("offer_code")
            )

            print(
                "DATE:",
                item.get("date")
            )

            print(
                "RAW DATE:",
                item.get("raw_date")
            )

            print(
                "PRODUCT:",
                item.get("product")
            )

            print(
                "SYMBOL:",
                item.get("symbol")
            )

            print(
                "HALL:",
                item.get("hall")
            )

            print(
                "PRODUCER:",
                item.get("producer")
            )

            print(
                "SUPPLIER:",
                item.get("supplier")
            )

            print(
                "VOLUME:",
                item.get("volume")
            )

            print(
                "VOLUME RAW:",
                item.get("volume_raw")
            )

            print(
                "BASE PRICE:",
                item.get("base_price")
            )

            print(
                "DELIVERY DATE:",
                item.get("delivery_date")
            )

        return records

    except requests.exceptions.Timeout:

        print("ERROR: REQUEST TIMEOUT")

    except requests.exceptions.ConnectionError as e:

        print("ERROR: CONNECTION ERROR")
        print(repr(e))

    except requests.exceptions.HTTPError as e:

        print("ERROR: HTTP ERROR")
        print(repr(e))

    except json.JSONDecodeError:

        print("ERROR: INVALID JSON")
        print(response.text[:1000])

    except Exception as e:

        print("ERROR:")
        print(repr(e))

    return []


# =========================================================
# MAIN
# =========================================================

def main():

    print()
    print("=" * 80)
    print("iBROKERS - LATEST PAGES DISCOVERY")
    print("=" * 80)
    print()

    all_records = []

    for page in PAGES_TO_CHECK:

        records = get_page(page)

        all_records.extend(records)

        time.sleep(1)

        print()
        print()


    # =====================================================
    # خلاصه نهایی
    # =====================================================

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print("TOTAL RECORDS RECEIVED:", len(all_records))

    print()

    if all_records:

        print("DATES FOUND:")

        dates = []

        for item in all_records:

            date = item.get("date")

            if date and date not in dates:
                dates.append(date)

        for date in dates:
            print("-", date)

        print()
        print("PRODUCTS:")

        for item in all_records:

            product = item.get("product")

            if product:
                print(
                    "-",
                    item.get("date"),
                    "|",
                    product
                )

    else:

        print("هیچ رکوردی دریافت نشد.")


    print()
    print("=" * 80)
    print("FINISHED")
    print("=" * 80)


# =========================================================
# اجرا
# =========================================================

if __name__ == "__main__":
    main()