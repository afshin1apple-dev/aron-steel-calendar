import requests

URL = "https://www.ibrokers.ir/api/announcements"

for page in range(23417, 23412, -1):
    try:
        r = requests.get(
            URL,
            params={"page": page, "limit": 10},
            timeout=30
        )

        data = r.json()
        records = data.get("data", [])

        print("\n" + "=" * 60)
        print("PAGE:", page)
        print("RECORDS:", len(records))

        for x in records:
            print(
                x.get("date"),
                "|",
                x.get("offer_code"),
                "|",
                x.get("product"),
                "|",
                x.get("hall")
            )

    except Exception as e:
        print("ERROR:", e)