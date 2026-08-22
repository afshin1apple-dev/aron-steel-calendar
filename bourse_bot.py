import requests
import json
from urllib.parse import urljoin
from datetime import datetime


# =========================================================
# تنظیمات
# =========================================================

BASE_URL = "https://www.ibrokers.ir"

CURRENT_API = f"{BASE_URL}/api/announcements"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Referer": f"{BASE_URL}/markets/physical/announcement",
}


# =========================================================
# تبدیل اعداد فارسی / عربی
# =========================================================

def normalize_number(value):

    if value is None:
        return None

    text = str(value)

    persian = "۰۱۲۳۴۵۶۷۸۹"
    arabic = "٠١٢٣٤٥٦٧٨٩"

    for i in range(10):
        text = text.replace(persian[i], str(i))
        text = text.replace(arabic[i], str(i))

    text = text.replace(",", "")
    text = text.replace("٬", "")

    return text


# =========================================================
# GET JSON
# =========================================================

def get_json(url, params=None):

    try:

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        print("\nURL:")
        print(response.url)

        print("STATUS:")
        print(response.status_code)

        print("SIZE:")
        print(len(response.content))

        print("CONTENT-TYPE:")
        print(response.headers.get("content-type"))

        if response.status_code != 200:

            print("❌ HTTP ERROR")

            return None

        try:

            return response.json()

        except Exception as e:

            print("❌ JSON ERROR:")
            print(e)

            print(
                response.text[:1000]
            )

            return None

    except Exception as e:

        print("❌ REQUEST ERROR:")
        print(e)

        return None


# =========================================================
# چاپ JSON زیبا
# =========================================================

def print_json(title, data):

    print("\n")
    print("=" * 70)
    print(title)
    print("=" * 70)

    try:

        print(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2
            )
        )

    except Exception as e:

        print("PRINT ERROR:", e)
        print(data)


# =========================================================
# تست اصلی API
# =========================================================

def test_current_api():

    print("\n")
    print("=" * 70)
    print("CURRENT API - DEEP INSPECTION")
    print("=" * 70)

    data = get_json(
        CURRENT_API,
        params={
            "limit": 10
        }
    )

    if not data:

        print("❌ پاسخی دریافت نشد.")

        return None

    # -----------------------------------------------------
    # کلیدهای اصلی
    # -----------------------------------------------------

    print("\nTOP LEVEL KEYS:")

    print(
        list(data.keys())
    )

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    print("\nSUCCESS:")

    print(
        data.get("success")
    )

    # -----------------------------------------------------
    # PAGINATION
    # -----------------------------------------------------

    pagination = data.get(
        "pagination"
    )

    print_json(
        "PAGINATION",
        pagination
    )

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    filters = data.get(
        "filters"
    )

    print_json(
        "FILTERS",
        filters
    )

    # -----------------------------------------------------
    # DATA
    # -----------------------------------------------------

    items = data.get(
        "data",
        []
    )

    print("\n")
    print("=" * 70)
    print("DATA SUMMARY")
    print("=" * 70)

    print(
        "RECORDS:",
        len(items)
    )

    # -----------------------------------------------------
    # نمایش رکوردها
    # -----------------------------------------------------

    for index, item in enumerate(
        items[:10],
        1
    ):

        print("\n")
        print("-" * 70)

        print(
            "RECORD:",
            index
        )

        print(
            "ID:",
            item.get("id")
        )

        print(
            "OFFER CODE:",
            item.get("offerCode")
        )

        print(
            "DATE:",
            item.get("offerDate")
        )

        print(
            "RAW DATE:",
            item.get("offerDateRaw")
        )

        print(
            "PRODUCT:",
            item.get("productName")
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
            item.get("availableVolume")
        )

        print(
            "VOLUME RAW:",
            item.get("availableVolumeRaw")
        )

        print(
            "BASE PRICE:",
            item.get("basePrice")
        )

        print(
            "BASE PRICE RAW:",
            item.get("basePriceRaw")
        )

        print(
            "UNIT:",
            item.get("unit")
        )

        print(
            "DELIVERY DATE:",
            item.get("delivery_date")
        )

        print(
            "STATUS:",
            item.get("status")
        )

        print(
            "MAIN GROUP:",
            item.get("mainGroup")
        )

        print(
            "MAIN GROUP ID:",
            item.get("main_group_id")
        )

        print(
            "GROUP:",
            item.get("group")
        )

        print(
            "GROUP ID:",
            item.get("group_id")
        )

        print(
            "SUB GROUP:",
            item.get("subGroup")
        )

        print(
            "SUB GROUP ID:",
            item.get("sub_group_id")
        )

        print(
            "COMMODITY ID:",
            item.get("commodity_id")
        )

    # -----------------------------------------------------
    # رکورد اول کامل
    # -----------------------------------------------------

    if items:

        print_json(
            "FULL FIRST RECORD",
            items[0]
        )

    return data


# =========================================================
# تست Pagination
# =========================================================

def test_pagination():

    print("\n")
    print("=" * 70)
    print("TEST PAGINATION")
    print("=" * 70)

    tests = [

        {
            "limit": 5,
            "page": 1
        },

        {
            "limit": 5,
            "page": 2
        },

        {
            "limit": 10,
            "page": 1
        },

        {
            "limit": 10,
            "page": 2
        },

        {
            "limit": 20,
            "page": 1
        },

        {
            "limit": 50,
            "page": 1
        },

        {
            "limit": 100,
            "page": 1
        },

    ]

    for params in tests:

        print("\n")
        print("-" * 70)

        print(
            "PARAMS:",
            params
        )

        data = get_json(
            CURRENT_API,
            params=params
        )

        if not data:

            print("NO DATA")

            continue

        items = data.get(
            "data",
            []
        )

        pagination = data.get(
            "pagination"
        )

        print(
            "RECORDS:",
            len(items)
        )

        print(
            "PAGINATION:"
        )

        print_json(
            "PAGINATION RESULT",
            pagination
        )

        if items:

            print(
                "FIRST:",
                items[0].get("offerDate"),
                "|",
                items[0].get("offerCode"),
                "|",
                items[0].get("productName")
            )

            print(
                "LAST:",
                items[-1].get("offerDate"),
                "|",
                items[-1].get("offerCode"),
                "|",
                items[-1].get("productName")
            )


# =========================================================
# تست پارامترهای Sort
# =========================================================

def test_sort_parameters():

    print("\n")
    print("=" * 70)
    print("TEST SORT PARAMETERS")
    print("=" * 70)

    tests = [

        {
            "limit": 10,
            "sort": "offerDate"
        },

        {
            "limit": 10,
            "sort": "-offerDate"
        },

        {
            "limit": 10,
            "sort": "offerDateRaw"
        },

        {
            "limit": 10,
            "sort": "-offerDateRaw"
        },

        {
            "limit": 10,
            "sortBy": "offerDate"
        },

        {
            "limit": 10,
            "sortBy": "offerDateRaw"
        },

        {
            "limit": 10,
            "order": "desc"
        },

        {
            "limit": 10,
            "order": "asc"
        },

        {
            "limit": 10,
            "sortOrder": "desc"
        },

        {
            "limit": 10,
            "sortOrder": "asc"
        },

    ]

    for params in tests:

        print("\n")
        print("-" * 70)

        print(
            "PARAMS:",
            params
        )

        data = get_json(
            CURRENT_API,
            params=params
        )

        if not data:

            print("NO DATA")

            continue

        items = data.get(
            "data",
            []
        )

        print(
            "RECORDS:",
            len(items)
        )

        if items:

            print(
                "FIRST:",
                items[0].get("offerDate"),
                "|",
                items[0].get("offerCode"),
                "|",
                items[0].get("productName")
            )

            print(
                "LAST:",
                items[-1].get("offerDate"),
                "|",
                items[-1].get("offerCode"),
                "|",
                items[-1].get("productName")
            )


# =========================================================
# تست فیلترهای تاریخ
# =========================================================

def test_date_parameters():

    print("\n")
    print("=" * 70)
    print("TEST DATE PARAMETERS")
    print("=" * 70)

    tests = [

        {
            "fromDate": "14050801",
            "toDate": "14050831"
        },

        {
            "startDate": "14050801",
            "endDate": "14050831"
        },

        {
            "dateFrom": "14050801",
            "dateTo": "14050831"
        },

        {
            "from": "14050801",
            "to": "14050831"
        },

        {
            "start": "14050801",
            "end": "14050831"
        },

        {
            "fromDate": "1405/08/01",
            "toDate": "1405/08/31"
        },

        {
            "startDate": "1405/08/01",
            "endDate": "1405/08/31"
        },

    ]

    for params in tests:

        print("\n")
        print("-" * 70)

        print(
            "PARAMS:",
            params
        )

        data = get_json(
            CURRENT_API,
            params=params
        )

        if not data:

            print("NO JSON")

            continue

        items = data.get(
            "data",
            []
        )

        print(
            "RECORDS:",
            len(items)
        )

        if items:

            dates = []

            for item in items:

                value = item.get(
                    "offerDateRaw"
                )

                if value:

                    dates.append(
                        str(value)
                    )

            if dates:

                print(
                    "MIN DATE:",
                    min(dates)
                )

                print(
                    "MAX DATE:",
                    max(dates)
                )

            print(
                "FIRST:",
                items[0].get("offerDate"),
                items[0].get("offerCode"),
                items[0].get("productName")
            )

            print(
                "LAST:",
                items[-1].get("offerDate"),
                items[-1].get("offerCode"),
                items[-1].get("productName")
            )


# =========================================================
# تست فیلترهای احتمالی
# =========================================================

def test_filter_parameters():

    print("\n")
    print("=" * 70)
    print("TEST FILTER PARAMETERS")
    print("=" * 70)

    tests = [

        {
            "limit": 10,
            "year": 1405
        },

        {
            "limit": 10,
            "jalaliYear": 1405
        },

        {
            "limit": 10,
            "date": "1405"
        },

        {
            "limit": 10,
            "offerDate": "1405"
        },

        {
            "limit": 10,
            "group": "فولاد"
        },

        {
            "limit": 10,
            "category": "فولاد"
        },

        {
            "limit": 10,
            "productGroup": "فولاد"
        },

        {
            "limit": 10,
            "hall": "تالار صنعتی"
        },

        {
            "limit": 10,
            "main_group_id": 1
        },

        {
            "limit": 10,
            "group_id": 1
        },

        {
            "limit": 10,
            "sub_group_id": 1
        },

        {
            "limit": 10,
            "commodity_id": 1
        },

        {
            "limit": 10,
            "tradingHallId": 1
        },

    ]

    for params in tests:

        print("\n")
        print("-" * 70)

        print(
            "PARAMS:",
            params
        )

        data = get_json(
            CURRENT_API,
            params=params
        )

        if not data:

            print("NO JSON")

            continue

        items = data.get(
            "data",
            []
        )

        print(
            "RECORDS:",
            len(items)
        )

        if items:

            print(
                "FIRST:",
                items[0].get("offerDate"),
                "|",
                items[0].get("offerCode"),
                "|",
                items[0].get("productName")
            )

            print(
                "LAST:",
                items[-1].get("offerDate"),
                "|",
                items[-1].get("offerCode"),
                "|",
                items[-1].get("productName")
            )


# =========================================================
# تست endpointهای احتمالی
# =========================================================

def test_possible_endpoints():

    print("\n")
    print("=" * 70)
    print("TEST POSSIBLE ENDPOINTS")
    print("=" * 70)

    endpoints = [

        "/api/announcements",

        "/api/announcement",

        "/api/physical/announcements",

        "/api/physical/announcement",

        "/api/markets/physical/announcements",

        "/api/markets/physical/announcement",

        "/api/markets/physical",

        "/api/markets/announcements",

        "/api/offers",

        "/api/offers/physical",

        "/api/physical/offers",

        "/api/market/announcements",

        "/api/market/physical/announcements",

    ]

    for path in endpoints:

        url = urljoin(
            BASE_URL,
            path
        )

        print("\n")
        print("-" * 70)

        print(
            "TEST:",
            path
        )

        try:

            response = requests.get(
                url,
                params={
                    "limit": 5
                },
                headers=HEADERS,
                timeout=15
            )

            print(
                "STATUS:",
                response.status_code
            )

            print(
                "TYPE:",
                response.headers.get(
                    "content-type"
                )
            )

            print(
                "SIZE:",
                len(response.content)
            )

            if response.status_code == 200:

                try:

                    data = response.json()

                    if isinstance(
                        data,
                        dict
                    ):

                        print(
                            "KEYS:",
                            list(data.keys())[:30]
                        )

                        items = data.get(
                            "data",
                            []
                        )

                        print(
                            "DATA RECORDS:",
                            len(items)
                        )

                        if items:

                            first = items[0]

                            print(
                                "FIRST DATE:",
                                first.get(
                                    "offerDate"
                                )
                            )

                            print(
                                "FIRST PRODUCT:",
                                first.get(
                                    "productName"
                                )
                            )

                            print(
                                "FIRST KEYS:",
                                list(first.keys())[:50]
                            )

                    else:

                        print(
                            "JSON TYPE:",
                            type(data).__name__
                        )

                except Exception:

                    print(
                        "RESPONSE:",
                        response.text[:500]
                    )

        except Exception as e:

            print(
                "ERROR:",
                e
            )


# =========================================================
# تست مخصوص رکوردهای فولادی
# =========================================================

def test_steel_records():

    print("\n")
    print("=" * 70)
    print("SEARCH STEEL RECORDS IN RETURNED DATA")
    print("=" * 70)

    data = get_json(
        CURRENT_API,
        params={
            "limit": 100
        }
    )

    if not data:

        print("❌ DATA NOT FOUND")

        return

    items = data.get(
        "data",
        []
    )

    print(
        "TOTAL RECORDS:",
        len(items)
    )

    steel_keywords = [

        "فولاد",
        "میلگرد",
        "ورق",
        "تیرآهن",
        "نبشی",
        "ناودانی",
        "شمش",
        "بلوم",
        "بیلت",
        "اسلب",
        "آهن",
        "گندله",
        "کنسانتره",
        "مقاطع",
        "لوله",

    ]

    found = []

    for item in items:

        product = str(
            item.get(
                "productName",
                ""
            )
        )

        producer = str(
            item.get(
                "producer",
                ""
            )
        )

        supplier = str(
            item.get(
                "supplier",
                ""
            )
        )

        text = (
            product
            + " "
            + producer
            + " "
            + supplier
        )

        if any(
            keyword in text
            for keyword in steel_keywords
        ):

            found.append(
                item
            )

    print(
        "\nSTEEL-LIKE RECORDS:",
        len(found)
    )

    for index, item in enumerate(
        found,
        1
    ):

        print("\n")
        print("-" * 70)

        print(
            index,
            "|",
            item.get("offerDate"),
            "|",
            item.get("offerCode")
        )

        print(
            "PRODUCT:",
            item.get("productName")
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
            "HALL:",
            item.get("hall")
        )

        print(
            "VOLUME:",
            item.get("availableVolume")
        )

        print(
            "PRICE:",
            item.get("basePrice")
        )

        print(
            "STATUS:",
            item.get("status")
        )


# =========================================================
# ذخیره گزارش کامل
# =========================================================

def save_report(data=None):

    report = {

        "test":
            "iBrokers API discovery",

        "base_url":
            BASE_URL,

        "current_api":
            CURRENT_API,

        "timestamp":
            datetime.utcnow().isoformat(),

        "data":
            data,

    }

    with open(
        "api_test_report.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\n")
    print(
        "✅ api_test_report.json ساخته شد."
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n")
    print("=" * 70)

    print(
        "iBROKERS API DISCOVERY - DEEP TEST"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # API اصلی
    # -----------------------------------------------------

    current_data = test_current_api()

    # -----------------------------------------------------
    # Pagination
    # -----------------------------------------------------

    test_pagination()

    # -----------------------------------------------------
    # Sort
    # -----------------------------------------------------

    test_sort_parameters()

    # -----------------------------------------------------
    # Date
    # -----------------------------------------------------

    test_date_parameters()

    # -----------------------------------------------------
    # Filters
    # -----------------------------------------------------

    test_filter_parameters()

    # -----------------------------------------------------
    # Steel
    # -----------------------------------------------------

    test_steel_records()

    # -----------------------------------------------------
    # Endpoints
    # -----------------------------------------------------

    test_possible_endpoints()

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_report(
        current_data
    )

    print("\n")
    print("=" * 70)

    print(
        "TEST FINISHED"
    )

    print("=" * 70)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()