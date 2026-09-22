import time
import requests
import xml.etree.ElementTree as ET

RSS_URL = 'http://feeds.bbci.co.uk/news/world/rss.xml'

def fetch_latest_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(RSS_URL, headers=headers)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            item = root.find('.//item')
            
            if item is not None:
                title = item.find('title').text
                link = item.find('link').text
                description = item.find('description').text
                
                print("========================================")
                print(f"New News Found: {title}")
                print(f"Link: {link}")
                print("========================================")
                
                # এখানে পরবর্তীতে আপনার ডাটাবেস বা ওয়েবসাইটে পোস্ট পাঠানোর লজিক থাকবে
    except Exception as e:
        print(f"Error fetching news: {e}")

if __name__ == "__main__":
    print("News Bot Started on Render!")
    while True:
        fetch_latest_news()
        # ১৮০০ সেকেন্ড = ৩০ মিনিট পর পর রান হবে
        time.sleep(1800)
