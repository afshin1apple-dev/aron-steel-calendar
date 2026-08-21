import requests
import feedparser

sources = {
    "WSJ Commodities": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
    "Economist": "https://www.economist.com/finance-and-economics/rss.xml",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Investing": "https://www.investing.com/rss/news.rss",
}

print("\n========== SOURCE TEST ==========\n")

for name, url in sources.items():
    print(f"Checking: {name}")
    print(f"URL: {url}")

    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
            timeout=20
        )

        print("HTTP status:", r.status_code)

        if r.status_code == 200:
            feed = feedparser.parse(r.content)

            print("Entries:", len(feed.entries))

            if feed.entries:
                print("Latest:", feed.entries[0].get("title", "No title"))
                print("Link:", feed.entries[0].get("link", "No link"))
                print("✅ WORKING")
            else:
                print("⚠️ Connected but no entries")

        else:
            print("❌ FAILED")

    except Exception as e:
        print("❌ ERROR:", e)

    print("--------------------------------\n")

print("========== TEST FINISHED ==========")