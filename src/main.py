"""Orquesta el pipeline completo: guion -> voz -> subtitulos -> video de fondo -> ensamblado -> subida."""
import sys
import traceback
import uuid
from pathlib import Path

from src import config
from src.script_generator import generate_script, save_used_topic
from src.tts import text_to_speech, transcribe_with_word_timestamps
from src.visuals import download_background_videos, download_person_images
from src.thumbnail import build_thumbnail
from src.video_builder import build_video
from src.youtube_uploader import upload_short


def run() -> None:
    run_id = uuid.uuid4().hex[:8]
    work_dir = config.OUTPUT_DIR / run_id
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/7] Generando guion (run_id={run_id})...")
    data = generate_script()
    print(f"  Tema: {data['topic']}")

    print("[2/7] Generando voz narrada...")
    audio_path = text_to_speech(data["script"], work_dir / "voz.mp3")

    print("[3/7] Transcribiendo audio para sincronizar subtitulos...")
    words = transcribe_with_word_timestamps(audio_path)
    if not words:
        raise RuntimeError("No se obtuvieron timestamps de palabras para los subtitulos")

    print("[4/7] Descargando videos de fondo y fotos reales del personaje...")
    background_paths = download_background_videos(data["keywords"], work_dir / "clips", min_clips=5)
    person_photos = download_person_images("Abelardo de la Espriella", work_dir / "persona", max_images=3)
    if person_photos:
        # Intercalar las fotos reales al inicio para captar la atencion desde el primer corte
        background_paths = person_photos + background_paths
    else:
        print("  [Aviso] No se encontraron fotos del personaje, se usará solo video de stock genérico.")

    print("[5/7] Ensamblando video final (tomas múltiples, zoom y subtítulos de alto impacto)...")
    final_video_path, music_attribution = build_video(background_paths, audio_path, words, work_dir / "short_final.mp4")

    print("[6/7] Generando miniatura con foto del personaje...")
    thumbnail_path = None
    if person_photos:
        thumbnail_path = build_thumbnail(person_photos[0], data["title"], work_dir / "thumbnail.jpg")
    else:
        print("  [Aviso] No se encontró foto disponible, se usará la miniatura automática de YouTube.")

    description = data["description"]
    if music_attribution:
        description = f"{description}\n\n{music_attribution}"

    print("[7/7] Subiendo a YouTube...")
    url = upload_short(final_video_path, data["title"], description, data["tags"], thumbnail_path)

    save_used_topic(data["topic"])
    print(f"\n✅ Short publicado: {url}")


if __name__ == "__main__":
    try:
        run()
    except Exception:
        print("❌ Error en el pipeline:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
