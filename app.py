from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
from pathlib import Path

app = Flask(__name__)

# ------------------- Folder setup ------------------- #
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = Path("/tmp/downloads")
VIDEO_DIR = DOWNLOAD_DIR / "Videos"
AUDIO_DIR = DOWNLOAD_DIR / "Audio"

for folder in [VIDEO_DIR, AUDIO_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


# ------------------- Fetch video info ------------------- #
@app.route("/api/info", methods=["POST"])
def api_info():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"ok": False, "error": "Missing URL"}), 400

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        fmts = info.get("formats", [])

        # ----- Filter + sort formats ----- #
        video_formats = [f for f in fmts if f.get("height") and f.get("vcodec") != "none"]
        video_heights = sorted({f["height"] for f in video_formats})

        best_formats_by_height = {}
        for h in video_heights:
            same_h = [f for f in video_formats if f["height"] == h]
            same_h.sort(key=lambda x: (x["ext"] != "mp4", x.get("tbr", 0)), reverse=True)
            best_formats_by_height[h] = same_h[0]

        audio_formats = [f for f in fmts if f.get("vcodec") == "none" and f.get("acodec") != "none"]

        return jsonify({
            "ok": True,
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "view_count": info.get("view_count"),
            "formats": fmts,
            "video_heights": video_heights,
            "audio_formats": audio_formats,
            "best_formats_by_height": best_formats_by_height,
            "webpage_url": info.get("webpage_url"),
        })

    except Exception as e:
        print("Error fetching info:", e)
        return jsonify({"ok": False, "error": str(e)})


# ------------------- Download and Merge ------------------- #
@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json()
    url = data.get("url")
    fmt_id = data.get("format_id")
    kind = data.get("kind", "video")

    if not url:
        return jsonify({"ok": False, "error": "Missing URL"}), 400

    output_path = VIDEO_DIR if kind == "video" else AUDIO_DIR

    try:
        # Different logic for audio vs video
        if kind == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": str(output_path / "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True
            }
        else:
            # Merge selected video + best audio
            format_string = f"{fmt_id}+bestaudio/best" if fmt_id else "bestvideo+bestaudio/best"
            ydl_opts = {
                "format": format_string,
                "merge_output_format": "mp4",
                "outtmpl": str(output_path / "%(title)s.%(ext)s"),
                "quiet": True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(result)

            # fix extension for audio
            if kind == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        return send_file(filename, as_attachment=True)

    except Exception as e:
        print("Download error:", e)
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
from pathlib import Path

app = Flask(__name__)

# ------------------- Folder setup ------------------- #
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = Path("/tmp/downloads")
VIDEO_DIR = DOWNLOAD_DIR / "Videos"
AUDIO_DIR = DOWNLOAD_DIR / "Audio"
COOKIE_FILE = BASE_DIR / "cookies.txt"  # ✅ added

for folder in [VIDEO_DIR, AUDIO_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# ------------------- Helper ------------------- #
COOKIE_ENV = os.getenv("YTDL_COOKIES")
COOKIE_PATH = BASE_DIR / "cookies.txt"

# If a cookie string is provided in environment (Render Secret),
# save it as cookies.txt for yt_dlp to use.
if COOKIE_ENV:
    with open(COOKIE_PATH, "w", encoding="utf-8") as f:
        f.write(COOKIE_ENV)

def get_cookie_opt():
    """Return yt_dlp options with cookie file if available."""
    if COOKIE_PATH.exists():
        return {"cookiefile": str(COOKIE_PATH)}
    return {}

# ------------------- Fetch video info ------------------- #
@app.route("/api/info", methods=["POST"])
def api_info():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"ok": False, "error": "Missing URL"}), 400

    # ✅ merge cookie option
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "extract_flat": False,
        **get_cookie_opt(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        fmts = info.get("formats", [])

        video_formats = [f for f in fmts if f.get("height") and f.get("vcodec") != "none"]
        video_heights = sorted({f["height"] for f in video_formats})

        best_formats_by_height = {}
        for h in video_heights:
            same_h = [f for f in video_formats if f["height"] == h]
            same_h.sort(key=lambda x: (x["ext"] != "mp4", x.get("tbr", 0)), reverse=True)
            best_formats_by_height[h] = same_h[0]

        audio_formats = [f for f in fmts if f.get("vcodec") == "none" and f.get("acodec") != "none"]

        return jsonify({
            "ok": True,
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "thumbnail": info.get("thumbnail"),
            "view_count": info.get("view_count"),
            "formats": fmts,
            "video_heights": video_heights,
            "audio_formats": audio_formats,
            "best_formats_by_height": best_formats_by_height,
            "webpage_url": info.get("webpage_url"),
        })

    except Exception as e:
        print("Error fetching info:", e)
        return jsonify({"ok": False, "error": str(e)})

# ------------------- Download and Merge ------------------- #
@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json()
    url = data.get("url")
    fmt_id = data.get("format_id")
    kind = data.get("kind", "video")

    if not url:
        return jsonify({"ok": False, "error": "Missing URL"}), 400

    output_path = VIDEO_DIR if kind == "video" else AUDIO_DIR

    try:
        if kind == "audio":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": str(output_path / "%(title)s.%(ext)s"),
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
                **get_cookie_opt(),  # ✅ added
            }
        else:
            format_string = f"{fmt_id}+bestaudio/best" if fmt_id else "bestvideo+bestaudio/best"
            ydl_opts = {
                "format": format_string,
                "merge_output_format": "mp4",
                "outtmpl": str(output_path / "%(title)s.%(ext)s"),
                "quiet": True,
                **get_cookie_opt(),  # ✅ added
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(result)

            if kind == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        return send_file(filename, as_attachment=True)

    except Exception as e:
        print("Download error:", e)
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
