# YouTube Summarizer (Groq)

Simple project:
1. Paste YouTube URL
2. Generate transcript (Whisper)
3. Generate summary (Llama)

## Stack

- Backend: FastAPI
- Download: `yt-dlp` (+ local `ffmpeg`)
- Transcription: Groq Whisper (`whisper-large-v3`)
- Summary: Groq Llama (`llama-3.3-70b-versatile`)
- Frontend: HTML/CSS/JS served by FastAPI

## Setup

From project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Copy env file:

```bash
cp backend/.env.example backend/.env
```

Then add your key in `backend/.env`:

```env
GROQ_API_KEY=your_key_here
```

## Run

```bash
uvicorn backend.main:app --reload
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Notes

- You need `ffmpeg` installed on your machine for audio extraction.
- Long videos take longer and cost more API usage.
- This is an MVP (single endpoint: `/api/summarize`).
