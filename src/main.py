"""Orquesta el pipeline completo: guion -> voz -> subtitulos -> video de fondo -> ensamblado -> subida."""
import sys
import traceback
import uuid
from pathlib import Path

from src import config
from src.script_generator import generate_script, save_used_topic
from src.tts import text_to_speech, transcribe_with_word_timestamps
from src.visuals import download_background_video
from src.video_builder import build_video
from src.youtube_uploader import upload_short


def run() -> None:
    run_id = uuid.uuid4().hex[:8]
    work_dir = config.OUTPUT_DIR / run_id
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/6] Generando guion (run_id={run_id})...")
    data = generate_script()
    print(f"  Tema: {data['topic']}")

    print("[2/6] Generando voz narrada...")
    audio_path = text_to_speech(data["script"], work_dir / "voz.mp3")

    print("[3/6] Transcribiendo audio para sincronizar subtitulos...")
    words = transcribe_with_word_timestamps(audio_path)
    if not words:
        raise RuntimeError("No se obtuvieron timestamps de palabras para los subtitulos")

    print("[4/6] Descargando video de fondo...")
    background_path = download_background_video(data["keywords"], work_dir / "fondo.mp4")

    print("[5/6] Ensamblando video final...")
    final_video_path, music_attribution = build_video(background_path, audio_path, words, work_dir / "short_final.mp4")

    description = data["description"]
    if music_attribution:
        description = f"{description}\n\n{music_attribution}"

    print("[6/6] Subiendo a YouTube...")
    url = upload_short(final_video_path, data["title"], description, data["tags"])

    save_used_topic(data["topic"])
    print(f"\n✅ Short publicado: {url}")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        print("❌ Error en el pipeline:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
