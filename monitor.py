import threading
import time
import json
import requests
import os
from datetime import datetime

VIDEOS_FILE = "videos.json"
CHANNELS_FILE = "channels.json"

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def fetch_latest_video(channel_id):
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        resp = requests.get(rss_url)
        if resp.status_code != 200:
            return None
        from xml.etree import ElementTree as ET
        root = ET.fromstring(resp.text)
        entry = root.find("{http://www.w3.org/2005/Atom}entry")
        if entry is not None:
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
            published = entry.find("{http://www.w3.org/2005/Atom}published").text
            return {"title": title, "video_id": video_id, "published": published}
    except Exception as e:
        print(f"[monitor] Lỗi lấy video từ {channel_id}: {e}")
    return None

def save_videos(videos):
    with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def monitor_loop():
    print("⚙️ Đã khởi động monitor.py")
    print("[monitor] Bắt đầu kiểm tra video mới mỗi phút...\n")
    while True:
        channels = load_channels()
        current_data = load_videos()

        for ch in channels:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Đang kiểm tra kênh: {ch['name']}")
            latest = fetch_latest_video(ch["channel_id"])
            if latest:
                last_known = current_data.get(ch["channel_id"])
                if not last_known or last_known["video_id"] != latest["video_id"]:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🆕 [NEW VIDEO] {ch['name']}: {latest['title']}")
                    current_data[ch["channel_id"]] = latest
                    save_videos(current_data)
        time.sleep(60)

if __name__ == "__main__":
    monitor_loop()
