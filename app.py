from flask import Flask, render_template, request, redirect, url_for
import json
import os
import re
import subprocess
import datetime
from datetime import datetime, UTC
import requests

app = Flask(__name__)
DATA_FILE = "channels.json"

def load_channels():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_channels(channels):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=4, ensure_ascii=False)

def extract_channel_id(url):
    if "@"+url.strip("@") == url:
        url = "https://www.youtube.com/" + url
    if "/@" in url:
        try:
            response = requests.get(url)
            match = re.search(r'"channelId":"(UC[\w-]{22})"', response.text)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Lỗi khi lấy channel ID từ handle: {e}")
    match = re.search(r"(UC[\w-]{22})", url)
    return match.group(1) if match else None

def get_channel_name(channel_id):
    try:
        url = f"https://www.youtube.com/channel/{channel_id}"
        response = requests.get(url)
        match = re.search(r'"title":"(.*?)"', response.text)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Lỗi khi lấy tên kênh: {e}")
    return "Không xác định"

@app.route("/", methods=["GET"])
def index():
    channels = load_channels()
    return render_template("index.html", channels=channels)

@app.route("/add_channel", methods=["POST"])
def add_channel():
    url = request.form.get("channel_url")
    folder = request.form.get("folder_name")
    download_path = request.form.get("download_path") or "downloads"

    if not url or not folder:
        return redirect(url_for("index"))

    channel_id = extract_channel_id(url)
    if not channel_id:
        return "Không thể trích xuất Channel ID từ URL", 400

    channel_name = get_channel_name(channel_id)
    channels = load_channels()

    channels[channel_id] = {
        "name": channel_name,
        "folder": folder,
        "download_path": download_path,
        "added": datetime.now(UTC).isoformat()
    }
    save_channels(channels)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
