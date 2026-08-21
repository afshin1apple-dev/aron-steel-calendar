from playwright.sync_api import sync_playwright

URL = "https://khorasan-steel.com/product.php?prd=5"

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page(locale="fa-IR")

    print("=" * 90)
    print("DOM STRUCTURE TEST")
    print("=" * 90)

    page.goto(
        URL,
        wait_until="networkidle",
        timeout=60000
    )

    page.wait_for_timeout(3000)

    # پیدا کردن تمام عناصری که متن «قیمت امروز» دارند
    elements = page.get_by_text(
        "قیمت امروز",
        exact=False
    )

    print("PRICE HEADER ELEMENTS:", elements.count())

    for i in range(min(elements.count(), 10)):

        el = elements.nth(i)

        print("\n" + "-" * 90)
        print("HEADER", i)
        print("-" * 90)

        try:
            print("TAG:", el.evaluate("(e) => e.tagName"))
            print("TEXT:", el.inner_text())
            print("\nOUTER HTML:")
            print(
                el.evaluate(
                    "(e) => e.parentElement.parentElement.outerHTML"
                )[:12000]
            )

        except Exception as e:
            print("ERROR:", e)

    print("\n" + "=" * 90)
    print("SEARCHING PRICE NUMBERS")
    print("=" * 90)

    # تمام عناصر حاوی قیمت‌های 6 رقمی
    candidates = page.locator(
        "text=/\\d{6}/"
    )

    print(
        "NUMBER CANDIDATES:",
        candidates.count()
    )

    for i in range(min(candidates.count(), 30)):

        el = candidates.nth(i)

        try:

            print("\n" + "-" * 60)
            print("CANDIDATE", i)
            print("TAG:", el.evaluate("(e) => e.tagName"))
            print("TEXT:", el.inner_text()[:1000])

            print("PARENT:")
            print(
                el.evaluate(
                    "(e) => e.parentElement.outerHTML"
                )[:5000]
            )

        except Exception as e:
            print("ERROR:", e)

    browser.close()

print("\n" + "=" * 90)
print("DOM TEST FINISHED")
print("=" * 90)