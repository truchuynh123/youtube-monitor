from flask import Flask, render_template, request, redirect
import requests
import json
import os
from datetime import datetime
import pytz
from xml.etree import ElementTree as ET

app = Flask(__name__)
CHANNELS_FILE = "channels.json"

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2)

# Lấy 10 video mới nhất từ một kênh YouTube (RSS)
def fetch_latest_videos(channel_id):
    videos = []
    try:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        resp = requests.get(rss_url)
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.text)
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")

        for entry in entries[:10]:  # lấy 10 video đầu tiên
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            video_id = entry.find("{http://www.youtube.com/xml/schemas/2015}videoId").text
            published = entry.find("{http://www.w3.org/2005/Atom}published").text
            # Chuyển thời gian về múi giờ Việt Nam
            utc_time = datetime.strptime(published, "%Y-%m-%dT%H:%M:%S%z")
            vn_time = utc_time.astimezone(pytz.timezone("Asia/Ho_Chi_Minh"))
            published_str = vn_time.strftime("%H:%M %d/%m/%Y")

            videos.append({
                "title": title,
                "video_id": video_id,
                "published": published_str
            })
    except Exception as e:
        print(f"Lỗi khi lấy video từ kênh {channel_id}: {e}")
    return videos

@app.route("/", methods=["GET"])
def index():
    channels = load_channels()
    all_videos = []
    for ch in channels:
        videos = fetch_latest_videos(ch["channel_id"])
        if videos:
            all_videos.append({
                "name": ch["name"],
                "videos": videos
            })
    return render_template("index.html", videos=all_videos)

@app.route("/add", methods=["POST"])
def add_channel():
    name = request.form.get("name")
    channel_id = request.form.get("channel_id")
    if name and channel_id:
        channels = load_channels()
        channels.append({"name": name, "channel_id": channel_id})
        save_channels(channels)
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
