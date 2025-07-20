from flask import Flask, render_template, request, redirect, url_for
import os
import json
import datetime
import subprocess
import re
from yt_dlp import YoutubeDL

app = Flask(__name__)
DATA_FILE = "channels.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

def normalize_youtube_url(url_or_id):
    # Nếu là channel ID
    if re.match(r'^UC[\w-]{21}[AQgw]$', url_or_id):
        return f"https://www.youtube.com/channel/{url_or_id}"
    # Nếu là link @...
    if re.match(r'^@[\w\d_-]+$', url_or_id):
        return f"https://www.youtube.com/{url_or_id}"
    # Nếu là URL đầy đủ hợp lệ
    if url_or_id.startswith("http"):
        return url_or_id
    # Nếu là username dạng user/xyz
    return f"https://www.youtube.com/user/{url_or_id}"

def get_channel_info(url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': 'in_playlist',
        'force_generic_extractor': False,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "channel_id": info["id"],
            "channel_title": info.get("title", "Unknown Channel")
        }

@app.route("/")
def index():
    with open(DATA_FILE, "r") as f:
        channels = json.load(f)
    return render_template("index.html", channels=channels)

@app.route("/add_channel", methods=["POST"])
def add_channel():
    raw_input = request.form["channel_url"].strip()
    normalized_url = normalize_youtube_url(raw_input)

    try:
        info = get_channel_info(normalized_url)
    except Exception as e:
        return f"Lỗi khi lấy thông tin kênh: {str(e)}", 400

    with open(DATA_FILE, "r") as f:
        channels = json.load(f)

    if any(c["channel_id"] == info["channel_id"] for c in channels):
        return redirect(url_for("index"))

    new_channel = {
        "channel_id": info["channel_id"],
        "channel_title": info["channel_title"],
        "url": normalized_url,
        "added": datetime.datetime.utcnow().isoformat()
    }
    channels.append(new_channel)
    with open(DATA_FILE, "w") as f:
        json.dump(channels, f, indent=2)

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
