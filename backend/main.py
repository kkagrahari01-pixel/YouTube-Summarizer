import os
import tempfile
from pathlib import Path

import yt_dlp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from groq import Groq
from pydantic import BaseModel, Field

ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_FILE)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

WHISPER_MODEL = "whisper-large-v3"
SUMMARY_MODEL = "llama-3.3-70b-versatile"


class SummarizeRequest(BaseModel):
    youtube_url: str = Field(..., description="A valid YouTube URL")


app = FastAPI(title="YouTube Summarizer API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Missing GROQ_API_KEY. Add it to backend/.env first.",
        )
    return Groq(api_key=api_key)


def is_youtube_url(url: str) -> bool:
    lowered = url.lower()
    return "youtube.com" in lowered or "youtu.be" in lowered


def download_audio(youtube_url: str, output_dir: Path) -> tuple[Path, str]:
    output_template = str(output_dir / "%(id)s.%(ext)s")
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(youtube_url, download=True)
        video_title = info.get("title", "Untitled video")
        video_id = info.get("id")
        audio_path = output_dir / f"{video_id}.mp3"

    if not audio_path.exists():
        raise HTTPException(status_code=500, detail="Audio download failed.")

    return audio_path, video_title


def transcribe_audio(client: Groq, audio_path: Path) -> str:
    with audio_path.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=WHISPER_MODEL,
            response_format="verbose_json",
        )
    return transcription.text.strip()


def summarize_text(client: Groq, transcript: str) -> str:
    if len(transcript.strip()) < 20:
        return "Transcript is too short to summarize."

    # Keep prompt size bounded for long videos.
    transcript_excerpt = transcript[:15000]

    prompt = (
        "Summarize the following YouTube transcript for a student.\n"
        "Output format:\n"
        "1) 5-8 key bullet points\n"
        "2) Short section: 'Action Items'\n"
        "3) Short section: 'One-line TL;DR'\n\n"
        "Transcript:\n"
        f"{transcript_excerpt}"
    )

    completion = client.chat.completions.create(
        model=SUMMARY_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "You are an expert learning assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content.strip()


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="frontend/index.html not found.")
    return FileResponse(index_file)


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/api/summarize")
def summarize_video(payload: SummarizeRequest) -> dict:
    if not is_youtube_url(payload.youtube_url):
        raise HTTPException(status_code=400, detail="Please provide a valid YouTube URL.")

    client = get_client()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        audio_path, video_title = download_audio(payload.youtube_url, temp_path)
        transcript = transcribe_audio(client, audio_path)
        summary = summarize_text(client, transcript)

    return {
        "video_title": video_title,
        "summary": summary,
        "transcript": transcript,
    }
