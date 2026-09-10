"""Elige una pista de musica de fondo local (CC BY 3.0, Kevin MacLeod / incompetech.com)."""
import random
from src import config

# nombre de archivo -> metadatos de la pista, incluye categoria para elegir el ambiente adecuado
# Agrega tus propios mp3 de estilo "noticiero" en assets/music/ con estos nombres y actualiza
# "title" con el nombre real de la pista para mantener la atribucion correcta.
TRACKS = {
    "news1.mp3": {"title": "PON_AQUI_EL_TITULO_REAL_1", "category": "news"},
    "news2.mp3": {"title": "PON_AQUI_EL_TITULO_REAL_2", "category": "news"},
    "news3.mp3": {"title": "PON_AQUI_EL_TITULO_REAL_3", "category": "news"},
    "track1.mp3": {"title": "Wallpaper", "category": "general"},
    "track2.mp3": {"title": "Sneaky Adventure", "category": "general"},
    "track3.mp3": {"title": "Fluffing a Duck", "category": "general"},
    "track4.mp3": {"title": "Carefree", "category": "general"},
    "track5.mp3": {"title": "Deliberate Thought", "category": "general"},
}

ATTRIBUTION_TEMPLATE = (
    'Musica: "{title}" de Kevin MacLeod (incompetech.com)\n'
    "Licencia: Creative Commons BY 3.0 (https://creativecommons.org/licenses/by/3.0/)"
)


def pick_background_music(category: str = "news") -> tuple[str, str] | tuple[None, None]:
    """Devuelve (ruta_absoluta_al_mp3, texto_de_atribucion) o (None, None) si no hay pistas.

    Prioriza pistas de la categoria pedida (por defecto "news"); si no hay ninguna disponible
    en disco, cae de vuelta a cualquier pista de la categoria "general".
    """
    music_dir = config.ASSETS_DIR / "music"

    def _available(cat: str) -> list[str]:
        return [f for f, meta in TRACKS.items() if meta["category"] == cat and (music_dir / f).exists()]

    available = _available(category) or _available("general")
    if not available:
        return None, None

    filename = random.choice(available)
    track_path = str(music_dir / filename)
    attribution = ATTRIBUTION_TEMPLATE.format(title=TRACKS[filename]["title"])
    return track_path, attribution
