import requests
import re

URL = "https://www.ibrokers.ir/"

def main():

    print("در حال پیدا کردن API بورس کالا...")

    try:

        response = requests.get(
            URL,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=30
        )

        html = response.text

        print("STATUS:", response.status_code)
        print("SIZE:", len(html))

        print("\n--- JAVASCRIPT FILES ---")

        scripts = re.findall(
            r'<script[^>]+src=["\']([^"\']+)["\']',
            html,
            re.I
        )

        for script in scripts:
            print(script)

        print("\n--- POSSIBLE API LINKS ---")

        for pattern in [
            r'https?://[^"\']+',
            r'/api/[^"\']+',
            r'/api/[^\'"]+'
        ]:

            matches = re.findall(
                pattern,
                html,
                re.I
            )

            for item in matches:
                print(item)

    except Exception as e:

        print("ERROR:", e)


if __name__ == "__main__":
    main()