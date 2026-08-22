import requests

BASE_URL = "https://www.ibrokers.ir"

def test_api(path):

    print("\n==============================")
    print("TEST:", path)
    print("==============================")

    try:

        response = requests.get(
            BASE_URL + path,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            },
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("CONTENT-TYPE:", response.headers.get("content-type"))
        print("SIZE:", len(response.content))

        print("\n--- DATA ---")
        print(response.text[:10000])

    except Exception as e:

        print("ERROR:", e)


def main():

    test_api("/api/bazaar-stats")
    test_api("/api/landing-stats")


if __name__ == "__main__":
    main()