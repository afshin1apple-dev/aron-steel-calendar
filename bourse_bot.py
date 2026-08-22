import requests

URL = "https://www.ime.co.ir/offer-stat.html"

def main():

    print("در حال اتصال به بورس کالا...")

    try:
        response = requests.get(
            URL,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        print("Status:", response.status_code)
        print("Size:", len(response.text))

        print("\n--- شروع اطلاعات دریافت شده ---\n")

        print(response.text[:3000])

        print("\n--- پایان تست ---")

    except Exception as e:

        print("ERROR:", e)


if __name__ == "__main__":
    main()