from flask import Flask, render_template, request
import yt_dlp
import os

app = Flask(__name__)

# Ensure downloads folder exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Path to cookies file (provided by Render environment file)
cookies_file = "cookies.txt"

@app.route("/", methods=["GET", "POST"])
def index():
    title = None
    thumbnail = None
    resolutions = None
    link = None

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
            mode = request.form["mode"]
            quality = request.form["quality"]
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
                else:
                    ydl_opts = {
                        "format": f"bestvideo[height<={quality}]+bestaudio/best",
                        "outtmpl": f"downloads/%(title)s.%(ext)s",
                        "cookiefile": cookies_file,
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([link])
                title = "✅ Download complete! Check downloads folder."
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
