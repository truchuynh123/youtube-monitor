import os
import json
import datetime
from flask import Flask, render_template, request, redirect, url_for
from yt_dlp import YoutubeDL
from urllib.parse import urlparse
import re

app = Flask(__name__)

CHANNELS_FILE = "channels.json"

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_channels(data):
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def extract_channel_id(url):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("channel_id")
    except Exception as e:
        print("⚠️ Không thể trích xuất channel_id:", e)
        return None

def get_channel_name(channel_id):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/channel/{channel_id}", download=False)
            return info.get("uploader") or channel_id
    except Exception as e:
        print("⚠️ Không thể lấy tên kênh:", e)
        return channel_id

@app.route("/", methods=["GET"])
def index():
    channels = load_channels()
    return render_template("index.html", channels=channels)

@app.route("/add_channel", methods=["POST"])
def add_channel():
    url = request.form.get("channel_url")
    folder = request.form.get("folder_name")
    download_path = request.form.get("download_path") or "downloads"
    channel_id_manual = request.form.get("channel_id_manual")
    channel_name_manual = request.form.get("channel_name_manual")

    if not url or not folder:
        return "Thiếu thông tin đầu vào", 400

    channel_id = extract_channel_id(url)

    if not channel_id and channel_id_manual:
        channel_id = channel_id_manual.strip()

    if not channel_id:
        return "Không thể trích xuất Channel ID từ URL và không có Channel ID thủ công", 400

    if channel_name_manual:
        channel_name = channel_name_manual.strip()
    else:
        channel_name = get_channel_name(channel_id)

    channels = load_channels()
    channels[channel_id] = {
        "name": channel_name,
        "folder": folder,
        "download_path": download_path,
        "added": datetime.datetime.now(datetime.UTC).isoformat()
    }
    save_channels(channels)
    return redirect(url_for("index"))
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render yêu cầu lấy PORT từ biến môi trường
    app.run(host="0.0.0.0", port=port)

