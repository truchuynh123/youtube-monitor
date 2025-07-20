from flask import Flask, render_template, request, redirect
import os
import json
import threading
import time
from datetime import datetime, timedelta
import yt_dlp

app = Flask(__name__)

CHANNEL_FILE = 'channels.json'
VIDEO_FILE = 'videos.json'

# 🧩 Tạo file nếu chưa tồn tại
if not os.path.exists(CHANNEL_FILE):
    with open(CHANNEL_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(VIDEO_FILE):
    with open(VIDEO_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

# 🧩 Hàm tiện ích
def load_channels():
    with open(CHANNEL_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_channels(channels):
    with open(CHANNEL_FILE, 'w', encoding='utf-8') as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)

def load_videos():
    with open(VIDEO_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_videos(videos):
    with open(VIDEO_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

# 🧩 Lấy ID và tên từ link kênh
def extract_channel_info(link):
    ydl_opts = {'quiet': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(link, download=False)
            return {
                'id': info['id'],
                'name': info.get('channel', info.get('title', 'Không tên'))
            }
        except Exception as e:
            print(f"Lỗi lấy thông tin kênh: {e}")
            return None

# 🧩 Lấy video mới trong 24h gần nhất
def fetch_recent_videos(channel_id):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': True,
        'dump_single_json': True,
    }
    url = f"https://www.youtube.com/channel/{channel_id}/videos"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            data = ydl.extract_info(url, download=False)
            videos = []
            now = datetime.utcnow()
            for entry in data.get('entries', []):
                upload_date = entry.get('upload_date')
                if upload_date:
                    upload_time = datetime.strptime(upload_date, '%Y%m%d')
                    if now - upload_time <= timedelta(days=1):
                        videos.append({
                            'id': entry['id'],
                            'title': entry['title'],
                            'uploaded': upload_time.strftime('%Y-%m-%d')
                        })
            return videos
        except Exception as e:
            print(f"Lỗi lấy video: {e}")
            return []

# 🧩 Nền: kiểm tra định kỳ mỗi 60s
def background_updater():
    while True:
        videos = load_videos()
        channels = load_channels()
        for ch in channels:
            new_videos = fetch_recent_videos(ch['id'])
            if new_videos:
                videos[ch['name']] = new_videos
        save_videos(videos)
        time.sleep(60)

# 👉 Khởi động luồng nền
threading.Thread(target=background_updater, daemon=True).start()

# ==== ROUTES ====

@app.route('/')
def index():
    channels = load_channels()
    videos = load_videos()
    return render_template('index.html', channels=channels, videos=videos)

@app.route('/add_channel', methods=['POST'])
def add_channel():
    link = request.form.get('link')
    info = extract_channel_info(link)
    if info:
        channels = load_channels()
        if not any(c['id'] == info['id'] for c in channels):
            channels.append(info)
            save_channels(channels)
    return redirect('/')
