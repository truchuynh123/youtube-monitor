from flask import Flask, render_template, request, redirect
import json, os, requests

app = Flask(__name__)
CHANNELS_FILE = "channels.json"
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def load_channels():
    if not os.path.exists(CHANNELS_FILE):
        return []
    with open(CHANNELS_FILE, "r") as f:
        return json.load(f)

def save_channels(channels):
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

def get_latest_video(channel_id):
    url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={channel_id}&part=snippet&order=date&maxResults=1"
    resp = requests.get(url)
    data = resp.json()
    if "items" in data and data["items"]:
        item = data["items"][0]
        video_id = item["id"].get("videoId")
        title = item["snippet"]["title"]
        return {"title": title, "video_id": video_id}
    return None

@app.route("/", methods=["GET", "POST"])
def index():
    channels = load_channels()
    videos = []
    for ch in channels:
        video = get_latest_video(ch["id"])
        if video:
            videos.append({"name": ch["name"], **video})
    return render_template("index.html", videos=videos)

@app.route("/add", methods=["POST"])
def add_channel():
    name = request.form["name"]
    channel_id = request.form["channel_id"]
    channels = load_channels()
    channels.append({"name": name, "id": channel_id})
    save_channels(channels)
    return redirect("/")
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
