from flask import Flask, render_template, request, send_file
import yt_dlp
import os
from pathlib import Path

app = Flask(__name__)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


def get_formats(link):
    ydl_opts = {
        "quiet": True,
        "cookiefile": "cookies.txt",  # 👈 Use cookies to bypass bot checks
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        formats = [
            {
                "format_id": f["format_id"],
                "ext": f["ext"],
                "resolution": f.get("resolution") or f"{f.get('width')}x{f.get('height')}",
                "filesize": f.get("filesize", 0),
            }
            for f in info.get("formats", [])
            if f.get("filesize")
        ]
    return formats, info


def download_video(link, format_id):
    ydl_opts = {
        "format": format_id,
        "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
        "cookiefile": "cookies.txt",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        return ydl.prepare_filename(info)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        link = request.form["link"]

        if "format_id" in request.form:  # download request
            format_id = request.form["format_id"]
            filepath = download_video(link, format_id)
            return send_file(filepath, as_attachment=True)

        # fetch formats
        resolutions, info = get_formats(link)
        return render_template("index.html", resolutions=resolutions, info=info)

    return render_template("index.html")


# ✅ Fix for Render: bind to 0.0.0.0:$PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
