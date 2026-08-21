import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

URLS = [
    "https://khorasan-steel.com/product.php?prd=5",
    "https://khorasan-steel.com/product.php?prd=3",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
}

KEYWORDS = [
    "price",
    "price2",
    "today",
    "yesterday",
    "ajax",
    "product",
    "prd",
    "قیمت",
    "امروز",
    "دیروز",
    "میلگرد",
]

def clean(text):
    return re.sub(r"\s+", " ", text).strip()

def show_matches(label, text):
    print("\n---", label, "---")

    lines = text.splitlines()
    found = 0

    for i, line in enumerate(lines):
        line_clean = clean(line)

        if not line_clean:
            continue

        lower = line_clean.lower()

        if any(keyword.lower() in lower for keyword in KEYWORDS):
            print(line_clean[:1000])
            found += 1

            if found >= 80:
                print("... more matches omitted ...")
                break

    print("MATCHES:", found)

for url in URLS:

    print("\n" + "=" * 80)
    print("CHECKING:", url)
    print("=" * 80)

    try:
        session = requests.Session()

        response = session.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        print("HTTP STATUS:", response.status_code)
        print("FINAL URL:", response.url)
        print("CONTENT TYPE:", response.headers.get("content-type"))
        print("HTML LENGTH:", len(response.text))

        if response.status_code != 200:
            print("❌ PAGE FAILED")
            continue

        html = response.text

        soup = BeautifulSoup(html, "html.parser")

        # -------------------------------------------------
        # 1. لینک‌ها
        # -------------------------------------------------

        print("\n" + "-" * 60)
        print("LINKS")
        print("-" * 60)

        links_found = set()

        for a in soup.find_all("a", href=True):

            href = a.get("href", "").strip()

            if not href:
                continue

            full_url = urljoin(response.url, href)

            text = clean(a.get_text(" ", strip=True))

            combined = (text + " " + href).lower()

            if any(k.lower() in combined for k in KEYWORDS):

                item = f"{text} => {full_url}"

                if item not in links_found:
                    links_found.add(item)
                    print(item)

        # -------------------------------------------------
        # 2. فرم‌ها
        # -------------------------------------------------

        print("\n" + "-" * 60)
        print("FORMS")
        print("-" * 60)

        for form in soup.find_all("form"):

            print(
                "FORM:",
                clean(str(form))[:2000]
            )

        # -------------------------------------------------
        # 3. Script ها
        # -------------------------------------------------

        print("\n" + "-" * 60)
        print("SCRIPTS")
        print("-" * 60)

        scripts = soup.find_all("script")

        print("SCRIPT COUNT:", len(scripts))

        for index, script in enumerate(scripts):

            src = script.get("src")

            if src:
                full_src = urljoin(response.url, src)

                print(
                    f"SCRIPT {index + 1}:",
                    full_src
                )

            else:

                content = script.get_text()

                lower = content.lower()

                if any(k.lower() in lower for k in KEYWORDS):

                    print(
                        f"\nINLINE SCRIPT {index + 1}:"
                    )

                    print(
                        clean(content)[:5000]
                    )

        # -------------------------------------------------
        # 4. درخواست‌های AJAX داخل HTML
        # -------------------------------------------------

        print("\n" + "-" * 60)
        print("AJAX / API CANDIDATES")
        print("-" * 60)

        patterns = [
            r"""url\s*:\s*["']([^"']+)["']""",
            r"""href\s*=\s*["']([^"']+)["']""",
            r"""fetch\s*\(\s*["']([^"']+)["']""",
            r"""ajax\s*\([^)]*url\s*:\s*["']([^"']+)["']""",
            r"""["']([^"']*(?:ajax|api|price|product)[^"']*)["']""",
        ]

        candidates = set()

        for pattern in patterns:

            matches = re.findall(
                pattern,
                html,
                flags=re.IGNORECASE
            )

            for match in matches:

                full = urljoin(response.url, match)

                candidates.add(full)

        if candidates:

            for candidate in sorted(candidates):
                print(candidate)

        else:

            print("No obvious AJAX/API URL found.")

        # -------------------------------------------------
        # 5. کلمات مرتبط با قیمت
        # -------------------------------------------------

        show_matches(
            "PRICE RELATED HTML",
            html
        )

        # -------------------------------------------------
        # 6. اعداد بزرگ موجود در HTML
        # -------------------------------------------------

        print("\n" + "-" * 60)
        print("NUMERIC DATA CANDIDATES")
        print("-" * 60)

        numbers = re.findall(
            r"(?<!\d)\d{4,8}(?!\d)",
            html
        )

        unique_numbers = []

        for number in numbers:

            if number not in unique_numbers:
                unique_numbers.append(number)

        for number in unique_numbers[:150]:

            print(number)

        print(
            "\nTOTAL UNIQUE NUMBERS:",
            len(unique_numbers)
        )

        print("\nDONE:", url)

    except Exception as e:

        print("\n❌ ERROR:")
        print(type(e).__name__, str(e))

print("\n" + "=" * 80)
print("PRICE SOURCE INVESTIGATION FINISHED")
print("=" * 80)