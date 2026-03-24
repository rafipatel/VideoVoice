"""
app.py — Gradio UI for the Video Translation Pipeline.

Run with:
    python app.py
Then open http://localhost:7860
"""
import gradio as gr
from pipeline import run_pipeline, LANGUAGE_CODES

LANGUAGES = list(LANGUAGE_CODES.keys())
SOURCE_LANGUAGES = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "Hindi": "hi",
    "German": "de",
    "Portuguese": "pt",
    "Italian": "it",
    "Japanese": "ja",
    "Chinese": "zh",
    "Arabic": "ar",
}


def gradio_pipeline(video_path, target_language, source_language_name):
    """Wrapper for Gradio: runs pipeline and streams log + returns output video."""
    if video_path is None:
        yield "⚠️ Please upload a video first.\n", None
        return

    source_lang_code = SOURCE_LANGUAGES.get(source_language_name, "en")
    stem = video_path.split("/")[-1].replace(".", "_")
    output_path = f"tmp/output_{stem}_{target_language.lower()}.mp4"

    log = ""
    final_video = None

    gen = run_pipeline(
        video_path=video_path,
        target_language=target_language,
        source_language=source_lang_code,
        output_path=output_path,
    )

    try:
        while True:
            msg = next(gen)
            log += msg
            yield log, None
    except StopIteration as e:
        final_video = e.value

    yield log, final_video


# ── UI Layout ────────────────────────────────────────────────────────────────
with gr.Blocks(
    title="🌐 VideoVoice — AI Video Translation",
    theme=gr.themes.Base(
        primary_hue="violet",
        secondary_hue="indigo",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    ),
    css="""
        body { background: #0f0f1a; }
        .gradio-container { max-width: 900px !important; margin: auto; }
        #title { text-align: center; margin-bottom: 8px; }
        #subtitle { text-align: center; color: #a0a0c0; margin-bottom: 32px; font-size: 1rem; }
        .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 16px; padding: 20px; }
        #log_box textarea { font-family: monospace; font-size: 0.85rem; background: #0a0a14 !important; color: #c0ffd0 !important; }
        #run_btn { background: linear-gradient(135deg, #7c3aed, #4f46e5) !important; font-size: 1.1rem !important; }
    """,
) as demo:
    gr.Markdown("# 🌐 VideoVoice", elem_id="title")
    gr.Markdown(
        "Re-voice any educational video in the learner's native language — preserving the original speaker's voice.",
        elem_id="subtitle",
    )

    with gr.Row():
        with gr.Column(scale=1, elem_classes="card"):
            video_input = gr.Video(label="📹 Upload Video", sources=["upload"])
            source_lang = gr.Dropdown(
                choices=list(SOURCE_LANGUAGES.keys()),
                value="English",
                label="🔤 Source Language",
            )
            target_lang = gr.Dropdown(
                choices=LANGUAGES,
                value="Spanish",
                label="🌍 Target Language",
            )
            run_btn = gr.Button("▶ Translate Video", variant="primary", elem_id="run_btn")

        with gr.Column(scale=1, elem_classes="card"):
            log_output = gr.Textbox(
                label="📋 Progress Log",
                lines=18,
                interactive=False,
                elem_id="log_box",
                placeholder="Pipeline progress will appear here...",
            )
            video_output = gr.Video(label="🎬 Translated Video")

    run_btn.click(
        fn=gradio_pipeline,
        inputs=[video_input, target_lang, source_lang],
        outputs=[log_output, video_output],
    )

    gr.Markdown(
        """
        ---
        **Pipeline:** Pollinations Whisper Large V3 → Pollinations LLM translation → Chatterbox TTS voice clone → FFmpeg sync & merge
        """,
        elem_id="footer",
    )

if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860, share=False)
