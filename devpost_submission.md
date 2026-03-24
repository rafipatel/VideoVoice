# VideoVoice: Education in Every Language, In Every Voice

## Inspiration
My primary inspiration comes from an unwavering interest in staying at the forefront of the rapidly evolving AI field—specifically the convergence of multimodal AI involving text, audio, and video. I recognized the profound potential this technology has to democratize knowledge and genuinely help people. We understand the world differently in our mother tongue; concepts click faster and ideas sink deeper. 

Unfortunately, high-quality educational content on platforms like YouTube is often gatekept by language barriers. Standard subtitles aren't enough when visual attention is required for learning. I wanted to build a tool that completely shatters this barrier by allowing anyone to learn from the world's best educators in their native language—while preserving the original speaker's emotional intonation and voice characteristics.

## What it does
**VideoVoice** is an end-to-end, automated video translation pipeline. You simply upload any educational video and select a target language (out of 23 supported languages). In minutes, VideoVoice returns a fully re-voiced version of the video. It extracts the audio, precisely transcribes and aligns the speech, leverages cutting-edge LLMs to translate the transcript naturally, and then uses a state-of-the-art multilingual Voice Cloning TTS engine to synthesize the new audio using the *original speaker's exact voice*. Finally, it synchronizes the generated audio to the original visual timestamps (stretching/padding as necessary) and merges it back into the high-quality video file.

## How I built it
I architected the project as a modular 6-step Python pipeline tailored to run both in the cloud and natively accelerated on Apple Silicon (M3 Mac / MPS backend):

1. **Extraction (Step 1):** I use `ffmpeg-python` to strip a high-quality 16kHz WAV track from the input video.
2. **Transcription & Alignment (Step 2):** I use the **Pollinations API** (`whisper-large-v3`) with `verbose_json` to extract text and highly accurate word-level timestamps. As a robust fallback for local inference, I integrated Apple's `mlx-whisper` (Medium model) running efficiently on my M3 GPU.
3. **Translation (Step 3):** I use the **Pollinations Chat Completions API** (via OpenAI compatible endpoints) with a strict system prompt to idiomatically translate subtitle segments while preserving mathematical/technical formatting and Array JSON structures.
4. **Multilingual Voice Cloning (Step 4):** I utilize the **Resemble AI Chatterbox Multilingual** model (`ChatterboxMultilingualTTS`). I feed the model a voice sample from the original video, extracting conditioning latents (via `VoiceEncoder` and `S3Gen`), and autoregressively synthesize the translated text natively on the MPS GPU (`max_new_tokens` dynamically scaled to prevent sequence stalling).
5. **Synchronization (Step 5):** Using `pydub` and custom `ffmpeg` audio filters (`atempo` / `apad`), I dynamically stretch, speed up, or pad silence into the generated TTS segments so they perfectly match the $\Delta t$ ($t_{end} - t_{start}$) of the original Whisper timestamps.
6. **A/V Stitching (Step 6):** Finally, I merge the synthesized audio track back onto the original visual stream frame-accurately.

The frontend is served via a premium, dark-mode static web page (`HTML/CSS/JS`) that embeds a specialized **Gradio** application for the interactive drag-and-drop backend demo.

## Challenges I ran into
Building a multimodal pipeline is inherently complex due to mismatched states, unconstrained models, and hardware limitations. 
- **The "Infinite Babbling" TTS issue:** My voice cloning model (Chatterbox) would occasionally fail to predict the EOS (End of Sequence) token and hallucinate noise or silence for thousands of steps, stalling the pipeline. I solved this by diving into the open-source pip package and monkey-patching `mtl_tts.py` to accept a dynamic `max_new_tokens` cutoff, calculated mathematically based on the original audio segment length ($\text{Tokens}_{max} = \max(150, \text{duration} \times 75 \text{Hz} \times 1.5)$). This made my pipeline **3x-5x faster**.
- **Hardware Deserialization:** I heavily utilized my Mac M3's Metal GPU (MPS). However, loading open-source models trained on CUDA caused `RuntimeError: Attempting to deserialize object on a CUDA device`. I successfully implemented custom torch loading hooks natively inside the pip library to map tensors to CPU safely before moving them to MPS.
- **Audio Synchronization Drift:** Natural speech translated into Spanish or German is often much longer than the original English spoken sequence. Audio segments began to overlap. I spent a profound amount of time engineering an `ffmpeg` temporal stretching layer to enforce synchronization boundaries without sounding robotic.

## Accomplishments that I'm proud of
- **End-to-end Autonomy:** Taking a raw MP4 file and outputting a perfectly translated, voice-cloned video completely autonomously in one pass.
- **Flawless Fallback Architecture:** Having my pipeline beautifully pivot between cloud API inference (Pollinations) and local Metal-accelerated generation (`mlx-whisper` and `chatterbox`) gives the app unparalleled resilience.
- **Performance Optimizations:** Hot-fixing the upstream open-source TTS library to support dynamic token cutoffs and CPU mapping shows my dedication to fixing root-cause issues, not just wrapping APIs.

## What I learned
- The absolute power of flow-matching and autoregressive voice generation—it's incredible how accurately just a few seconds of contextual audio can map the entire prosody and timbre of a speaker into an entirely foreign language.
- The intricacies of robust API prompt engineering. Handling timestamps and JSON structures cleanly out of an LLM requires rigorous prompting to ensure no data is dropped. 
- Deep expertise in audio/video manipulation using `ffmpeg` filters natively in Python.

## What's next for VideoVoice
- **Real-time Streaming:** Optimizing the model weights using PEFT/LoRA to stream the video processing on-the-fly rather than waiting for batch processing.
- **Lip-syncing Automation:** Adding a computer vision step that visually morphs the educator's mouth movements to match the newly synthesized audio phonemes for perfect uncanny-valley removal.
- **Deploying as a Browser Extension:** Building an overlay extension for YouTube or Coursera that automatically replaces the audio stream dynamically while watching.
