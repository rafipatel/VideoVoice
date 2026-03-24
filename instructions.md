Got everything I need. Here's the updated brief with the Pollinations API section and code added:

---

# Hackathon Project Brief

## Track
**Track 3: Economic Empowerment & Education**

---

## Problem Statement
Quality education is gatekept by language. Humans understand concepts far better in their mother tongue, yet most high-quality educational content exists only in a handful of languages — locking out billions of learners.

---

## Solution: End-to-End Video Translation Pipeline

A tool that takes any educational video and re-voices it in the learner's native language, preserving the original speaker's voice.

---

## Pipeline (Step-by-Step)

1. **Input** — Accept a short video (demo: ~20 seconds)
2. **Audio Extraction** — Strip the audio track from the video
3. **Transcription** — Use Pollinations API (Whisper Large V3) with diarization to transcribe speech and identify individual speakers with timestamps
4. **Translation** — Translate the transcribed text into the target language
5. **Voice Cloning & TTS** — Use Resemble AI Chatterbox to clone the original speaker's voice and synthesise the translated text as speech
6. **Audio Sync** — Handle duration mismatches:
   - Translated audio longer than original → speed up playback
   - Translated audio shorter than original → pad with silence
   - Whisper diarization timestamps used to align sync per segment
7. **Output** — Merge the new audio back into the original video

---

## Key Technical Components

| Component | Tool |
|---|---|
| Transcription + Diarization | Pollinations API — Whisper Large V3 |
| Translation | TBD (e.g. Claude / DeepL) |
| Voice Cloning + TTS | Resemble AI Chatterbox |
| Audio/Video Processing | FFmpeg |

---

## Transcription: Pollinations API — Whisper Large V3

**Endpoint:** `POST https://gen.pollinations.ai/v1/audio/transcriptions`

**API Key:** Get yours at [enter.pollinations.ai](https://enter.pollinations.ai)

**Supported audio formats:** `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `wav`, `webm`

**Response formats:** `json`, `text`, `srt`, `verbose_json`, `vtt`


**API Keys:**
POLLEN_API_KEY_MAIN=sk_4q0kWflGY5LSgOIMtqe1OXXFfHKnFUhF

POLLEN_API_KEY_SECONDARY=sk_RqoKDXdjlpXVILTHUgVhMrYv6b9sw6DW 

**Python code:**

```python
import requests

def transcribe_audio(audio_file_path: str, language: str = "en") -> dict:
    url = "https://gen.pollinations.ai/v1/audio/transcriptions"

    with open(audio_file_path, "rb") as f:
        files = {"file": f}
        data = {
            "model": "whisper-large-v3",       # Whisper Large V3 ALPHA
            "language": language,               # ISO-639-1 e.g. "en", "hi", "fr"
            "response_format": "verbose_json",  # Includes timestamps per segment
            "temperature": 0,                   # Deterministic output
        }
        headers = {
            "Authorization": ""
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        return response.json()

# Usage
result = transcribe_audio("extracted_audio.mp3", language="en")

# Access transcript and segments (for diarization alignment)
print(result["text"])           # Full transcript
for segment in result.get("segments", []):
    print(segment["start"], segment["end"], segment["text"])
```

**Why `verbose_json`?** It returns per-segment timestamps (`start`, `end`, `text`) which are essential for syncing the translated audio back to the correct position in the video.

---

## Impact
Removes language as a barrier to education — enabling any learner to access content in their mother tongue, with natural-sounding, speaker-matched audio.