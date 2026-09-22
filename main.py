import time
import requests
import xml.etree.ElementTree as ET

# ১. নিউজ আনার ফাংশন (BBC News RSS)
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
                link = item.find('link').text
                print(f"📰 News: {title}\n🔗 Link: {link}\n")
    except Exception as e:
        print(f"News Error: {e}")

# ২. আবহাওয়ার লাইভ ডাটা (Open-Meteo API)
def fetch_weather():
    try:
        # ঢাকা শহরের আবহাওয়া (Latitude: 23.8103, Longitude: 90.4125)
        url = 'https://api.open-meteo.com/v1/forecast?latitude=23.8103&longitude=90.4125&current_weather=true'
        res = requests.get(url).json()
        temp = res['current_weather']['temperature']
        print(f"☀️ Current Weather (Dhaka): {temp}°C\n")
    except Exception as e:
        print(f"Weather Error: {e}")

# ৩. লাইভ কারেন্সি রেট (Open Exchange Rates API)
def fetch_currency():
    try:
        url = 'https://open.er-api.com/v6/latest/USD'
        res = requests.get(url).json()
        bdt_rate = res['rates']['BDT']
        print(f"💵 USD to BDT Rate: {bdt_rate} BDT\n")
    except Exception as e:
        print(f"Currency Error: {e}")

# বট রান করার লুপ
if __name__ == "__main__":
    print("🚀 All-in-One News & Data Bot Started on Render!\n")
    while True:
        print("----------------------------------------")
        fetch_latest_news()
        fetch_weather()
        fetch_currency()
        print("----------------------------------------\n")
        
        # ৩০০ সেকেন্ড = ৫ মিনিট পর পর সব আপডেট হবে
        time.sleep(300)
