import time
import threading
import requests
import xml.etree.ElementTree as ET
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

# 1. Render Port Binding-er jonno choto Server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"News Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# 2. News Bot Logic
def fetch_latest_news():
    try:
        url = 'http://feeds.bbci.co.uk/news/world/rss.xml'
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            item = root.find('.//item')
            if item is not None:
                title = item.find('title').text
                print(f"📰 News: {title}\n")
    except Exception as e:
        print(f"News Error: {e}")

def fetch_weather():
    try:
        url = 'https://api.open-meteo.com/v1/forecast?latitude=23.8103&longitude=90.4125&current_weather=true'
        res = requests.get(url).json()
        temp = res['current_weather']['temperature']
        print(f"☀️ Current Weather (Dhaka): {temp}°C\n")
    except Exception as e:
        print(f"Weather Error: {e}")

def fetch_currency():
    try:
        url = 'https://open.er-api.com/v6/latest/USD'
        res = requests.get(url).json()
        bdt_rate = res['rates']['BDT']
        print(f"💵 USD to BDT Rate: {bdt_rate} BDT\n")
    except Exception as e:
        print(f"Currency Error: {e}")

def bot_loop():
    print("🚀 All-in-One News Bot Loop Started!\n")
    while True:
        print("----------------------------------------")
        fetch_latest_news()
        fetch_weather()
        fetch_currency()
        print("----------------------------------------\n")
        time.sleep(300) # 5 minit interval

# এই লাইনটি ঠিক করা হয়েছে (ডাবল আন্ডারস্কোর যুক্ত করা হয়েছে)
if __name__ == "__main__":
    # Background-e bot cholbe
    t = threading.Thread(target=bot_loop)
    t.daemon = True
    t.start()
    
    # Main thread-e Render server cholbe
    run_web_server()
