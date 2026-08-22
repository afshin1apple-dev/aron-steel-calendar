import requests
import json

URL = "https://www.ibrokers.ir/api/announcements"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.ibrokers.ir/markets/physical/announcement",
}


def test(params):

    print("\n" + "=" * 70)
    print("PARAMS:")
    print(params)

    try:

        r = requests.get(
            URL,
            params=params,
            headers=HEADERS,
            timeout=30
        )

        print("URL:")
        print(r.url)

        print("STATUS:", r.status_code)
        print("SIZE:", len(r.content))

        if r.status_code != 200:
            print(r.text[:500])
            return

        data = r.json()

        print("\nPAGINATION:")
        print(
            json.dumps(
                data.get("pagination"),
                ensure_ascii=False,
                indent=2
            )
        )

        print("\nFILTERS:")
        print(
            json.dumps(
                data.get("filters"),
                ensure_ascii=False,
                indent=2
            )
        )

        items = data.get("data", [])

        print("\nRECORDS:", len(items))

        for i, item in enumerate(items[:10], 1):

            print(
                f"{i}. "
                f"DATE={item.get('offerDate')} | "
                f"CODE={item.get('offerCode')} | "
                f"PRODUCT={item.get('productName')} | "
                f"HALL={item.get('hall')}"
            )

    except Exception as e:

        print("ERROR:", repr(e))


def main():

    print("=" * 70)
    print("iBROKERS DATE + PAGINATION DISCOVERY")
    print("=" * 70)

    # -----------------------------------------------------
    # تست 1 - همان چیزی که الان داریم
    # -----------------------------------------------------

    test({
        "limit": 10,
        "start_date": "1405/08/01",
        "end_date": "1405/08/31"
    })

    # -----------------------------------------------------
    # تست 2 - سال 1401 که می دانیم داده دارد
    # -----------------------------------------------------

    test({
        "limit": 10,
        "start_date": "1401/07/01",
        "end_date": "1401/07/31"
    })

    # -----------------------------------------------------
    # تست 3 - فقط start_date
    # -----------------------------------------------------

    test({
        "limit": 10,
        "start_date": "1401/07/01"
    })

    # -----------------------------------------------------
    # تست 4 - فقط end_date
    # -----------------------------------------------------

    test({
        "limit": 10,
        "end_date": "1401/07/31"
    })

    # -----------------------------------------------------
    # تست 5 - صفحه 1
    # -----------------------------------------------------

    test({
        "page": 1,
        "limit": 10
    })

    # -----------------------------------------------------
    # تست 6 - صفحه 2
    # -----------------------------------------------------

    test({
        "page": 2,
        "limit": 10
    })

    # -----------------------------------------------------
    # تست 7 - صفحه 100
    # -----------------------------------------------------

    test({
        "page": 100,
        "limit": 10
    })

    print("\n" + "=" * 70)
    print("FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()