import time
import threading
import requests
import json
import xml.etree.ElementTree as ET
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
WEBSITE_URL = "https://worldsnew.netlify.app"

latest_data = {
    "news": [],
    "weather": "Loading...",
    "currency": "Loading..."
}

def send_to_telegram(text):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram variables missing!")
        return 
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram Error:", e)

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

def fetch_latest_news():
    try:
        url = 'http://feeds.bbci.co.uk/news/world/rss.xml'
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            items = root.findall('.//item')
            
            news_list = []
            # শীর্ষ ৫টি খবর ও তার বিবরণ সংগ্রহ
            for item in items[:5]:
                title = item.find('title').text if item.find('title') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                
                news_list.append({
                    "title": title,
                    "description": desc,
                    "link": link
                })

            if news_list:
                if not latest_data["news"] or latest_data["news"][0]["title"] != news_list[0]["title"]:
                    latest_data["news"] = news_list
                    top_news = news_list[0]
                    
                    tg_message = f"📰 <b>{top_news['title']}</b>\n\n{top_news['description']}\n\n👉 <b>Read Full News On Website:</b>\n🔗 {WEBSITE_URL}"
                    send_to_telegram(tg_message)
                    print(f"✅ New Post Sent to Telegram: {top_news['title']}")
    except Exception as e:
        print(f"News Error: {e}")

def fetch_weather():
    try:
        url = 'https://api.open-meteo.com/v1/forecast?latitude=23.8103&longitude=90.4125&current_weather=true'
        res = requests.get(url).json()
        temp = res['current_weather']['temperature']
        latest_data["weather"] = f"{temp}°C"
    except Exception as e:
        pass

def fetch_currency():
    try:
        url = 'https://open.er-api.com/v6/latest/USD'
        res = requests.get(url).json()
        bdt_rate = res['rates']['BDT']
        latest_data["currency"] = f"{bdt_rate} BDT"
    except Exception as e:
        pass

def bot_loop():
    print("🚀 Auto-Post Bot Running for worldsnew.netlify.app!")
    while True:
        fetch_latest_news()
        fetch_weather()
        fetch_currency()
        time.sleep(1800)

if __name__ == "__main__":
    t = threading.Thread(target=bot_loop)
    t.daemon = True
    t.start()
    run_web_server()
