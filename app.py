from flask import Flask, render_template, request, redirect
import requests
import json
import os

app = Flask(__name__)
CHANNELS_FILE = "channels.json"

# Load danh sách kênh từ file
def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# Lưu danh sách kênh vào file
def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2)

# Lấy video mới nhất từ một kênh YouTube (qua RSS)
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
            return {"title": title, "video_id": video_id}
    except Exception as e:
        print(f"Lỗi khi lấy video từ kênh {channel_id}: {e}")
    return None

@app.route("/", methods=["GET"])
def index():
    channels = load_channels()
    videos = []
    for ch in channels:
        video = fetch_latest_video(ch["channel_id"])
        if video:
            videos.append({"name": ch["name"], "video_id": video["video_id"], "title": video["title"]})
    return render_template("index.html", videos=videos)

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
    port = int(os.environ.get("PORT", 5000))  # Render sẽ cung cấp PORT qua biến môi trường
    app.run(host="0.0.0.0", port=port)
