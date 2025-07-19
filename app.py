from flask import Flask, render_template, request, redirect
import json
import os
import subprocess
import datetime
import yt_dlp
import re

app = Flask(__name__)

CHANNELS_FILE = "channels.json"
DOWNLOAD_FOLDER = "downloads"

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return []
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_channels(channels):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)

def extract_channel_info(channel_url):
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            return {
                "name": info.get("uploader") or info.get("title"),
                "id": info.get("channel_id"),
                "url": f"https://www.youtube.com/channel/{info.get('channel_id')}"
            }
    except Exception as e:
        print(f"Lỗi khi trích xuất kênh: {e}")
        return None

def get_videos_within_1_day(channel_url):
    one_day_ago = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'dateafter': one_day_ago,
        'force_generic_extractor': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_url, download=False)
            return info.get('entries', [])
        except Exception as e:
            print(f"Lỗi khi lấy video: {e}")
            return []

@app.route("/", methods=["GET"])
def index():
    channels = load_channels()
    return render_template("index.html", channels=channels)

@app.route("/add_channel", methods=["POST"])
def add_channel():
    link = request.form.get("link")
    if not link:
        return redirect("/")

    info = extract_channel_info(link)
    if info:
        channels = load_channels()
        if not any(c["id"] == info["id"] for c in channels):
            channels.append(info)
            save_channels(channels)
    return redirect("/")

@app.route("/fetch_new_videos", methods=["GET"])
def fetch_new_videos():
    channels = load_channels()
    all_new_videos = {}

    for channel in channels:
        videos = get_videos_within_1_day(channel["url"])
        all_new_videos[channel["name"]] = videos

    return render_template("new_videos.html", videos=all_new_videos)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=10000)
