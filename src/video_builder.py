"""Ensambla el short final con cortes dinámicos de video, transiciones, efecto zoom (Ken Burns) y subtítulos de alto impacto."""
import math
from pathlib import Path
import numpy as np
from PIL import Image
from moviepy import (
    VideoFileClip,
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    concatenate_videoclips,
    TextClip,
)
from moviepy.audio.fx import MultiplyVolume
from moviepy.video.fx import FadeIn, Loop
from src import config
from src.music import pick_background_music


def _crop_to_vertical(clip: VideoFileClip) -> VideoFileClip:
    target_ratio = config.VIDEO_WIDTH / config.VIDEO_HEIGHT
    current_ratio = clip.w / clip.h

    if current_ratio > target_ratio:
        new_width = int(clip.h * target_ratio)
        x1 = (clip.w - new_width) // 2
        clip = clip.cropped(x1=x1, y1=0, x2=x1 + new_width, y2=clip.h)
    else:
        new_height = int(clip.w / target_ratio)
        y1 = (clip.h - new_height) // 2
        clip = clip.cropped(x1=0, y1=y1, x2=clip.w, y2=y1 + new_height)

    return clip.resized((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))


def _apply_ken_burns(clip: VideoFileClip, zoom_rate: float = 0.07, zoom_in: bool = True) -> VideoFileClip:
    """Aplica un efecto de zoom lento y continuo para darle dinamismo a tomas estáticas."""
    d = clip.duration
    w, h = clip.w, clip.h

    def effect(get_frame, t):
        frame = np.asarray(get_frame(t), dtype=np.uint8)
        progress = (t / d) if d and d > 0 else 0
        factor = 1.0 + (zoom_rate * progress if zoom_in else zoom_rate * (1.0 - progress))
        new_w, new_h = int(w * factor), int(h * factor)
        img = Image.fromarray(frame).resize((new_w, new_h), Image.Resampling.BILINEAR)
        x1 = (new_w - w) // 2
        y1 = (new_h - h) // 2
        cropped = img.crop((x1, y1, x1 + w, y1 + h))
        return np.array(cropped)

    return clip.with_updated_frame_function(lambda t: effect(clip.get_frame, t))


def _build_background_sequence(background_inputs: list[Path] | Path, total_duration: float) -> tuple[VideoFileClip, list[VideoFileClip]]:
    """Construye una pista de video compuesta por múltiples tomas cortas (3-5s) con transiciones suaves."""
    paths = [background_inputs] if isinstance(background_inputs, Path) else list(background_inputs)
    if not paths:
        raise ValueError("No se proporcionaron videos de fondo")

    # Duración ideal por toma: entre 3.5 y 5.5 segundos
    shot_duration = 4.2
    num_shots_needed = max(1, math.ceil(total_duration / shot_duration))

    raw_clips = []
    processed_segments = []

    try:
        for i in range(num_shots_needed):
            path = paths[i % len(paths)]
            is_image = path.suffix.lower() in {".jpg", ".jpeg", ".png"}
            clip = ImageClip(str(path)).with_duration(shot_duration) if is_image else VideoFileClip(str(path))
            raw_clips.append(clip)

            clip = _crop_to_vertical(clip)
            # Asegurar que el clip dure al menos la duración de la toma
            if clip.duration < shot_duration:
                clip = clip.with_effects([Loop(duration=shot_duration)])
            segment = clip.subclipped(0, shot_duration)

            # Alternar zoom in y zoom out para dinamismo
            zoom_in = (i % 2 == 0)
            segment = _apply_ken_burns(segment, zoom_rate=0.07, zoom_in=zoom_in)

            # Transición suave entre tomas
            if i > 0:
                segment = segment.with_effects([FadeIn(0.25)])

            processed_segments.append(segment)

        concat = concatenate_videoclips(processed_segments, method="compose")
        final_background = concat.subclipped(0, total_duration).without_audio()
        return final_background, raw_clips
    except Exception:
        # En caso de fallo, limpiar clips abiertos
        for c in raw_clips:
            try:
                c.close()
            except Exception:
                pass
        raise


def _group_words_into_phrases(words: list[dict], max_words: int = 3) -> list[dict]:
    """Agrupa palabras con timestamps en frases cortas de alto impacto (estilo Shorts virales)."""
    phrases = []
    for i in range(0, len(words), max_words):
        chunk = words[i : i + max_words]
        phrases.append(
            {
                "text": " ".join(w["word"] for w in chunk).strip(),
                "start": chunk[0]["start"],
                "end": chunk[-1]["end"],
            }
        )
    return phrases


def _build_subtitle_clips(words: list[dict]) -> list[TextClip]:
    """Genera subtítulos llamativos con colores alternados y contorno oscuro para legibilidad total."""
    clips = []
    # Paleta de colores virales: Amarillo Eléctrico, Verde Neón, Blanco Puro
    palette = ["#FFE600", "#00FF66", "#FFFFFF"]

    for idx, phrase in enumerate(_group_words_into_phrases(words, max_words=3)):
        duration = max(phrase["end"] - phrase["start"], 0.1)
        color = palette[idx % len(palette)]

        text_clip = (
            TextClip(
                font=config.FONT_PATH,
                text=phrase["text"].upper(),
                font_size=82,
                color=color,
                stroke_color="black",
                stroke_width=6,
                method="caption",
                size=(int(config.VIDEO_WIDTH * 0.88), None),
                text_align="center",
                margin=(20, 20, 20, 20),
            )
            .with_start(phrase["start"])
            .with_duration(duration)
            .with_position(("center", int(config.VIDEO_HEIGHT * 0.54)))
        )
        clips.append(text_clip)
    return clips


def _loop_audio_to_duration(clip: AudioFileClip, duration: float) -> AudioFileClip:
    if clip.duration <= 0:
        return clip
    return clip.subclipped(0, min(clip.duration, duration))


def build_video(
    background_input: list[Path] | Path,
    audio_path: Path,
    words: list[dict],
    out_path: Path,
) -> tuple[Path, str | None]:
    audio_clip = AudioFileClip(str(audio_path))
    duration = min(audio_clip.duration, config.MAX_DURATION_SECONDS)
    voice_clip = audio_clip.subclipped(0, duration)

    music_clip = None
    music_path, music_attribution = pick_background_music(category="news")
    if music_path:
        music_clip = AudioFileClip(music_path)
        music_clip = _loop_audio_to_duration(music_clip, duration)
        music_clip = music_clip.with_effects([MultiplyVolume(0.12)])  # De fondo, volumen sutil
        final_audio = CompositeAudioClip([music_clip, voice_clip])
    else:
        final_audio = voice_clip

    background_clip, raw_clips = _build_background_sequence(background_input, duration)
    subtitle_clips = _build_subtitle_clips(words)

    final = CompositeVideoClip(
        [background_clip, *subtitle_clips],
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
    )
    final = final.with_audio(final_audio)
    final = final.with_duration(duration)

    final.write_videofile(
        str(out_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        threads=4,
        preset="medium",
        ffmpeg_params=["-pix_fmt", "yuv420p"],
    )

    # Limpieza de recursos
    audio_clip.close()
    if music_clip:
        music_clip.close()
    background_clip.close()
    for c in raw_clips:
        try:
            c.close()
        except Exception:
            pass
    final.close()

    return out_path, music_attribution

