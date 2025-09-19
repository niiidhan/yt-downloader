from flask import Flask, render_template, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

cookies_file = "cookies.txt"  # Make sure this file exists or remove if not needed


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json()
    url = data.get("url")
    mode = data.get("mode", "video")
    quality = data.get("quality", "best")

    try:
        if mode == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
                "cookiefile": cookies_file if os.path.exists(cookies_file) else None,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        else:  # Video download
            ydl_opts = {
                "format": f"(bestvideo[height<={quality}]+bestaudio)/bestvideo+bestaudio/best",
                "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
                "cookiefile": cookies_file if os.path.exists(cookies_file) else None,
                "merge_output_format": "mp4",
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        title = info.get("title", "video")
        actual_height = info.get("height")
        if mode == "video" and quality != "best" and actual_height and str(actual_height) != quality:
            message = f"⚠️ {quality}p not available. Downloaded best available ({actual_height}p)."
        else:
            message = f"✅ Download complete! Saved: {title}"

        return jsonify({"status": "success", "message": message})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
