from flask import Flask, render_template, request
import yt_dlp
import os

app = Flask(__name__)

# Ensure downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

cookies_file = "cookies.txt"

@app.route("/", methods=["GET", "POST"])
def index():
    title = None
    thumbnail = None
    resolutions = None
    link = None
    message = None

    if request.method == "POST":
        if "fetch" in request.form:
            link = request.form["url"]
            try:
                ydl_opts = {
                    "quiet": True,
                    "skip_download": True,
                    "cookiefile": cookies_file,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link, download=False)
                    title = info.get("title", "Unknown Title")
                    thumbnail = info.get("thumbnail")
                    formats = info.get("formats", [])
                    resolutions = sorted(
                        list({f["height"] for f in formats if f.get("height")}),
                        reverse=True,
                    )
            except Exception as e:
                title = f"Error fetching video info: {str(e)}"

        elif "download" in request.form:
            link = request.form["url"]
            mode = request.form.get("mode")
            quality = request.form.get("quality")

            try:
                if mode == "audio":
                    ydl_opts = {
                        "format": "bestaudio/best",
                        "outtmpl": f"downloads/%(title)s.%(ext)s",
                        "cookiefile": cookies_file,
                        "postprocessors": [
                            {
                                "key": "FFmpegExtractAudio",
                                "preferredcodec": "mp3",
                                "preferredquality": quality,
                            }
                        ],
                    }
                    message = f"✅ Download complete! Saved as MP3 ({quality} kbps)."

                else:
                    ydl_opts = {
                        "format": f"bestvideo[height<={quality}]+bestaudio/bestvideo+bestaudio/best",
                        "outtmpl": f"downloads/%(title)s.%(ext)s",
                        "cookiefile": cookies_file,
                        "merge_output_format": "mp4",
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(link, download=True)

                    actual_height = None
                    if "height" in info:
                        actual_height = info["height"]

                    if actual_height and str(actual_height) != quality:
                        message = f"⚠️ {quality}p not available. Downloaded best available ({actual_height}p)."
                    else:
                        message = f"✅ Download complete! Saved in {quality}p."

                title = message

            except Exception as e:
                title = f"Error during download: {str(e)}"

    return render_template(
        "index.html",
        title=title,
        thumbnail=thumbnail,
        resolutions=resolutions,
        link=link,
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
