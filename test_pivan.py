import requests
from bs4 import BeautifulSoup


URL = "https://pivan.co/brands/khorasan-steel-neishabour/rebar/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}


def main():

    print("=" * 70)
    print("PIVAN STEEL PRICE TEST")
    print("=" * 70)

    print("URL:", URL)

    try:

        response = requests.get(
            URL,
            headers=HEADERS,
            timeout=30
        )

        print("HTTP:", response.status_code)
        print("LENGTH:", len(response.text))

        response.raise_for_status()

    except Exception as e:

        print("ERROR:", e)
        return

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    print()
    print("=" * 70)
    print("TABLES")
    print("=" * 70)

    tables = soup.find_all("table")

    print(
        "TABLE COUNT:",
        len(tables)
    )

    for index, table in enumerate(
        tables,
        start=1
    ):

        print()
        print(
            f"--- TABLE {index} ---"
        )

        rows = table.find_all("tr")

        print(
            "ROWS:",
            len(rows)
        )

        for row in rows[:10]:

            cells = row.find_all(
                ["th", "td"]
            )

            values = [
                cell.get_text(
                    " ",
                    strip=True
                )
                for cell in cells
            ]

            print(values)

    print()
    print("=" * 70)
    print("TEXT SAMPLE")
    print("=" * 70)

    text = soup.get_text(
        " ",
        strip=True
    )

    print(
        text[:5000]
    )

    print()
    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)


if __name__ == "__main__":
    main()