# VideoVoice

**AI-powered short video translation with zero-shot voice cloning.**

Translate any short video (≤60s) into 23+ languages while preserving the original speaker's voice. Paste an Instagram Reel, YouTube Short, or upload any video file.

---

## How It Works

1. **Upload or Paste URL** — Drop a video file or paste a social media link
2. **AI Translates & Clones** — Our 6-step pipeline transcribes, translates, and synthesizes new speech using a voice clone of the original speaker
3. **Preview & Download** — Watch your translated video and download in full quality

### Pipeline Architecture

```
Video → Extract Audio → Whisper Transcription → LLM Translation
      → Chatterbox Voice Clone + TTS → Time-Sync → Final Merge
```

| Step | Component | Description |
|------|-----------|-------------|
| 1 | FFmpeg | Extract audio track from video |
| 2 | Whisper Large V3 | Transcribe with word-level timestamps |
| 3 | GPT-4o-mini | Context-aware subtitle translation |
| 4 | Chatterbox Multilingual | Zero-shot voice cloning + TTS synthesis |
| 5 | Dynamic Time-Stretch | Align translated audio to original timing |
| 6 | FFmpeg | Merge new audio track back into video |

---

## Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg installed (`brew install ffmpeg` on macOS)
- OpenAI API key

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/VideoVoice.git
cd VideoVoice

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run the Server

```bash
python server.py
```

The app will be available at [http://localhost:8000](http://localhost:8000).

### CLI Usage

You can also run the pipeline directly:

```bash
python pipeline.py --input data/my_video.mp4 --target-lang Spanish
```

---

## API Reference

### `POST /api/jobs`

Submit a video for translation.

**Form Data:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | * | Video file (MP4, MOV, WebM, ≤50MB) |
| `url` | String | * | Instagram Reel or YouTube Short URL |
| `target_language` | String | Yes | Target language name (e.g., "Spanish") |
| `source_language` | String | No | Source language ISO code (default: "en") |

\* Either `file` or `url` is required.

**Response:**
```json
{ "job_id": "abc123", "status": "queued" }
```

### `GET /api/jobs/{job_id}`

SSE endpoint streaming real-time pipeline progress.

**Events:**
```json
{ "type": "progress", "message": "Step 3/6: Translating...", "step": 3 }
{ "type": "complete", "elapsed": 47 }
{ "type": "error", "message": "Pipeline failed" }
```

### `GET /api/jobs/{job_id}/result`

Download the translated video (MP4).

---

## Supported Languages

Spanish, French, German, Hindi, Portuguese, Italian, Japanese, Chinese, Arabic, Korean — and more.

---

## Project Structure

```
VideoVoice/
├── server.py            # FastAPI backend
├── pipeline.py          # Core translation pipeline
├── steps/               # Pipeline step modules
│   ├── s1_extract_audio.py
│   ├── s2_transcribe.py
│   ├── s3_translate.py
│   ├── s4_tts.py
│   ├── s5_sync.py
│   └── s6_merge.py
├── frontend/            # Static web UI
│   ├── index.html
│   ├── style.css
│   └── app.js
├── requirements.txt
├── .env.example
└── README.md
```

---

## Deployment

### AWS (Recommended for GPU)

```bash
# On a g4dn.xlarge instance
sudo apt update && sudo apt install -y ffmpeg
pip install -r requirements.txt
python server.py
```

Recommended: use `systemd` service for auto-restart, CloudFront for CDN, S3 for video storage with 24h auto-delete lifecycle policy.

---

## License

MIT License — see [LICENSE](LICENSE).
