<div align="center">
  <img src="https://img.shields.io/badge/Track-Economic_Empowerment_&_Education-blue" alt="Track Badge">
  <img src="https://img.shields.io/badge/Python-3.11-blue" alt="Python Badge">
  <img src="https://img.shields.io/badge/Accelerated-Apple_Silicon_MPS-orange" alt="Mac Badge">
  <h1>🌍 VideoVoice 🗣️</h1>
  <p><b>Education in every language. In every voice.</b></p>
</div>
<img width="1255" height="823" alt="Screenshot 2026-03-24 at 19 32 16" src="https://github.com/user-attachments/assets/fe7f2182-8137-4234-a63e-17f62680b66a" />

<br>

**VideoVoice** is an end-to-end, fully automated video translation pipeline built for Track 3 (Economic Empowerment & Education). It takes any educational video, precise-transcribes it, translates the dialogue natively into one of 23 supported languages, and synthesizes a **Zero-Shot Voice Clone** of the original educator speaking their new language. 

The original visual timestamps are retained, and the new multilingual audio is dynamically time-stretched or padded to perfectly sync with the original speaker's video without drift.

## 🚀 Features

* **Autonomous Pipeline:** Drag-and-drop a `.mp4` and get a fully translated MP4 out. No intermediate steps required.
* **Flawless Fallback Architecture:** Cloud-API transcription using `whisper-large-v3` with an automatic, lightning-fast local fallback to Apple's `mlx-whisper` (Whisper-Medium) natively on your M3 GPU.
* **Intelligent JSON Prompting:** Integrates Pollinations.AI for deep translation capabilities, ensuring JSON array data structures remain perfect across translations.
* **Multilingual Voice Cloning:** Leverages the open-source **Resemble AI Chatterbox Multilingual** engine, natively patched and accelerated using PyTorch MPS on Apple Silicon.
* **Dynamic Time Alignment:** Features a robust audio sync engine using recursive temporal math and `ffmpeg/pydub` cross-fading to enforce frame-accurate alignments.
* **Premium Web UI:** Includes a beautiful Vanilla JS dark-mode frontend housing the interactive Gradio demo application.

---

## 🛠️ Architecture (The 6-Step Pipeline)
The pipeline is entirely modular and broken down into `steps/`:
1. `s1_extract_audio.py` - Rips a 16kHz Mono WAV sequence from the video.
2. `s2_transcribe.py` - Cloud transcribes (or MLX local) for word/phrase-level timestamps.
3. `s3_translate.py` - Translates transcribed text array while preserving semantic meaning and technical jargon.
4. `s4_tts.py` - Voice-clones the original audio and synthesizes translated strings into raw waveform chunks.
5. `s5_sync.py` - Dynamically time-stretches/pads synthesized chunks to match original $\Delta t$ durations and stitches them.
6. `s6_merge.py` - Injects the new synthesized audio stream back into the visual MP4 frame-losslessly.

---

## 💻 Tech Stack
* **Python, JS, HTML, CSS**
* **Frameworks:** Gradio (Backend UI), custom frontend
* **APIs:** Pollinations.AI API
* **Local ML:** `mlx-whisper`, `chatterbox-multilingual` TTS, `pytorch`
* **Media:** `ffmpeg`, `ffmpeg-python`, `pydub`

---

## ⚙️ Setup & Installation

**1. Clone the repository:**
```bash
git clone https://github.com/your-username/videovoice.git
cd videovoice
```

**2. Setup the Conda Environment:**
This project relies on `torch`, `gradio`, and heavy audio dependencies. An isolated environment is required.
```bash
conda create -n video-translate python=3.11 -y
conda activate video-translate
```

**3. Install Dependencies:**
```bash
# Core python packages
pip install -r requirements.txt

# You MUST install ffmpeg on your system for video merging to work:
# macOS
brew install ffmpeg
```

**4. Environment Variables (`.env`)**
Create a `.env` file in the root folder with your Pollinations API keys (used for cloud transcribing and translating).
```env
POLLEN_API_KEY=your_key_here
HF_TOKEN=your_huggingface_token  # (Optional: for pulling specific models)
```

---

## ▶️ Usage

### Using the Web UI (Gradio)
To run the interactive UI with streaming progress logs:
```bash
conda activate video-translate
python app.py
```
* **Frontend Site:** Open `frontend/index.html` in your web browser for the full premium experience.
* **Direct UI:** Open `http://localhost:7860` in your web browser.

### Using the CLI Pipeline
If you prefer running headless or batch-processing translation jobs:
```bash
conda activate video-translate
python pipeline.py --input data/test_video.mp4 --output data/translated_video.mp4 --target-language "Spanish"
```
