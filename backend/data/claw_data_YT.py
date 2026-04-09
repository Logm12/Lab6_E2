import yt_dlp
import pandas as pd
import os
import re
import time
import random
from typing import List, Dict
from youtube_transcript_api import YouTubeTranscriptApi
from concurrent.futures import ThreadPoolExecutor, as_completed
from faster_whisper import WhisperModel

# =========================
# CONFIG
# =========================
CSV_PATH = "vinfast_data.csv"
MAX_WORKERS = 3   # ⚠️ đừng để cao quá (bị block)

VINFAST_MODELS = [
    "VinFast Evo200", "VinFast Feliz S",
    "VinFast Klara S", "VinFast Vento S"
]

# =========================
# LOAD MODEL GPU
# =========================
print("🚀 Loading faster-whisper...")
model = WhisperModel(
    "small",
    device="cuda",
    compute_type="float16"
)

# =========================
# CLEAN TEXT (GIỮ NGUYÊN EN)
# =========================
def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = text.replace(" ,", ",").replace(" .", ".")
    return text.strip()

# =========================
# SEARCH
# =========================
def search_youtube(query: str, limit: int = 10):
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "js_runtimes": {"node": {"path": "/usr/bin/node"}}
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)

    return [{"title": e["title"], "video_id": e["id"]} for e in result["entries"]]

# =========================
# TRANSCRIPT
# =========================
def get_transcript(video):
    video_id = video["video_id"]
    filename = f"{video_id}.mp3"

    try:
        # 👉 random sleep tránh block
        time.sleep(random.uniform(1, 3))

        # 👉 1. subtitle (ưu tiên EN)
        try:
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, languages=['en', 'vi']
            )
            text = " ".join([t["text"] for t in transcript])
            return clean_text(text)
        except:
            pass

        # 👉 2. download audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': filename,
            'quiet': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'geo_bypass': True,

            # 🔥 FIX JS runtime
            'js_runtimes': {'node': {'path': '/usr/bin/node'}},

            # 🔥 tránh bị block
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

        # 👉 3. whisper GPU
        segments, _ = model.transcribe(
            filename,
            language=None,      # ✅ auto detect (FIX LỖI)
            beam_size=3,
            vad_filter=True
        )

        text = " ".join([seg.text for seg in segments])
        return clean_text(text)

    except Exception as e:
        print(f"❌ {video_id} error: {e}")
        return ""

    finally:
        if os.path.exists(filename):
            os.remove(filename)

# =========================
# LOAD CSV
# =========================
def load_existing():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        return df.to_dict("records"), set(df["video_id"])
    return [], set()

# =========================
# SAVE NGAY
# =========================
def save_row(row):
    df = pd.DataFrame([row])

    if not os.path.exists(CSV_PATH):
        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    else:
        df.to_csv(CSV_PATH, mode='a', header=False, index=False, encoding="utf-8-sig")

# =========================
# PARALLEL
# =========================
def process_videos(videos, model_name, existing_ids):

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(get_transcript, v): v
            for v in videos if v["video_id"] not in existing_ids
        }

        for future in as_completed(futures):
            v = futures[future]

            try:
                text = future.result()

                if text:
                    row = {
                        "model": model_name,
                        "video_title": v["title"],
                        "video_id": v["video_id"],
                        "transcript": text
                    }

                    save_row(row)
                    existing_ids.add(v["video_id"])

                    print(f"💾 Saved: {v['title']}")

            except Exception as e:
                print(f"❌ Failed: {v['title']} | {e}")

# =========================
# MAIN
# =========================
def main():
    print("🚀 Start crawling...")

    _, existing_ids = load_existing()

    for model_name in VINFAST_MODELS:
        print(f"\n🔎 {model_name}")

        videos = search_youtube(model_name + " review", limit=10)

        process_videos(videos, model_name, existing_ids)

    print("\n✅ DONE")

    # ⬇️ download file
    from google.colab import files
    files.download(CSV_PATH)

# =========================
if __name__ == "__main__":
    main()