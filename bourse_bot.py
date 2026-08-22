import requests
import json


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
    "Referer": f"{BASE_URL}/markets/physical/announcement",
}


# =========================================================
# دریافت API
# =========================================================

def get_data(params):

    print("\n" + "-" * 70)
    print("PARAMS:")
    print(params)

    try:

        r = requests.get(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        print("URL:", r.url)
        print("STATUS:", r.status_code)
        print("SIZE:", len(r.content))

        if r.status_code != 200:
            return None

        data = r.json()

        items = data.get("data", [])
        pagination = data.get("pagination", {})
        filters = data.get("filters", {})

        print("RECORDS:", len(items))

        print("\nPAGINATION:")
        print(
            json.dumps(
                pagination,
                ensure_ascii=False,
                indent=2
            )
        )

        print("\nFILTERS:")
        print(
            json.dumps(
                filters,
                ensure_ascii=False,
                indent=2
            )
        )

        if items:

            print("\nFIRST 5 RECORDS:")

            for i, item in enumerate(items[:5], 1):

                print(
                    f"{i}. "
                    f"{item.get('offerDate')} | "
                    f"{item.get('productName')} | "
                    f"{item.get('hall')} | "
                    f"{item.get('producer')}"
                )

        return data

    except Exception as e:

        print("ERROR:", e)

        return None


# =========================================================
# 1. تست Pagination
# =========================================================

def test_pagination():

    print("\n")
    print("=" * 70)
    print("1 - PAGINATION TEST")
    print("=" * 70)

    tests = [

        {
            "page": 1,
            "limit": 5
        },

        {
            "page": 2,
            "limit": 5
        },

        {
            "page": 10,
            "limit": 5
        },

        {
            "page": 100,
            "limit": 5
        },

    ]

    for params in tests:

        data = get_data(params)

        if not data:
            continue


# =========================================================
# 2. تست تاریخ واقعی API
# =========================================================

def test_real_date_filters():

    print("\n")
    print("=" * 70)
    print("2 - REAL DATE FILTER TEST")
    print("=" * 70)

    tests = [

        {
            "limit": 10,
            "start_date": "1405/08/01",
            "end_date": "1405/08/31"
        },

        {
            "limit": 10,
            "start_date": "1405-08-01",
            "end_date": "1405-08-31"
        },

        {
            "limit": 10,
            "start_date": "14050801",
            "end_date": "14050831"
        },

        {
            "limit": 10,
            "start_date": "1405/08/20",
            "end_date": "1405/08/31"
        },

    ]

    for params in tests:

        get_data(params)


# =========================================================
# 3. تست market_type
# =========================================================

def test_market_type():

    print("\n")
    print("=" * 70)
    print("3 - MARKET TYPE TEST")
    print("=" * 70)

    values = [

        "physical",
        "فیزیکی",
        "physical_market",
        "1",
        "2",
        "3",

    ]

    for value in values:

        params = {
            "limit": 10,
            "market_type": value
        }

        get_data(params)


# =========================================================
# 4. تست main_group
# =========================================================

def test_main_group():

    print("\n")
    print("=" * 70)
    print("4 - MAIN GROUP TEST")
    print("=" * 70)

    values = [

        "فولاد",
        "صنعتی",
        "فلزات",
        "1",
        "2",
        "3",

    ]

    for value in values:

        params = {
            "limit": 10,
            "main_group": value
        }

        get_data(params)


# =========================================================
# 5. تست group
# =========================================================

def test_group():

    print("\n")
    print("=" * 70)
    print("5 - GROUP TEST")
    print("=" * 70)

    values = [

        "فولاد",
        "محصولات فولادی",
        "میلگرد",
        "تیرآهن",
        "ورق",
        "آهن اسفنجی",

    ]

    for value in values:

        params = {
            "limit": 10,
            "group": value
        }

        get_data(params)


# =========================================================
# 6. تست sub_group
# =========================================================

def test_sub_group():

    print("\n")
    print("=" * 70)
    print("6 - SUB GROUP TEST")
    print("=" * 70)

    values = [

        "میلگرد",
        "تیرآهن",
        "ورق",
        "آهن اسفنجی",
        "شمش",

    ]

    for value in values:

        params = {
            "limit": 10,
            "sub_group": value
        }

        get_data(params)


# =========================================================
# 7. تست SEARCH
# =========================================================

def test_search():

    print("\n")
    print("=" * 70)
    print("7 - SEARCH TEST")
    print("=" * 70)

    values = [

        "فولاد",
        "میلگرد",
        "تیرآهن",
        "شمش",
        "آهن اسفنجی",
        "ورق",

    ]

    for value in values:

        params = {
            "limit": 10,
            "search": value
        }

        get_data(params)


# =========================================================
# 8. تست ترکیبی
# =========================================================

def test_combined():

    print("\n")
    print("=" * 70)
    print("8 - COMBINED FILTER TEST")
    print("=" * 70)

    tests = [

        {
            "page": 1,
            "limit": 20,
            "start_date": "1405/08/01",
            "end_date": "1405/08/31",
            "search": "فولاد"
        },

        {
            "page": 1,
            "limit": 20,
            "start_date": "1405/08/20",
            "end_date": "1405/08/31",
            "search": "میلگرد"
        },

        {
            "page": 1,
            "limit": 20,
            "start_date": "1405/08/20",
            "end_date": "1405/08/31",
            "search": "شمش"
        },

        {
            "page": 1,
            "limit": 20,
            "start_date": "1405/08/20",
            "end_date": "1405/08/31",
            "search": "آهن اسفنجی"
        },

    ]

    for params in tests:

        get_data(params)


# =========================================================
# MAIN
# =========================================================

def main():

    print("\n")
    print("=" * 70)
    print("iBROKERS REAL FILTER DISCOVERY")
    print("=" * 70)

    # 1
    test_pagination()

    # 2
    test_real_date_filters()

    # 3
    test_market_type()

    # 4
    test_main_group()

    # 5
    test_group()

    # 6
    test_sub_group()

    # 7
    test_search()

    # 8
    test_combined()

    print("\n")
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()