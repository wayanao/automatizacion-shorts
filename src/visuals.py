"""Busca y descarga múltiples videos verticales de stock desde Pexels según palabras clave."""
import random
import shutil
from pathlib import Path
import requests
from src import config

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
WIKIPEDIA_API_URL = "https://es.wikipedia.org/w/api.php"
_IGNORED_IMAGE_PATTERNS = ("commons-logo", "wiki", "icon", "edit-", "flag_of", "symbol", "padlock")


def download_person_images(name: str, output_dir: Path, max_images: int = 3) -> list[Path]:
    """Descarga varias fotos de licencia libre del personaje desde Wikipedia/Wikimedia para usarlas
    como tomas reales dentro del video (ademas de la miniatura)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        page_response = requests.get(
            WIKIPEDIA_API_URL,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": name,
                "gsrlimit": 1,
                "prop": "images",
                "imlimit": 30,
                "format": "json",
            },
            timeout=20,
        )
        page_response.raise_for_status()
        pages = page_response.json().get("query", {}).get("pages", {})
        file_titles = []
        for page in pages.values():
            for img in page.get("images", []):
                title = img.get("title", "")
                lower = title.lower()
                if not lower.endswith((".jpg", ".jpeg", ".png")):
                    continue
                if any(pattern in lower for pattern in _IGNORED_IMAGE_PATTERNS):
                    continue
                file_titles.append(title)
        if not file_titles:
            return []

        info_response = requests.get(
            WIKIPEDIA_API_URL,
            params={
                "action": "query",
                "titles": "|".join(file_titles[:20]),
                "prop": "imageinfo",
                "iiprop": "url|size",
                "format": "json",
            },
            timeout=20,
        )
        info_response.raise_for_status()
        info_pages = info_response.json().get("query", {}).get("pages", {})

        candidates = []
        for page in info_pages.values():
            for info in page.get("imageinfo", []):
                url = info.get("url")
                width = info.get("width", 0)
                if url and width >= 400:
                    candidates.append((width, url))
        candidates.sort(key=lambda c: c[0], reverse=True)

        downloaded = []
        for idx, (_, url) in enumerate(candidates[:max_images]):
            dest_path = output_dir / f"persona_{idx+1}.jpg"
            try:
                img_response = requests.get(url, timeout=30)
                img_response.raise_for_status()
                dest_path.write_bytes(img_response.content)
                downloaded.append(dest_path)
            except Exception as e:
                print(f"  [Aviso] Error descargando imagen {idx+1} del personaje: {e}")
        return downloaded
    except Exception as e:
        print(f"  [Aviso] No se pudieron obtener imagenes de Wikipedia: {e}")
        return []


def _search_videos_for_query(query: str, per_page: int = 10) -> list[dict]:
    headers = {"Authorization": config.PEXELS_API_KEY}
    try:
        response = requests.get(
            PEXELS_SEARCH_URL,
            headers=headers,
            params={"query": query, "orientation": "portrait", "per_page": per_page},
            timeout=20,
        )
        response.raise_for_status()
        return response.json().get("videos", [])
    except Exception:
        return []


def _pick_best_video_url(video_data: dict) -> str | None:
    files = video_data.get("video_files", [])
    if not files:
        return None

    # Priorizar videos verticales (w <= h) con resolución óptima
    portrait_files = [f for f in files if f.get("width") and f["width"] <= f.get("height", 0)]
    candidate_list = portrait_files or files

    # Ordenar buscando buena calidad (ideal ~1080) sin exceder pesos extremos
    sorted_files = sorted(
        candidate_list,
        key=lambda f: (f.get("width", 0) if f.get("width", 0) <= 1080 else -f.get("width", 0)),
        reverse=True,
    )
    return sorted_files[0].get("link") if sorted_files else None


def download_background_videos(keywords: list[str], output_dir: Path, min_clips: int = 5) -> list[Path]:
    """Descarga de 4 a 6 clips de video variados para dinamismo visual en el Short."""
    output_dir.mkdir(parents=True, exist_ok=True)
    all_videos = []
    seen_ids = set()

    # Buscar clips con cada keyword individual para máxima variedad visual
    search_queries = list(keywords) if keywords else ["colombia flag", "courthouse justice", "bogota city"]
    if len(search_queries) < 3:
        search_queries.extend(["government building", "gavel court", "colombia congress"])

    for query in search_queries:
        videos = _search_videos_for_query(query, per_page=8)
        for v in videos:
            if v["id"] not in seen_ids:
                seen_ids.add(v["id"])
                all_videos.append(v)
        if len(all_videos) >= min_clips * 3:
            break

    if not all_videos:
        all_videos = _search_videos_for_query("colombia politics", per_page=10)

    if not all_videos:
        raise RuntimeError("No se encontraron videos de fondo en Pexels")

    # Barajar para dinamismo y seleccionar hasta min_clips
    random.shuffle(all_videos)
    selected_videos = all_videos[: max(min_clips, 4)]

    downloaded_paths = []
    for idx, vid in enumerate(selected_videos):
        url = _pick_best_video_url(vid)
        if not url:
            continue
        dest_path = output_dir / f"clip_{idx+1}.mp4"
        try:
            with requests.get(url, stream=True, timeout=45) as r:
                r.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=16384):
                        f.write(chunk)
            downloaded_paths.append(dest_path)
        except Exception as e:
            print(f"  [Aviso] Error descargando clip {idx+1}: {e}")

    if not downloaded_paths:
        raise RuntimeError("No se pudo descargar ningún video de fondo")

    return downloaded_paths


def download_background_video(keywords: list[str], out_path: Path) -> Path:
    """Retrocompatibilidad para descargar un solo video."""
    clips = download_background_videos(keywords, out_path.parent, min_clips=1)
    if clips[0] != out_path:
        shutil.copyfile(clips[0], out_path)
    return out_path

