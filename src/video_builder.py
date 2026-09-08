"""Ensambla el short final: video de fondo + audio narrado + subtitulos animados palabra por palabra."""
from pathlib import Path
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    TextClip,
    vfx,
)
from src import config


def _crop_to_vertical(clip: VideoFileClip) -> VideoFileClip:
    target_ratio = config.VIDEO_WIDTH / config.VIDEO_HEIGHT
    current_ratio = clip.w / clip.h

    if current_ratio > target_ratio:
        new_width = int(clip.h * target_ratio)
        x1 = (clip.w - new_width) // 2
        clip = clip.crop(x1=x1, y1=0, x2=x1 + new_width, y2=clip.h)
    else:
        new_height = int(clip.w / target_ratio)
        y1 = (clip.h - new_height) // 2
        clip = clip.crop(x1=0, y1=y1, x2=clip.w, y2=y1 + new_height)

    return clip.resize((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))


def _loop_to_duration(clip: VideoFileClip, duration: float) -> VideoFileClip:
    if clip.duration < duration:
        clip = clip.fx(vfx.loop, duration=duration)
    return clip.subclip(0, duration)


def _group_words_into_phrases(words: list[dict], max_words: int = 4) -> list[dict]:
    """Agrupa palabras con timestamps en frases cortas para subtitular estilo Shorts."""
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
    clips = []
    for phrase in _group_words_into_phrases(words):
        duration = max(phrase["end"] - phrase["start"], 0.1)
        text_clip = (
            TextClip(
                phrase["text"].upper(),
                fontsize=80,
                font=config.FONT_PATH,
                color="white",
                stroke_color="black",
                stroke_width=4,
                method="caption",
                size=(int(config.VIDEO_WIDTH * 0.85), None),
                align="center",
            )
            .set_start(phrase["start"])
            .set_duration(duration)
            .set_position(("center", "center"))
        )
        clips.append(text_clip)
    return clips


def build_video(background_path: Path, audio_path: Path, words: list[dict], out_path: Path) -> Path:
    audio_clip = AudioFileClip(str(audio_path))
    duration = min(audio_clip.duration, config.MAX_DURATION_SECONDS)

    background_clip = VideoFileClip(str(background_path))
    background_clip = _crop_to_vertical(background_clip)
    background_clip = _loop_to_duration(background_clip, duration)
    background_clip = background_clip.without_audio()

    subtitle_clips = _build_subtitle_clips(words)

    final = CompositeVideoClip([background_clip, *subtitle_clips], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
    final = final.set_audio(audio_clip.subclip(0, duration))
    final = final.set_duration(duration)

    final.write_videofile(
        str(out_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
    )

    audio_clip.close()
    background_clip.close()
    final.close()

    return out_path
