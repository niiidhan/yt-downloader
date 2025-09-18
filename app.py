import os
from flask import Flask, render_template, request, send_file
import yt_dlp

app = Flask(__name__)

# Default download folder
DOWNLOAD_FOLDER = "downloads"
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Path to cookies file (must be Netscape format)
COOKIES_FILE = "cookies.txt"


def get_ydl_opts(extra_opts=None):
    """Return yt-dlp options with cookies if available"""
    opts = {"quiet": True, "noplaylist": True}
    if os.path.exists(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE
    if extra_opts:
        opts.update(extra_opts)
    return opts


def get_video_info(url):
    """Fetch video title, thumbnail, and available resolutions"""
    ydl_opts = get_ydl_opts({"skip_download": True})
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get("formats", [])

        # Extract available resolutions
        resolutions = sorted(
            list(
                set(
                    f["height"]
                    for f in formats
                    if f.get("height") and f.get("vcodec") != "none"
                )
            ),
            reverse=True,
        )
        return info["title"], info["thumbnail"], resolutions


def download_video(url, quality, mode):
    """Download video or audio"""
    output_path = os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s")

    if mode == "audio":
        extra_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality,
                }
            ],
        }
    else:
        extra_opts = {
            "format": f"bestvideo[height<={quality}]+bestaudio/best",
            "outtmpl": output_path,
        }

    ydl_opts = get_ydl_opts(extra_opts)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if mode == "audio":
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        return filename


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")

        if "fetch" in request.form:
            try:
                title, thumbnail, resolutions = get_video_info(url)
                return render_template(
                    "index.html",
                    link=url,
                    title=title,
                    thumbnail=thumbnail,
                    resolutions=resolutions,
                )
            except Exception as e:
                return f"Error fetching video info: {e}"

        elif "download" in request.form:
            quality = request.form.get("quality")
            mode = request.form.get("mode")

            try:
                file_path = download_video(url, quality, mode)
                return send_file(file_path, as_attachment=True)
            except Exception as e:
                return f"Error downloading: {e}"

    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
