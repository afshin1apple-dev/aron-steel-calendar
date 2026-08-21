from playwright.sync_api import sync_playwright
import re

URLS = {
    "سایر کارخانجات": "https://khorasan-steel.com/product.php?prd=5",
    "نیشابور": "https://khorasan-steel.com/product.php?prd=3",
}

def clean_number(text):
    text = text.replace(",", "").replace("،", "")
    text = re.sub(r"[^\d]", "", text)
    return int(text) if text else None


with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        locale="fa-IR"
    )

    for group, url in URLS.items():

        print("\n" + "=" * 90)
        print(group)
        print(url)
        print("=" * 90)

        page.goto(
            url,
            wait_until="networkidle",
            timeout=60000
        )

        page.wait_for_timeout(3000)

        # پیدا کردن عنوان‌های جدول
        headings = page.locator("text=قیمت امروز")

        print("PRICE HEADINGS:", headings.count())

        # تمام متن صفحه
        text = page.locator("body").inner_text()

        lines = [
            re.sub(r"\s+", " ", x).strip()
            for x in text.splitlines()
        ]

        print("\n--- EXTRACTED PRODUCTS ---")

        current_factory = None
        found = 0

        for i, line in enumerate(lines):

            if not line:
                continue

            # تشخیص کارخانه از خطوط قبل از جدول
            factories = [
                "اصفهان",
                "شاهین بناب",
                "ظفر",
                "راد همدان",
                "شاهرود",
                "سیادن ابهر",
                "البرزتاکستان",
                "روهینا جنوب",
                "آریان فولاد",
                "آناهیتا",
                "نیک صدرا",
                "پرشین فولاد",
                "فولادکاسپین",
                "شمس سپهر",
                "میانه",
                "کاوه تیکمه داش",
                "آذرفولادامین",
                "کویرکاشان",
                "فولاد سیرجان",
                "بافق یزد",
                "فایکو",
                "حدید سیرجان",
                "ابرکوه یزد",
                "درپاد تبریز",
            ]

            for factory in factories:

                if factory in line and len(line) < 80:
                    current_factory = factory
                    break

            # خطوطی که قیمت دارند
            numbers = re.findall(
                r"(?<!\d)\d{5,7}(?!\d)",
                line.replace(",", "")
            )

            if len(numbers) >= 2:

                values = [
                    clean_number(x)
                    for x in numbers
                ]

                values = [
                    x for x in values
                    if x is not None
                ]

                if len(values) >= 2:

                    # معمولاً:
                    # سایز / قیمت دیروز / قیمت امروز
                    print(
                        f"FACTORY={current_factory} | "
                        f"LINE={line}"
                    )

                    found += 1

                    if found >= 200:
                        break

        print("\nFOUND:", found)

    browser.close()

print("\n" + "=" * 90)
print("REAL PRICE EXTRACTION TEST FINISHED")
print("=" * 90)