"""Sube el video final a YouTube usando las credenciales OAuth guardadas (refresh token)."""
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials() -> Credentials:
    if not all([config.YT_CLIENT_ID, config.YT_CLIENT_SECRET, config.YT_REFRESH_TOKEN]):
        raise RuntimeError(
            "Faltan credenciales de YouTube (YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN). "
            "Ejecuta scripts/generate_youtube_token.py para obtenerlas."
        )
    return Credentials(
        token=None,
        refresh_token=config.YT_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.YT_CLIENT_ID,
        client_secret=config.YT_CLIENT_SECRET,
        scopes=SCOPES,
    )


def upload_short(video_path: Path, title: str, description: str, tags: list[str]) -> str:
    credentials = _get_credentials()
    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "24",  # Entertainment
        },
        "status": {
            "privacyStatus": config.YT_PRIVACY_STATUS,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()

    video_id = response["id"]
    return f"https://youtube.com/shorts/{video_id}"
