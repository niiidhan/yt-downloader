from flask import Flask, render_template, request, send_file
import yt_dlp
import os
from pathlib import Path
import tempfile

app = Flask(__name__)

# Path to cookies file
COOKIES_FILE = "cookies.txt"

def get_formats(link):
    ydl_opts = {
        "quiet": True,
        "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        formats = [
            (f["format_id"], f.get("ext"), f.get("resolution") or f.get("height"))
            for f in info.get("formats", [])
            if f.get("acodec") != "none" or f.get("vcodec") != "none"
        ]
    return formats, info


def download_video(link, format_id):
    ydl_opts = {
        "format": format_id,
        "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        "outtmpl": os.path.join(tempfile.gettempdir(), "%(title)s.%(ext)s"),
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        return ydl.prepare_filename(info)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        link = request.form["url"]
        format_id = request.form.get("format_id")

        if format_id:  # User selected format → download
            filepath = download_video(link, format_id)
            return send_file(filepath, as_attachment=True)

        else:  # First submit → show formats
            resolutions, info = get_formats(link)
            return render_template(
                "index.html", formats=resolutions, link=link, title=info["title"]
            )

    return render_template("index.html", formats=None, link=None, title=None)


if __name__ == "__main__":
    app.run(debug=True)
