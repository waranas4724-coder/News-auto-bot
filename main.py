import os
import re
import json
import time
import html
import hashlib
import sqlite3
import threading
import difflib
import xml.etree.ElementTree as ET

import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import HTTPServer, BaseHTTPRequestHandler


# =========================================================
# CONFIG
# =========================================================

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

WEBSITE_URL = os.environ.get(
    "WEBSITE_URL",
    "https://worldsnew.netlify.app"
)

PORT = int(os.environ.get("PORT", "10000"))

DB_FILE = os.environ.get(
    "NEWS_DB",
    "/tmp/news_bot.db"
)

POST_INTERVAL = 900  # 15 minutes


# =========================================================
# RSS FEEDS
# =========================================================
# 50+ feeds
#
# NOTE:
# Reuters/AP old public RSS endpoints are intentionally
# not included because their old public feeds are unreliable.
# =========================================================

RSS_FEEDS = [

    # -----------------------------------------------------
    # BBC
    # -----------------------------------------------------

    ("BBC World",
     "https://feeds.bbci.co.uk/news/world/rss.xml"),

    ("BBC Top Stories",
     "https://feeds.bbci.co.uk/news/rss.xml"),

    ("BBC Business",
     "https://feeds.bbci.co.uk/news/business/rss.xml"),

    ("BBC Technology",
     "https://feeds.bbci.co.uk/news/technology/rss.xml"),

    ("BBC Science",
     "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"),

    ("BBC UK",
     "https://feeds.bbci.co.uk/news/uk/rss.xml"),

    ("BBC US & Canada",
     "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"),

    ("BBC Asia",
     "https://feeds.bbci.co.uk/news/world/asia/rss.xml"),

    ("BBC Africa",
     "https://feeds.bbci.co.uk/news/world/africa/rss.xml"),

    ("BBC Europe",
     "https://feeds.bbci.co.uk/news/world/europe/rss.xml"),

    ("BBC Middle East",
     "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml"),

    ("BBC Sports",
     "https://feeds.bbci.co.uk/sport/rss.xml"),


    # -----------------------------------------------------
    # CNN
    # -----------------------------------------------------

    ("CNN World",
     "http://rss.cnn.com/rss/edition_world.rss"),

    ("CNN Technology",
     "http://rss.cnn.com/rss/edition_technology.rss"),

    ("CNN Business",
     "http://rss.cnn.com/rss/money_latest.rss"),

    ("CNN Top Stories",
     "http://rss.cnn.com/rss/cnn_topstories.rss"),


    # -----------------------------------------------------
    # AL JAZEERA
    # -----------------------------------------------------

    ("Al Jazeera",
     "https://www.aljazeera.com/xml/rss/all.xml"),

    ("Al Jazeera Middle East",
     "https://www.aljazeera.com/xml/rss/middle-east.xml"),

    ("Al Jazeera Asia",
     "https://www.aljazeera.com/xml/rss/asia.xml"),


    # -----------------------------------------------------
    # THE GUARDIAN
    # -----------------------------------------------------

    ("Guardian World",
     "https://www.theguardian.com/world/rss"),

    ("Guardian Technology",
     "https://www.theguardian.com/technology/rss"),

    ("Guardian Business",
     "https://www.theguardian.com/business/rss"),

    ("Guardian UK",
     "https://www.theguardian.com/uk-news/rss"),

    ("Guardian Science",
     "https://www.theguardian.com/science/rss"),


    # -----------------------------------------------------
    # NEW YORK TIMES
    # -----------------------------------------------------

    ("NY Times World",
     "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),

    ("NY Times Technology",
     "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"),

    ("NY Times Business",
     "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"),

    ("NY Times Science",
     "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml"),

    ("NY Times US",
     "https://rss.nytimes.com/services/xml/rss/nyt/US.xml"),


    # -----------------------------------------------------
    # EUROPE / INTERNATIONAL
    # -----------------------------------------------------

    ("DW News",
     "https://rss.dw.com/rdf/rss-en-all"),

    ("DW World",
     "https://rss.dw.com/rdf/rss-en-world"),

    ("Euronews",
     "https://www.euronews.com/rss"),

    ("France 24",
     "https://www.france24.com/en/rss"),

    ("Sky News World",
     "https://feeds.skynews.com/feeds/rss/world.xml"),

    ("Sky News Technology",
     "https://feeds.skynews.com/feeds/rss/technology.xml"),


    # -----------------------------------------------------
    # ASIA / INTERNATIONAL
    # -----------------------------------------------------

    ("NHK World",
     "https://www3.nhk.or.jp/rssxml/news/globalnewsroom.xml"),

    ("CBC World",
     "https://www.cbc.ca/webfeed/rss/rss-world"),


    # -----------------------------------------------------
    # NPR
    # -----------------------------------------------------

    ("NPR News",
     "https://feeds.npr.org/1001/rss.xml"),

    ("NPR World",
     "https://feeds.npr.org/1004/rss.xml"),


    # -----------------------------------------------------
    # FOX
    # -----------------------------------------------------

    ("Fox News World",
     "https://moxie.foxnews.com/google-publisher/world.xml"),

    ("Fox News Latest",
     "https://moxie.foxnews.com/google-publisher/latest.xml"),


    # -----------------------------------------------------
    # TECHNOLOGY
    # -----------------------------------------------------

    ("TechCrunch",
     "https://techcrunch.com/feed/"),

    ("Wired",
     "https://www.wired.com/feed/rss"),

    ("The Verge",
     "https://www.theverge.com/rss/index.xml"),

    ("Ars Technica",
     "https://feeds.arstechnica.com/arstechnica/index"),

    ("Mashable",
     "https://mashable.com/feed"),

    ("Engadget",
     "https://www.engadget.com/rss.xml"),

    ("VentureBeat",
     "https://venturebeat.com/feed/"),

    ("Gizmodo",
     "https://gizmodo.com/rss"),

    ("Hacker News",
     "https://news.ycombinator.com/rss"),


    # -----------------------------------------------------
    # BUSINESS / FINANCE
    # -----------------------------------------------------

    ("CNBC",
     "https://www.cnbc.com/id/100003114/device/rss/rss.html"),

    ("CoinDesk",
     "https://www.coindesk.com/arc/outboundfeeds/rss/"),


    # -----------------------------------------------------
    # SPORTS
    # -----------------------------------------------------

    ("ESPN",
     "https://www.espn.com/espn/rss/news"),

    ("Sky Sports",
     "https://www.skysports.com/rss/12040"),


    # -----------------------------------------------------
    # SCIENCE
    # -----------------------------------------------------

    ("ScienceDaily",
     "https://www.sciencedaily.com/rss/all.xml"),

    ("Scientific American",
     "https://www.scientificamerican.com/platform/syndication/rss/"),

    ("Nature",
     "https://www.nature.com/nature.rss"),


    # -----------------------------------------------------
    # US / INTERNATIONAL
    # -----------------------------------------------------

    ("VOA News",
     "https://www.voanews.com/api/ztqveq-$8t0z"),


    # -----------------------------------------------------
    # INDIA / SOUTH ASIA
    # -----------------------------------------------------

    ("NDTV Latest",
     "https://feeds.feedburner.com/NDTV-LatestNews"),

    ("Times of India",
     "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"),


    # -----------------------------------------------------
    # EXTRA
    # -----------------------------------------------------

    ("Economist",
     "https://www.economist.com/the-world-this-week/rss.xml"),

]


# =========================================================
# GLOBAL DATA
# =========================================================

latest_data = {
    "news": [],
    "weather": "Loading...",
    "currency": "Loading..."
}

db_lock = threading.Lock()


# =========================================================
# DATABASE
# =========================================================

def init_database():

    with sqlite3.connect(DB_FILE) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS posted_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_hash TEXT UNIQUE,
                title_hash TEXT,
                url TEXT,
                title TEXT,
                source TEXT,
                created_at REAL
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_title_hash
            ON posted_news(title_hash)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url
            ON posted_news(url)
        """)

        conn.commit()

    print(f"✅ Database initialized: {DB_FILE}")


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text):

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = text.lower()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def make_hash(text):

    normalized = normalize_text(text)

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


# =========================================================
# DUPLICATE CHECK
# =========================================================

def is_duplicate(title, link):

    title_normalized = normalize_text(title)

    title_hash = make_hash(title)

    # -----------------------------------------------------
    # URL exact duplicate
    # -----------------------------------------------------

    with db_lock:

        with sqlite3.connect(DB_FILE) as conn:

            row = conn.execute(
                """
                SELECT id
                FROM posted_news
                WHERE url = ?
                LIMIT 1
                """,
                (link,)
            ).fetchone()

            if row:
                return True


            # -------------------------------------------------
            # Exact title duplicate
            # -------------------------------------------------

            row = conn.execute(
                """
                SELECT id
                FROM posted_news
                WHERE title_hash = ?
                LIMIT 1
                """,
                (title_hash,)
            ).fetchone()

            if row:
                return True


            # -------------------------------------------------
            # Similar title duplicate
            # -------------------------------------------------

            rows = conn.execute(
                """
                SELECT title
                FROM posted_news
                ORDER BY created_at DESC
                LIMIT 500
                """
            ).fetchall()


    for row in rows:

        old_title = normalize_text(row[0])

        if not old_title:
            continue

        similarity = difflib.SequenceMatcher(
            None,
            title_normalized,
            old_title
        ).ratio()

        # 88%+ similar = duplicate
        if similarity >= 0.88:
            return True


    return False


# =========================================================
# SAVE POSTED NEWS
# =========================================================

def save_posted_news(title, link, source):

    title_hash = make_hash(title)

    combined_hash = make_hash(
        f"{title}|{link}"
    )

    with db_lock:

        with sqlite3.connect(DB_FILE) as conn:

            try:

                conn.execute(
                    """
                    INSERT INTO posted_news
                    (
                        news_hash,
                        title_hash,
                        url,
                        title,
                        source,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        combined_hash,
                        title_hash,
                        link,
                        title,
                        source,
                        time.time()
                    )
                )

                conn.commit()

            except sqlite3.IntegrityError:
                pass


# =========================================================
# CLEAN HTML
# =========================================================

def clean_html(text):

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# IMAGE EXTRACTION
# =========================================================

def extract_image(item):

    namespaces = {
        "media": "http://search.yahoo.com/mrss/",
        "content": "http://purl.org/rss/1.0/modules/content/"
    }

    # -----------------------------------------------------
    # media content / thumbnail
    # -----------------------------------------------------

    for tag in [
        "media:content",
        "media:thumbnail"
    ]:

        elem = item.find(
            tag,
            namespaces
        )

        if elem is not None:

            url = elem.attrib.get("url")

            if url:
                return url


    # -----------------------------------------------------
    # enclosure
    # -----------------------------------------------------

    enclosure = item.find("enclosure")

    if enclosure is not None:

        url = enclosure.attrib.get("url")

        if url:
            return url


    # -----------------------------------------------------
    # content encoded
    # -----------------------------------------------------

    desc_elem = item.find("description")

    content_elem = item.find(
        "content:encoded",
        namespaces
    )

    desc = (
        desc_elem.text
        if desc_elem is not None
        else ""
    )

    content = (
        content_elem.text
        if content_elem is not None
        else ""
    )

    combined = (
        (desc or "") +
        " " +
        (content or "")
    )

    matches = re.findall(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        combined,
        re.IGNORECASE
    )

    if matches:
        return matches[0]


    # -----------------------------------------------------
    # fallback image
    # -----------------------------------------------------

    return (
        "https://images.unsplash.com/"
        "photo-1504711434969-e33886168f5c"
        "?w=1200&q=80"
    )


# =========================================================
# XML HELPERS
# =========================================================

def get_element_text(element):

    if element is None:
        return ""

    return clean_html(
        "".join(
            element.itertext()
        )
    )


def find_first(element, names):

    for name in names:

        child = element.find(name)

        if child is not None:
            return child

    return None


# =========================================================
# PARSE FEED
# =========================================================

def parse_feed(feed_url, source_name):

    headers = {
        "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    }

    try:

        response = requests.get(
            feed_url,
            headers=headers,
            timeout=12
        )

        if response.status_code != 200:

            print(
                f"⚠️ {source_name}: "
                f"HTTP {response.status_code}"
            )

            return []


        root = ET.fromstring(
            response.content
        )


        # -------------------------------------------------
        # RSS
        # -------------------------------------------------

        items = root.findall(".//item")


        # -------------------------------------------------
        # Atom
        # -------------------------------------------------

        if not items:

            items = root.findall(
                ".//{http://www.w3.org/2005/Atom}entry"
            )


        articles = []


        for item in items[:10]:

            # ---------------------------------------------
            # RSS title
            # ---------------------------------------------

            title_element = find_first(
                item,
                [
                    "title",
                    "{http://www.w3.org/2005/Atom}title"
                ]
            )

            title = get_element_text(
                title_element
            )


            if not title:
                continue


            # ---------------------------------------------
            # RSS link
            # ---------------------------------------------

            link_element = find_first(
                item,
                [
                    "link",
                    "{http://www.w3.org/2005/Atom}link"
                ]
            )


            link = ""


            if link_element is not None:

                if link_element.text:

                    link = (
                        link_element.text
                        .strip()
                    )

                else:

                    link = (
                        link_element.attrib.get(
                            "href",
                            ""
                        )
                    )


            # ---------------------------------------------
            # Atom alternate link
            # ---------------------------------------------

            if not link:

                for child in item:

                    if child.tag.endswith("link"):

                        href = child.attrib.get(
                            "href"
                        )

                        rel = child.attrib.get(
                            "rel",
                            "alternate"
                        )

                        if href and rel == "alternate":

                            link = href
                            break


            if not link:
                continue


            # ---------------------------------------------
            # Description
            # ---------------------------------------------

            description_element = find_first(
                item,
                [
                    "description",
                    "summary",
                    "{http://www.w3.org/2005/Atom}summary",
                    "{http://purl.org/rss/1.0/modules/content/}encoded"
                ]
            )


            description = get_element_text(
                description_element
            )


            if len(description) > 350:

                description = (
                    description[:347] +
                    "..."
                )


            # ---------------------------------------------
            # Image
            # ---------------------------------------------

            image = extract_image(item)


            articles.append({

                "title": title,

                "description": description,

                "link": link,

                "image": image,

                "source": source_name

            })


        print(
            f"✅ {source_name}: "
            f"{len(articles)} articles"
        )

        return articles


    except Exception as e:

        print(
            f"❌ {source_name}: "
            f"{str(e)[:120]}"
        )

        return []


# =========================================================
# FETCH ALL NEWS
# =========================================================

def fetch_news_from_all_sources():

    all_articles = []


    with ThreadPoolExecutor(
        max_workers=12
    ) as executor:

        futures = [

            executor.submit(
                parse_feed,
                feed_url,
                source_name
            )

            for source_name, feed_url
            in RSS_FEEDS

        ]


        for future in as_completed(futures):

            try:

                result = future.result()

                if result:

                    all_articles.extend(
                        result
                    )

            except Exception:
                continue


    # -----------------------------------------------------
    # Remove duplicates inside current batch
    # -----------------------------------------------------

    unique_articles = []


    for article in all_articles:

        duplicate = False


        for existing in unique_articles:

            similarity = difflib.SequenceMatcher(
                None,
                normalize_text(
                    article["title"]
                ),
                normalize_text(
                    existing["title"]
                )
            ).ratio()


            if (
                article["link"]
                == existing["link"]
                or similarity >= 0.88
            ):

                duplicate = True
                break


        if not duplicate:

            unique_articles.append(
                article
            )


    return unique_articles


# =========================================================
# TELEGRAM MESSAGE
# =========================================================

def send_news_to_telegram(article):

    if not TG_BOT_TOKEN:

        print(
            "❌ TG_BOT_TOKEN missing!"
        )

        return False


    if not TG_CHAT_ID:

        print(
            "❌ TG_CHAT_ID missing!"
        )

        return False


    title = html.escape(
        article["title"]
    )

    description = html.escape(
        article["description"]
    )

    source = html.escape(
        article["source"]
    )

    link = article["link"]


    # -----------------------------------------------------
    # Professional Telegram caption
    # -----------------------------------------------------

    caption = (

        "📰 <b>WORLD NEWS</b>\n"
        "\n"

        f"<b>{title}</b>\n"
        "\n"

        f"{description}\n"
        "\n"

        f"🌐 <b>Source:</b> {source}\n"
        "\n"

        "━━━━━━━━━━━━━━━━━━\n"

        "🌍 <b>Stay Updated With World News</b>\n"

        "#WorldNews #BreakingNews #News"

    )


    api_base = (
        f"https://api.telegram.org/"
        f"bot{TG_BOT_TOKEN}"
    )


    # -----------------------------------------------------
    # Inline button
    # -----------------------------------------------------

    reply_markup = {

        "inline_keyboard": [

            [
                {
                    "text":
                    "🔗 Read Full News",
                    "url": link
                }
            ],

            [
                {
                    "text":
                    "🌐 Visit News Website",
                    "url":
                    WEBSITE_URL
                }
            ]

        ]

    }


    # -----------------------------------------------------
    # Try photo post
    # -----------------------------------------------------

    if article.get("image"):

        try:

            response = requests.post(

                f"{api_base}/sendPhoto",

                json={

                    "chat_id":
                    TG_CHAT_ID,

                    "photo":
                    article["image"],

                    "caption":
                    caption,

                    "parse_mode":
                    "HTML",

                    "reply_markup":
                    reply_markup

                },

                timeout=20

            )


            if response.status_code == 200:

                print(
                    "✅ Telegram photo post sent:"
                    f" {article['title']}"
                )

                return True


            else:

                print(
                    "⚠️ Photo failed: "
                    f"{response.text[:300]}"
                )


        except Exception as e:

            print(
                f"⚠️ Telegram photo error: {e}"
            )


    # -----------------------------------------------------
    # Text fallback
    # -----------------------------------------------------

    try:

        response = requests.post(

            f"{api_base}/sendMessage",

            json={

                "chat_id":
                TG_CHAT_ID,

                "text":
                caption,

                "parse_mode":
                "HTML",

                "disable_web_page_preview":
                False,

                "reply_markup":
                reply_markup

            },

            timeout=20

        )


        if response.status_code == 200:

            print(
                "✅ Telegram text post sent:"
                f" {article['title']}"
            )

            return True


        print(
            "❌ Telegram text failed:"
            f" {response.text[:300]}"
        )


    except Exception as e:

        print(
            f"❌ Telegram text error: {e}"
        )


    return False


# =========================================================
# WEATHER
# =========================================================

def fetch_weather():

    try:

        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=23.8103"
            "&longitude=90.4125"
            "&current_weather=true"
        )


        response = requests.get(
            url,
            timeout=8
        )


        data = response.json()


        temp = (
            data["current_weather"]
            ["temperature"]
        )


        latest_data["weather"] = (
            f"{temp}°C"
        )


    except Exception:

        pass


# =========================================================
# CURRENCY
# =========================================================

def fetch_currency():

    try:

        url = (
            "https://open.er-api.com/v6/latest/USD"
        )


        response = requests.get(
            url,
            timeout=8
        )


        data = response.json()


        rate = (
            data["rates"]["BDT"]
        )


        latest_data["currency"] = (
            f"{round(rate, 2)} BDT"
        )


    except Exception:

        pass


# =========================================================
# UPDATE WEBSITE DATA
# =========================================================

def update_website_data(article):

    latest_data["news"].insert(
        0,
        article
    )


    # Maximum 30 articles
    latest_data["news"] = (
        latest_data["news"][:30]
    )


# =========================================================
# MAIN BOT LOOP
# =========================================================

def bot_loop():

    print(
        "🚀 WORLD NEWS AUTO BOT STARTED"
    )

    print(
        f"📡 RSS sources: "
        f"{len(RSS_FEEDS)}"
    )

    print(
        "⏱️ Posting interval: "
        "15 minutes"
    )


    while True:

        try:

            # ---------------------------------------------
            # Weather + Currency
            # ---------------------------------------------

            fetch_weather()

            fetch_currency()


            # ---------------------------------------------
            # Fetch news
            # ---------------------------------------------

            print(
                "\n🔎 Checking RSS feeds..."
            )


            articles = (
                fetch_news_from_all_sources()
            )


            print(
                f"📥 Unique articles found: "
                f"{len(articles)}"
            )


            # ---------------------------------------------
            # Find first non-duplicate
            # ---------------------------------------------

            selected_article = None


            for article in articles:

                if is_duplicate(
                    article["title"],
                    article["link"]
                ):

                    continue


                selected_article = article

                break


            # ---------------------------------------------
            # Publish
            # ---------------------------------------------

            if selected_article:

                print(
                    "📰 Selected:"
                    f" {selected_article['title']}"
                )


                success = (
                    send_news_to_telegram(
                        selected_article
                    )
                )


                if success:

                    # Save ONLY after successful Telegram post
                    save_posted_news(

                        selected_article["title"],

                        selected_article["link"],

                        selected_article["source"]

                    )


                    # Website update
                    update_website_data(
                        selected_article
                    )


                    print(
                        "✅ Published successfully!"
                    )


                else:

                    print(
                        "❌ Telegram post failed. "
                        "News was NOT saved as posted."
                    )


            else:

                print(
                    "ℹ️ No new unique news "
                    "available right now."
                )


        except Exception as e:

            print(
                f"❌ Main loop error: {e}"
            )


        # ---------------------------------------------
        # 15 minutes
        # ---------------------------------------------

        print(
            "⏳ Next check in 15 minutes..."
        )


        time.sleep(
            POST_INTERVAL
        )


# =========================================================
# WEBSITE API SERVER
# =========================================================

class SimpleHTTPRequestHandler(
    BaseHTTPRequestHandler
):


    def do_GET(self):

        if self.path == "/":

            response_data = latest_data


        elif self.path == "/api/news":

            response_data = latest_data


        else:

            response_data = latest_data


        body = json.dumps(
            response_data,
            ensure_ascii=False
        ).encode("utf-8")


        self.send_response(200)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Cache-Control",
            "no-cache, no-store, must-revalidate"
        )

        self.end_headers()


        self.wfile.write(
            body
        )


    def log_message(
        self,
        format,
        *args
    ):

        # Reduce Render log noise
        return


# =========================================================
# WEB SERVER
# =========================================================

def run_web_server():

    server = HTTPServer(
        (
            "0.0.0.0",
            PORT
        ),
        SimpleHTTPRequestHandler
    )


    print(
        f"🌐 API server running on port "
        f"{PORT}"
    )


    server.serve_forever()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    init_database()


    # Start news bot
    news_thread = threading.Thread(
        target=bot_loop,
        daemon=True
    )

    news_thread.start()


    # Start website API
    run_web_server()
