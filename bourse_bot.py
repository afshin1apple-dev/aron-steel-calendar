import requests

URL = "https://www.ibrokers.ir/"

def main():
    print("در حال تست منبع بورس کالا...")

    try:
        response = requests.get(
            URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("SIZE:", len(response.content))
        print("CONTENT-TYPE:", response.headers.get("content-type"))

        print("\n--- RESPONSE ---")
        print(response.text[:5000])

    except Exception as e:
        print("ERROR:", e)


if __name__ == "__main__":
    main()