import requests
import re
import json
from html import unescape
from datetime import datetime, timezone
from urllib.parse import urljoin


URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://khorasan-steel.com/product.php?prd=3",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


session = requests.Session()
session.headers.update(HEADERS)


def clean(text):
    if text is None:
        return ""

    text = unescape(str(text))
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    text = text.replace("&nbsp;", " ")

    return " ".join(text.split()).strip()


def price_value(text):
    text = clean(text)

    if text in ("", "-", "—", "–", "null", "None"):
        return None

    digits = re.sub(r"[^\d]", "", text)

    if not digits:
        return None

    try:
        return int(digits)
    except Exception:
        return None


def extract_table_rows(html):

    rows = re.findall(
        r"<tr\b[^>]*>(.*?)</tr>",
        html,
        flags=re.I | re.S
    )

    result = []

    for row in rows:

        cells = re.findall(
            r"<td\b[^>]*>(.*?)</td>",
            row,
            flags=re.I | re.S
        )

        values = [clean(x) for x in cells]

        if len(values) == 5:
            result.append(values)

    return result


def extract_products(html, source_page):

    rows = extract_table_rows(html)

    products = []

    for values in rows:

        factory = clean(values[0])
        size = clean(values[1])
        yesterday = clean(values[2])
        today = clean(values[3])
        description = clean(values[4])

        if not factory or not size:
            continue

        if "قیمت دیروز" in yesterday:
            continue

        if "قیمت امروز" in today:
            continue

        if factory == "میلگرد":
            continue

        if "قیمت ها با احتساب" in factory:
            continue

        old_price = price_value(yesterday)
        new_price = price_value(today)

        products.append({
            "factory": factory,
            "size": size,
            "yesterday": old_price,
            "today": new_price,
            "description": description,
            "source_page": source_page
        })

    return products


def extract_urls_from_html(html, base_url):

    found = []

    # href
    hrefs = re.findall(
        r"""href\s*=\s*["']([^"']+)["']""",
        html,
        flags=re.I
    )

    # src
    srcs = re.findall(
        r"""src\s*=\s*["']([^"']+)["']""",
        html,
        flags=re.I
    )

    # URLهای داخل JavaScript
    js_urls = re.findall(
        r"""["']([^"']*(?:ajax|api|price|product|archive|load)[^"']*)["']""",
        html,
        flags=re.I
    )

    for url in hrefs + srcs + js_urls:

        url = unescape(url).strip()

        if not url:
            continue

        if url.startswith("#"):
            continue

        full_url = urljoin(base_url, url)

        if full_url not in found:
            found.append(full_url)

    return found


def find_ajax_candidates(html, base_url):

    candidates = []

    patterns = [
        r"""url\s*:\s*["']([^"']+)["']""",
        r"""url\s*=\s*["']([^"']+)["']""",
        r"""["']([^"']*ajax[^"']*)["']""",
        r"""["']([^"']*product[^"']*)["']""",
        r"""["']([^"']*price[^"']*)["']""",
        r"""["']([^"']*archive[^"']*)["']""",
        r"""["']([^"']*load[^"']*)["']""",
        r"""["']([^"']*prd=[^"']*)["']""",
    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            flags=re.I
        )

        for match in matches:

            match = unescape(match).strip()

            if not match:
                continue

            full_url = urljoin(base_url, match)

            if full_url not in candidates:
                candidates.append(full_url)

    return candidates


def inspect_nishabour_page(html, url):

    print()
    print("=" * 70)
    print("NISHABOUR PAGE ANALYSIS")
    print("=" * 70)

    print("HTML LENGTH:", len(html))

    # -----------------------------------------
    # پیدا کردن URLهای احتمالی
    # -----------------------------------------

    candidates = find_ajax_candidates(
        html,
        url
    )

    print()
    print("POSSIBLE AJAX/API URLS:")

    for item in candidates[:50]:
        print(item)

    # -----------------------------------------
    # پیدا کردن scriptها
    # -----------------------------------------

    scripts = re.findall(
        r"<script\b[^>]*>(.*?)</script>",
        html,
        flags=re.I | re.S
    )

    print()
    print("INLINE SCRIPTS:", len(scripts))

    keywords = [
        "ajax",
        "$.get",
        "$.post",
        "xmlhttp",
        "fetch(",
        "axios",
        "price",
        "product",
        "archive",
        "prd",
        "load("
    ]

    interesting = []

    for script in scripts:

        lower = script.lower()

        if any(k.lower() in lower for k in keywords):

            text = clean(script)

            if text:
                interesting.append(text)

    print(
        "INTERESTING SCRIPTS:",
        len(interesting)
    )

    for index, script in enumerate(
        interesting[:20],
        start=1
    ):

        print()
        print(
            f"--- SCRIPT {index} ---"
        )

        print(
            script[:4000]
        )

    # -----------------------------------------
    # پیدا کردن فایل‌های JS
    # -----------------------------------------

    js_files = re.findall(
        r"""<script[^>]+src\s*=\s*["']([^"']+)["']""",
        html,
        flags=re.I
    )

    print()
    print("JS FILES:")

    for js in js_files[:50]:

        full = urljoin(
            url,
            unescape(js)
        )

        print(full)

    return candidates


def try_json_response(
    response,
    source_page
):

    text = response.text.strip()

    if not text:
        return []

    # -----------------------------------------
    # JSON مستقیم
    # -----------------------------------------

    try:

        data = response.json()

        products = parse_json_products(
            data,
            source_page
        )

        if products:
            return products

    except Exception:
        pass

    # -----------------------------------------
    # JSON داخل HTML
    # -----------------------------------------

    json_blocks = re.findall(
        r"""(?:\{.*?\}|\[.*?\])""",
        text,
        flags=re.S
    )

    for block in json_blocks:

        try:

            data = json.loads(block)

            products = parse_json_products(
                data,
                source_page
            )

            if products:
                return products

        except Exception:
            continue

    return []


def parse_json_products(
    data,
    source_page
):

    products = []

    def walk(obj):

        if isinstance(obj, dict):

            keys = {
                str(k).lower()
                for k in obj.keys()
            }

            # کلیدهای احتمالی
            factory_key = None
            size_key = None
            old_key = None
            new_key = None
            desc_key = None

            for k in obj.keys():

                lk = str(k).lower()

                if any(
                    x in lk
                    for x in [
                        "factory",
                        "brand",
                        "company",
                        "کارخانه",
                        "میلگرد"
                    ]
                ):
                    factory_key = k

                if any(
                    x in lk
                    for x in [
                        "size",
                        "saz",
                        "سایز"
                    ]
                ):
                    size_key = k

                if any(
                    x in lk
                    for x in [
                        "yesterday",
                        "old",
                        "prev",
                        "دیروز"
                    ]
                ):
                    old_key = k

                if any(
                    x in lk
                    for x in [
                        "today",
                        "new",
                        "current",
                        "امروز"
                    ]
                ):
                    new_key = k

                if any(
                    x in lk
                    for x in [
                        "description",
                        "desc",
                        "توضیحات"
                    ]
                ):
                    desc_key = k

            if factory_key and size_key:

                factory = clean(
                    obj.get(factory_key)
                )

                size = clean(
                    obj.get(size_key)
                )

                old_price = (
                    price_value(
                        obj.get(old_key)
                    )
                    if old_key
                    else None
                )

                new_price = (
                    price_value(
                        obj.get(new_key)
                    )
                    if new_key
                    else None
                )

                description = (
                    clean(
                        obj.get(desc_key)
                    )
                    if desc_key
                    else ""
                )

                if (
                    factory
                    and size
                    and (
                        old_price is not None
                        or new_price is not None
                    )
                ):

                    products.append({
                        "factory": factory,
                        "size": size,
                        "yesterday": old_price,
                        "today": new_price,
                        "description": description,
                        "source_page": source_page
                    })

            for value in obj.values():
                walk(value)

        elif isinstance(obj, list):

            for item in obj:
                walk(item)

    walk(data)

    return products


def fetch_page(title, url):

    print()
    print("=" * 70)
    print(title)
    print(url)
    print("=" * 70)

    try:

        response = session.get(
            url,
            timeout=30
        )

        print(
            "HTTP:",
            response.status_code
        )

        print(
            "LENGTH:",
            len(response.text)
        )

        response.raise_for_status()

        return response.text

    except Exception as e:

        print(
            "ERROR:",
            e
        )

        return ""


def fetch_nishabour_data(html, url):

    print()
    print("=" * 70)
    print("TRYING NISHABOUR DATA")
    print("=" * 70)

    all_products = []

    # -----------------------------------------
    # روش 1: جدول مستقیم
    # -----------------------------------------

    products = extract_products(
        html,
        "میلگرد نیشابور"
    )

    if products:

        print(
            "TABLE PRODUCTS:",
            len(products)
        )

        all_products.extend(
            products
        )

    # -----------------------------------------
    # روش 2: JSON موجود در HTML
    # -----------------------------------------

    products = try_json_response(
        requests.models.Response(),
        "میلگرد نیشابور"
    )

    # -----------------------------------------
    # تحلیل صفحه
    # -----------------------------------------

    candidates = inspect_nishabour_page(
        html,
        url
    )

    # -----------------------------------------
    # امتحان کردن URLهای احتمالی
    # -----------------------------------------

    tested = set()

    for candidate in candidates:

        if candidate in tested:
            continue

        tested.add(candidate)

        # فقط URLهای مربوط به سایت
        if "khorasan-steel.com" not in candidate:
            continue

        try:

            print()
            print(
                "TRY:",
                candidate
            )

            response = session.get(
                candidate,
                timeout=20,
                headers={
                    **HEADERS,
                    "Referer": url
                }
            )

            print(
                "HTTP:",
                response.status_code,
                "LENGTH:",
                len(response.text)
            )

            if response.status_code != 200:
                continue

            # جدول
            found = extract_products(
                response.text,
                "میلگرد نیشابور"
            )

            if found:

                print(
                    "TABLE FOUND:",
                    len(found)
                )

                all_products.extend(
                    found
                )

            # JSON
            try:

                data = response.json()

                found = parse_json_products(
                    data,
                    "میلگرد نیشابور"
                )

                if found:

                    print(
                        "JSON FOUND:",
                        len(found)
                    )

                    all_products.extend(
                        found
                    )

            except Exception:
                pass

        except Exception as e:

            print(
                "REQUEST ERROR:",
                e
            )

    return all_products


def remove_duplicates(products):

    unique = []
    seen = set()

    for product in products:

        key = (
            product["factory"],
            product["size"],
            product["yesterday"],
            product["today"],
            product["description"],
            product["source_page"]
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(product)

    return unique


def main():

    all_products = []

    page_counts = {}

    # ==================================================
    # سایر کارخانجات
    # ==================================================

    html = fetch_page(
        "میلگرد سایر کارخانجات",
        URLS["میلگرد سایر کارخانجات"]
    )

    if html:

        products = extract_products(
            html,
            "میلگرد سایر کارخانجات"
        )

        print(
            "FOUND:",
            len(products)
        )

        page_counts[
            "میلگرد سایر کارخانجات"
        ] = len(products)

        all_products.extend(
            products
        )

    else:

        page_counts[
            "میلگرد سایر کارخانجات"
        ] = 0

    # ==================================================
    # نیشابور
    # ==================================================

    html = fetch_page(
        "میلگرد نیشابور",
        URLS["میلگرد نیشابور"]
    )

    if html:

        products = fetch_nishabour_data(
            html,
            URLS["میلگرد نیشابور"]
        )

        print()
        print(
            "NISHABOUR FOUND:",
            len(products)
        )

        page_counts[
            "میلگرد نیشابور"
        ] = len(products)

        all_products.extend(
            products

        )

    else:

        page_counts[
            "میلگرد نیشابور"
        ] = 0

    # ==================================================
    # حذف تکراری
    # ==================================================

    all_products = remove_duplicates(
        all_products
    )

    # ==================================================
    # ساخت JSON
    # ==================================================

    data = {
        "source": "khorasan-steel.com",
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "count": len(all_products),
        "prices": all_products
    }

    with open(
        "prices.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    # ==================================================
    # نتیجه
    # ==================================================

    print()
    print("=" * 70)
    print("JSON CREATED")
    print("=" * 70)

    print(
        "FILE: prices.json"
    )

    print(
        "TOTAL PRODUCTS:",
        len(all_products)
    )

    print()
    print(
        "COUNT BY PAGE:"
    )

    for page, count in page_counts.items():

        print(
            f"{page}: {count}"
        )

    print()
    print("=" * 70)
    print("SAMPLE")
    print("=" * 70)

    for product in all_products[:15]:

        print(
            f"{product['factory']} | "
            f"سایز {product['size']} | "
            f"امروز {product['today']} | "
            f"{product['description']}"
        )

    print()
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()