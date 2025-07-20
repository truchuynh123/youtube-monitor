from flask import Flask, render_template, request, redirect
import json
import os
import requests
import threading
import time
from xml.etree import ElementTree as ET

app = Flask(__name__)

CHANNELS_FILE = "channels.json"
VIDEOS_FILE = "videos.json"

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)

def fetch_latest_video(channel_id):
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        resp = requests.get(rss_url)
        if resp.status_code != 200:
            return None
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

def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_videos(videos):
    with open(VIDEOS_FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

def monitor_loop():
    print("[monitor] Đang chạy giám sát video mới mỗi phút...")
    while True:
        channels = load_channels()
        current_data = load_videos()

        for ch in channels:
            latest = fetch_latest_video(ch["channel_id"])
            if latest:
                last_known = current_data.get(ch["channel_id"])
                if not last_known or last_known["video_id"] != latest["video_id"]:
                    print(f"[NEW VIDEO] {ch['name']}: {latest['title']}")
                    current_data[ch["channel_id"]] = latest
                    save_videos(current_data)
        time.sleep(60)

@app.route("/")
def index():
    channels = load_channels()
    videos = load_videos()
    return render_template("index.html", channels=channels, videos=videos)

@app.route("/add", methods=["POST"])
def add_channel():
    url = request.form["channel_url"].strip()
    name = request.form["channel_name"].strip()
    if "@@" in url or "/@" in url:
        # Chuyển từ dạng @username → channel_id
        try:
            resp = requests.get(url)
            if "channelId" in resp.text:
                import re
                match = re.search(r"channelId=([\w\-]+)", resp.text)
                if match:
                    channel_id = match.group(1)
                else:
                    return "Không tìm thấy channel ID trong trang", 400
            else:
                return "Không thể xác định channel ID từ đường link", 400
        except:
            return "Lỗi khi lấy thông tin từ đường link", 400
    elif "channel/" in url:
        channel_id = url.split("channel/")[-1].split("/")[0]
    else:
        return "Link kênh không hợp lệ", 400

    channels = load_channels()
    if not any(c["channel_id"] == channel_id for c in channels):
        channels.append({"name": name, "channel_id": channel_id})
        save_channels(channels)
    return redirect("/")

# ✅ Khởi động background thread khi app Flask bắt đầu
if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

