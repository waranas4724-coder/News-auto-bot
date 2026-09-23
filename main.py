import time
import threading
import requests
import json
import xml.etree.ElementTree as ET
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
WEBSITE_URL = "https://worldsnew.netlify.app"

# ৩০টি শীর্ষ বিশ্বখ্যাত আরএসএস নিউজ ফিড (খবর, প্রযুক্তি, খেলাধুলা, বিজনেস)
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "http://feeds.bbci.co.uk/news/business/rss.xml",
    "http://rss.cnn.com/rss/edition_world.rss",
    "http://rss.cnn.com/rss/edition_technology.rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.theguardian.com/technology/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://moxie.foxnews.com/google-publisher/world.xml",
    "https://moxie.foxnews.com/google-publisher/latest.xml",
    "https://search.cnbc.com/rs/search/combinedrender?source=10000003&id=10000003&extra=headline",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://www.theverge.com/rss/index.xml",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://www.npr.org/rss/rss.php?id=1004",
    "https://www.france24.com/en/rss",
    "https://rss.dw.com/xml/rss-en-all",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://mashable.com/feed",
    "https://arstechnica.com/feed/",
    "https://www.ign.com/news/rss",
    "https://www.espn.com/espn/rss/news",
    "https://www.skysports.com/rss/12040",
    "https://www.sciencedaily.com/rss/all.xml",
    "https://feeds.feedburner.com/NDTV-LatestNews",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.economist.com/the-world-this-week/rss.xml"
]

latest_data = {
    "news": [],
    "weather": "Loading...",
    "currency": "Loading..."
}

posted_links = set()

def send_photo_or_text_to_telegram(caption, image_url):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram credentials missing!")
        return

    # ১. ছবিসহ ফটো পোস্ট টেলিগ্রামে পাঠানো
    photo_api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    payload_photo = {
        "chat_id": TG_CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    try:
        res = requests.post(photo_api_url, json=payload_photo, timeout=10)
        if res.status_code == 200:
            print("✅ Photo Post Sent to Telegram Successfully!")
            return
    except Exception as e:
        print(f"Telegram Photo Error: {e}")

    # ২. ছবি লিংকে সমস্যা থাকলে ব্যাকআপ হিসেবে টেক্সট পোস্ট
    msg_api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload_msg = {
        "chat_id": TG_CHAT_ID,
        "text": caption,
        "parse_mode": "HTML"
    }
    try:
        requests.post(msg_api_url, json=payload_msg, timeout=10)
        print("✅ Text Post Sent to Telegram Successfully!")
    except Exception as e:
        print(f"Telegram Text Error: {e}")

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(latest_data).encode('utf-8'))

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def clean_html(text):
    if not text:
        return ""
    clean = re.sub('<.*?>', '', text)
    return clean.strip()

def extract_image(item):
    namespaces = {
        'media': 'http://search.yahoo.com/mrss/',
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }
    
    # ১. media:content বা media:thumbnail খোঁজা
    for tag in ['media:content', 'media:thumbnail']:
        elem = item.find(tag, namespaces)
        if elem is not None and 'url' in elem.attrib:
            return elem.attrib['url']
    
    # ২. enclosure ট্যাগ খোঁজা (ছবি ক্যাটাগরি)
    enclosure = item.find('enclosure')
    if enclosure is not None and 'url' in enclosure.attrib:
        return enclosure.attrib['url']

    # ৩. description বা content এর ভেতর HTML <img> ট্যাগ খোঁজা
    desc = item.find('description').text if item.find('description') is not None else ""
    content = item.find('content:encoded', namespaces).text if item.find('content:encoded', namespaces) is not None else ""
    
    combined = (desc or "") + " " + (content or "")
    matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', combined, re.IGNORECASE)
    if matches:
        return matches[0]

    # ছবি না পাওয়া গেলে আকর্ষণীয় স্ট্যান্ডার্ড নিউজ ব্যানার
    return "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=600&q=80"

def fetch_news_from_all_sources():
    all_fetched_news = []
    
    for feed_url in RSS_FEEDS:
        try:
            res = requests.get(feed_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=6)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                items = root.findall('.//item')
                
                for item in items[:3]:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    
                    if title_elem is not None and link_elem is not None:
                        title = clean_html(title_elem.text)
                        link = link_elem.text.strip() if link_elem.text else ""
                        desc = clean_html(desc_elem.text) if desc_elem is not None else ""

                        if len(desc) > 200:
                            desc = desc[:197] + "..."

                        image_url = extract_image(item)

                        if link and link not in posted_links:
                            all_fetched_news.append({
                                "title": title,
                                "description": desc,
                                "link": link,
                                "image": image_url
                            })
        except Exception:
            continue

    return all_fetched_news

def fetch_weather():
    try:
        url = 'https://api.open-meteo.com/v1/forecast?latitude=23.8103&longitude=90.4125&current_weather=true'
        res = requests.get(url, timeout=5).json()
        temp = res['current_weather']['temperature']
        latest_data["weather"] = f"{temp}°C"
    except Exception:
        pass

def fetch_currency():
    try:
        url = 'https://open.er-api.com/v6/latest/USD'
        res = requests.get(url, timeout=5).json()
        bdt_rate = res['rates']['BDT']
        latest_data["currency"] = f"{round(bdt_rate, 2)} BDT"
    except Exception:
        pass

def bot_loop():
    print("🚀 30+ RSS Feeds Multi-Bot Engine Active (Posts every 15 mins)!")
    
    while True:
        fetch_weather()
        fetch_currency()
        
        new_articles = fetch_news_from_all_sources()
        
        if new_articles:
            # একদম আনকমন নতুন ১টি খবর নির্বাচন
            top_news = new_articles[0]
            posted_links.add(top_news["link"])

            # ওয়েবসাইটে প্রদর্শনের জন্য তালিকার শুরুতে যোগ (সর্বোচ্চ ৩০টি খবর থাকবে)
            latest_data["news"].insert(0, top_news)
            latest_data["news"] = latest_data["news"][:30]

            # টেলিগ্রাম সুন্দর ফরম্যাট
            tg_caption = f"📰 <b>{top_news['title']}</b>\n\n{top_news['description']}\n\n👉 <b>Read Full News On Website:</b>\n🔗 {WEBSITE_URL}"
            
            send_photo_or_text_to_telegram(tg_caption, top_news['image'])
            print(f"✅ Published New Post: {top_news['title']}")
        else:
            print("ℹ️ No new unposted news found at this moment.")

        # ১৫ মিনিট টাইমার (১৫ মিনিট = ৯০০ সেকেন্ড)
        time.sleep(900)

if __name__ == "__main__":
    t = threading.Thread(target=bot_loop)
    t.daemon = True
    t.start()
    run_web_server()
