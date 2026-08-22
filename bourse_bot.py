import requests
import json
from urllib.parse import urljoin


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
# تبدیل اعداد
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
# درخواست GET
# =========================================================

def get_json(url, params=None):

    try:

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        print("URL:", response.url)
        print("STATUS:", response.status_code)
        print("SIZE:", len(response.content))
        print(
            "CONTENT-TYPE:",
            response.headers.get("content-type")
        )

        if response.status_code != 200:
            return None

        try:
            return response.json()

        except Exception:
            return None

    except Exception as e:

        print("ERROR:", e)

        return None


# =========================================================
# تست API فعلی
# =========================================================

def test_current_api():

    print("\n" + "=" * 70)
    print("CURRENT API")
    print("=" * 70)

    data = get_json(
        CURRENT_API,
        params={
            "limit": 10
        }
    )

    if not data:

        print("❌ پاسخی دریافت نشد.")

        return

    items = data.get("data", [])

    print("SUCCESS:", data.get("success"))
    print("RECORDS:", len(items))

    if items:

        print("\nFIRST RECORD:")

        print(
            json.dumps(
                items[0],
                ensure_ascii=False,
                indent=2
            )
        )


# =========================================================
# تست پارامترهای تاریخ
# =========================================================

def test_date_parameters():

    print("\n" + "=" * 70)
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

        print("\n" + "-" * 70)

        print("PARAMS:")
        print(params)

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

            first = items[0]
            last = items[-1]

            print(
                "FIRST:",
                first.get("offerDate"),
                first.get("offerCode"),
                first.get("productName")
            )

            print(
                "LAST:",
                last.get("offerDate"),
                last.get("offerCode"),
                last.get("productName")
            )


# =========================================================
# تست پارامترهای فیلتر
# =========================================================

def test_filter_parameters():

    print("\n" + "=" * 70)
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

    ]

    for params in tests:

        print("\n" + "-" * 70)

        print("PARAMS:")
        print(params)

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


# =========================================================
# تست endpointهای احتمالی
# =========================================================

def test_possible_endpoints():

    print("\n" + "=" * 70)
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

        print("\n" + "-" * 70)

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

                    if isinstance(data, dict):

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

                            print(
                                "FIRST DATE:",
                                items[0].get(
                                    "offerDate"
                                )
                            )

                            print(
                                "FIRST PRODUCT:",
                                items[0].get(
                                    "productName"
                                )
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
# ذخیره گزارش
# =========================================================

def save_report():

    report = {

        "test": "iBrokers API discovery",

        "base_url": BASE_URL,

        "current_api": CURRENT_API,

        "timestamp": __import__(
            "datetime"
        ).datetime.utcnow().isoformat(),

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

    print(
        "\n✅ api_test_report.json ساخته شد."
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n")

    print("=" * 70)

    print(
        "iBROKERS API DISCOVERY"
    )

    print("=" * 70)

    # -----------------------------------------------------
    # API فعلی
    # -----------------------------------------------------

    test_current_api()

    # -----------------------------------------------------
    # تست تاریخ
    # -----------------------------------------------------

    test_date_parameters()

    # -----------------------------------------------------
    # تست فیلترها
    # -----------------------------------------------------

    test_filter_parameters()

    # -----------------------------------------------------
    # تست endpointهای احتمالی
    # -----------------------------------------------------

    test_possible_endpoints()

    # -----------------------------------------------------
    # گزارش
    # -----------------------------------------------------

    save_report()

    print("\n" + "=" * 70)

    print(
        "TEST FINISHED"
    )

    print("=" * 70)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    main()