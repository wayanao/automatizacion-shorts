"""Elige una pista de musica de fondo local (CC BY 3.0, Kevin MacLeod / incompetech.com)."""
import random
from src import config

# nombre de archivo -> (titulo, autor, licencia) para dar atribucion en la descripcion
TRACKS = {
    "track1.mp3": "Wallpaper",
    "track2.mp3": "Sneaky Adventure",
    "track3.mp3": "Fluffing a Duck",
    "track4.mp3": "Carefree",
    "track5.mp3": "Deliberate Thought",
}

ATTRIBUTION_TEMPLATE = (
    'Musica: "{title}" de Kevin MacLeod (incompetech.com)\n'
    "Licencia: Creative Commons BY 3.0 (https://creativecommons.org/licenses/by/3.0/)"
)


def pick_background_music() -> tuple[str, str] | tuple[None, None]:
    """Devuelve (ruta_absoluta_al_mp3, texto_de_atribucion) o (None, None) si no hay pistas."""
    music_dir = config.ASSETS_DIR / "music"
    available = [f for f in TRACKS if (music_dir / f).exists()]
    if not available:
        return None, None

    filename = random.choice(available)
    track_path = str(music_dir / filename)
    attribution = ATTRIBUTION_TEMPLATE.format(title=TRACKS[filename])
    return track_path, attribution
