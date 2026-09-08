"""Busca y descarga un video vertical de stock desde Pexels segun palabras clave."""
import random
from pathlib import Path
import requests
from src import config

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"


def download_background_video(keywords: list[str], out_path: Path) -> Path:
    headers = {"Authorization": config.PEXELS_API_KEY}
    query = " ".join(keywords[:3]) if keywords else "nature"

    response = requests.get(
        PEXELS_SEARCH_URL,
        headers=headers,
        params={"query": query, "orientation": "portrait", "per_page": 15},
        timeout=30,
    )
    response.raise_for_status()
    videos = response.json().get("videos", [])
    if not videos:
        # fallback generico si no hay resultados para las keywords
        response = requests.get(
            PEXELS_SEARCH_URL,
            headers=headers,
            params={"query": "abstract background", "orientation": "portrait", "per_page": 15},
            timeout=30,
        )
        response.raise_for_status()
        videos = response.json().get("videos", [])

    if not videos:
        raise RuntimeError("No se encontraron videos de fondo en Pexels")

    video = random.choice(videos)
    # elegir el archivo de video vertical de mejor calidad disponible
    files = sorted(
        [f for f in video["video_files"] if f.get("width") and f["width"] <= f.get("height", 0)],
        key=lambda f: f.get("width", 0),
        reverse=True,
    ) or video["video_files"]
    video_url = files[0]["link"]

    with requests.get(video_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return out_path
