"""Ensambla el short final: video de fondo + audio narrado + subtitulos animados palabra por palabra."""
from pathlib import Path
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
    TextClip,
)
from moviepy.audio.fx import MultiplyVolume
from moviepy.video.fx import Loop
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


def _loop_to_duration(clip: VideoFileClip, duration: float) -> VideoFileClip:
    if clip.duration < duration:
        clip = clip.with_effects([Loop(duration=duration)])
    return clip.subclipped(0, duration)


def _loop_audio_to_duration(clip: AudioFileClip, duration: float) -> AudioFileClip:
    if clip.duration <= 0:
        return clip
    return clip.subclipped(0, min(clip.duration, duration))


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
                font=config.FONT_PATH,
                text=phrase["text"].upper(),
                font_size=80,
                color="white",
                stroke_color="black",
                stroke_width=4,
                method="caption",
                size=(int(config.VIDEO_WIDTH * 0.85), None),
                text_align="center",
                margin=(30, 30, 30, 30),
            )
            .with_start(phrase["start"])
            .with_duration(duration)
            .with_position(("center", "center"))
        )
        clips.append(text_clip)
    return clips


def build_video(background_path: Path, audio_path: Path, words: list[dict], out_path: Path) -> tuple[Path, str | None]:
    audio_clip = AudioFileClip(str(audio_path))
    duration = min(audio_clip.duration, config.MAX_DURATION_SECONDS)
    voice_clip = audio_clip.subclipped(0, duration)

    music_path, music_attribution = pick_background_music()
    if music_path:
        music_clip = AudioFileClip(music_path)
        music_clip = _loop_audio_to_duration(music_clip, duration)
        music_clip = music_clip.with_effects([MultiplyVolume(0.12)])  # de fondo, bajo volumen
        final_audio = CompositeAudioClip([music_clip, voice_clip])
    else:
        final_audio = voice_clip

    background_clip = VideoFileClip(str(background_path))
    background_clip = _crop_to_vertical(background_clip)
    background_clip = _loop_to_duration(background_clip, duration)
    background_clip = background_clip.without_audio()

    subtitle_clips = _build_subtitle_clips(words)

    final = CompositeVideoClip([background_clip, *subtitle_clips], size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT))
    final = final.with_audio(final_audio)
    final = final.with_duration(duration)

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

    return out_path, music_attribution
