from playwright.sync_api import sync_playwright
import re

URLS = {
    "میلگرد سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "میلگرد نیشابور": "https://khorasan-steel.com/product.php?prd=3",
}

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page(
        locale="fa-IR"
    )

    for title, url in URLS.items():

        print("\n" + "=" * 90)
        print(title)
        print(url)
        print("=" * 90)

        try:

            page.goto(
                url,
                wait_until="networkidle",
                timeout=60000
            )

            page.wait_for_timeout(5000)

            print("PAGE TITLE:", page.title())
            print("FINAL URL:", page.url)

            html = page.content()

            print("DOM LENGTH:", len(html))

            print("\n--- TEXT CONTAINING PRICE ---")

            text = page.locator("body").inner_text()

            lines = text.splitlines()

            found = 0

            for line in lines:

                line = re.sub(
                    r"\s+",
                    " ",
                    line
                ).strip()

                if not line:
                    continue

                if (
                    "قیمت" in line
                    or "ریال" in line
                    or re.search(r"\d{5,}", line)
                ):

                    print(line[:1000])

                    found += 1

                    if found >= 150:
                        break

            print("\nFOUND:", found)

            print("\n--- INPUTS ---")

            inputs = page.locator("input")

            print(
                "INPUT COUNT:",
                inputs.count()
            )

            for i in range(inputs.count()):

                el = inputs.nth(i)

                print(
                    i,
                    el.get_attribute("name"),
                    el.get_attribute("value"),
                    el.get_attribute("type")
                )

            print("\n--- TABLE COUNT ---")

            print(
                "TABLES:",
                page.locator("table").count()
            )

            print(
                "ROWS:",
                page.locator("tr").count()
            )

            print("\n--- PRICE KEYWORDS ---")

            for keyword in [
                "قیمت امروز",
                "قیمت دیروز",
                "میلگرد",
                "نیشابور",
                "اصفهان",
                "شاهین بناب",
                "ظفر بناب"
            ]:

                count = text.count(keyword)

                if count:
                    print(
                        keyword,
                        "=>",
                        count
                    )

        except Exception as e:

            print(
                "ERROR:",
                type(e).__name__,
                str(e)
            )

    browser.close()

print("\n" + "=" * 90)
print("BROWSER PRICE TEST FINISHED")
print("=" * 90)