import requests
import re
import json

BASE_URL = "https://www.ibrokers.ir"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/139.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
              "application/json;q=0.8,*/*;q=0.7",
}


def get_page(path):
    print("\n" + "=" * 70)
    print("PAGE:", path)
    print("=" * 70)

    url = BASE_URL + path

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("CONTENT-TYPE:", response.headers.get("content-type"))
        print("SIZE:", len(response.content))

        return response.text

    except Exception as e:
        print("ERROR:", e)
        return ""


def find_api_urls(html):
    print("\n" + "=" * 70)
    print("SEARCHING FOR API URLS")
    print("=" * 70)

    patterns = [
        r'https?://[^"\']+/api/[^"\']+',
        r'["\'](/api/[^"\']+)["\']',
        r'["\'](api/[^"\']+)["\']',
    ]

    found = set()

    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)

        for item in matches:
            if item.startswith("/"):
                url = BASE_URL + item
            elif item.startswith("http"):
                url = item
            else:
                url = BASE_URL + "/" + item

            found.add(url)

    if not found:
        print("هیچ API مستقیمی داخل صفحه پیدا نشد.")
    else:
        print("API های پیدا شده:")

        for url in sorted(found):
            print(url)

    return sorted(found)


def find_js_files(html):
    print("\n" + "=" * 70)
    print("SEARCHING FOR JAVASCRIPT FILES")
    print("=" * 70)

    patterns = [
        r'<script[^>]+src=["\']([^"\']+)["\']',
    ]

    found = set()

    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)

        for item in matches:

            if item.startswith("http"):
                url = item

            elif item.startswith("/"):
                url = BASE_URL + item

            else:
                url = BASE_URL + "/" + item

            if ".js" in url.lower():
                found.add(url)

    for url in sorted(found):
        print(url)

    print("\nTOTAL JS FILES:", len(found))

    return sorted(found)


def search_api_inside_js(js_urls):
    print("\n" + "=" * 70)
    print("SEARCHING API INSIDE JAVASCRIPT")
    print("=" * 70)

    all_apis = set()

    for js_url in js_urls:

        print("\n----------------------------------------")
        print("JS:", js_url)
        print("----------------------------------------")

        try:

            response = requests.get(
                js_url,
                headers=HEADERS,
                timeout=30
            )

            print("STATUS:", response.status_code)
            print("SIZE:", len(response.content))

            if response.status_code != 200:
                continue

            text = response.text

            patterns = [
                r'https?://[^"\']+/api/[^"\']+',
                r'["\'](/api/[^"\']+)["\']',
                r'["\'](api/[^"\']+)["\']',
            ]

            for pattern in patterns:

                matches = re.findall(
                    pattern,
                    text,
                    re.IGNORECASE
                )

                for item in matches:

                    if item.startswith("/"):
                        url = BASE_URL + item

                    elif item.startswith("http"):
                        url = item

                    else:
                        url = BASE_URL + "/" + item

                    all_apis.add(url)

        except Exception as e:
            print("ERROR:", e)

    print("\n" + "=" * 70)
    print("ALL API URLS FOUND")
    print("=" * 70)

    if not all_apis:
        print("هیچ API پیدا نشد.")
    else:
        for url in sorted(all_apis):
            print(url)

    return sorted(all_apis)


def test_api(url):

    print("\n" + "=" * 70)
    print("TEST API:")
    print(url)
    print("=" * 70)

    try:

        response = requests.get(
            url,
            headers={
                "User-Agent": HEADERS["User-Agent"],
                "Accept": "application/json,text/plain,*/*"
            },
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("CONTENT-TYPE:", response.headers.get("content-type"))
        print("SIZE:", len(response.content))

        print("\n--- RESPONSE ---")

        print(response.text[:5000])

        return response

    except Exception as e:

        print("ERROR:", e)

        return None


def main():

    # صفحه اصلی اطلاعیه های عرضه
    page = get_page(
        "/markets/physical/announcement"
    )

    if not page:
        print("صفحه دریافت نشد.")
        return

    # API هایی که مستقیماً داخل HTML هستند
    api_urls = find_api_urls(page)

    # فایل های JavaScript صفحه
    js_urls = find_js_files(page)

    # API هایی که داخل JavaScript هستند
    js_api_urls = search_api_inside_js(js_urls)

    # ترکیب همه API ها
    all_api_urls = sorted(
        set(api_urls + js_api_urls)
    )

    print("\n" + "=" * 70)
    print("FINAL API LIST")
    print("=" * 70)

    for i, url in enumerate(all_api_urls, 1):
        print(f"{i}. {url}")

    # فقط API هایی که احتمالاً مربوط به عرضه هستند
    print("\n" + "=" * 70)
    print("POSSIBLE ANNOUNCEMENT APIs")
    print("=" * 70)

    keywords = [
        "announcement",
        "announce",
        "offer",
        "supply",
        "bazaar",
        "market",
        "physical",
        "commodity",
        "auction",
        "listing"
    ]

    possible = []

    for url in all_api_urls:

        low = url.lower()

        if any(
            keyword in low
            for keyword in keywords
        ):
            possible.append(url)

    if not possible:

        print("API مرتبط با عرضه از روی اسم پیدا نشد.")

    else:

        for url in possible:
            print(url)

    # تست API های احتمالی
    print("\n" + "=" * 70)
    print("TESTING POSSIBLE APIs")
    print("=" * 70)

    for url in possible:

        test_api(url)


if __name__ == "__main__":
    main()