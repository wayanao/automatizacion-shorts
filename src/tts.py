"""Convierte texto a voz y transcribe con marcas de tiempo por palabra (para subtitulos), usando OpenAI."""
from pathlib import Path
from openai import OpenAI
from src import config


def text_to_speech(text: str, out_path: Path) -> Path:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    with client.audio.speech.with_streaming_response.create(
        model=config.TTS_MODEL,
        voice=config.TTS_VOICE,
        input=text,
        instructions=config.TTS_INSTRUCTIONS,
    ) as response:
        response.stream_to_file(out_path)
    return out_path


def transcribe_with_word_timestamps(audio_path: Path) -> list[dict]:
    """Devuelve una lista de {"word": str, "start": float, "end": float}."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=config.WHISPER_MODEL,
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )
    words = getattr(transcript, "words", None) or []
    return [{"word": w.word, "start": w.start, "end": w.end} for w in words]
