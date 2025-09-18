from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
from pathlib import Path
import os

app = Flask(__name__)
FFMPEG_PATH = r"C:\ffmpeg\bin"  # Update if deploying to Linux
TEMP_DIR = Path("temp_downloads")
TEMP_DIR.mkdir(exist_ok=True)

def get_formats(link):
    """Fetch all available formats using desktop user-agent."""
    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "format": "best",
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
    formats = info.get("formats", [])
    video_res = sorted({f.get("height") for f in formats if f.get("height")}, reverse=True)
    return video_res, info

def download_video(link, quality):
    ydl_opts = {
        "outtmpl": str(TEMP_DIR / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "ffmpeg_location": FFMPEG_PATH,
        "format": f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link)
        filename = ydl.prepare_filename(info)
    return Path(filename)

def download_audio(link, quality="320"):
    ydl_opts = {
        "outtmpl": str(TEMP_DIR / "%(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": quality},
            {"key": "FFmpegMetadata"},
        ],
        "ffmpeg_location": FFMPEG_PATH,
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link)
        filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")
    return Path(filename)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        link = request.form["url"]

        # Fetch video info
        if "fetch" in request.form:
            resolutions, info = get_formats(link)
            return render_template(
                "index.html",
                link=link,
                resolutions=resolutions,
                title=info.get("title"),
                thumbnail=info.get("thumbnail"),
            )

        # Download video/audio
        elif "download" in request.form:
            mode = request.form["mode"]
            quality = request.form.get("quality", "320")

            if mode == "video":
                filepath = download_video(link, quality)
            else:
                filepath = download_audio(link, quality)

            @after_this_request
            def remove_file(response):
                try:
                    os.remove(filepath)
                except:
                    pass
                return response

            return send_file(filepath, as_attachment=True)

    return render_template("index.html", resolutions=[])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


