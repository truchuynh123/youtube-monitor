import threading
import json
import os
import datetime
from flask import Flask, request, redirect, render_template
from monitor import monitor_loop

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

def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

@app.route("/", methods=["GET"])
def index():
    channels = load_channels()
    all_videos = load_videos()
    videos = []
    for ch in channels:
        v = all_videos.get(ch["channel_id"])
        if v:
            videos.append({
                "name": ch["name"],
                "video_id": v["video_id"],
                "title": v["title"],
                "published": v["published"]
            })
    return render_template("index.html", videos=videos)

@app.route("/add_channel", methods=["POST"])
def add_channel():
    url = request.form.get("url")
    name = request.form.get("name")
    if not url or not name:
        return "Thiếu URL hoặc tên", 400

    import yt_dlp
    ydl_opts = {"quiet": True, "extract_flat": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            channel_id = info.get("channel_id")
            if not channel_id:
                return "Không thể trích xuất Channel ID từ URL", 400
        except Exception as e:
            return f"Lỗi: {e}", 400

    channels = load_channels()
    if any(c["channel_id"] == channel_id for c in channels):
        return "Kênh đã tồn tại", 400

    channels.append({"name": name, "url": url, "channel_id": channel_id, "added": datetime.datetime.now(datetime.UTC).isoformat()})
    save_channels(channels)
    return redirect("/")

if __name__ == "__main__":
    threading.Thread(target=monitor_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
