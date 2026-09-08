"""
Script de UN SOLO USO que corres en tu PC (no en GitHub Actions) para obtener el
YT_REFRESH_TOKEN. Abre el navegador, inicias sesion con tu cuenta de YouTube y
autorizas la app. Al final imprime los valores que debes guardar como secrets
de GitHub (YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN).

Requisitos previos:
1. Crear un proyecto en https://console.cloud.google.com/
2. Habilitar la "YouTube Data API v3"
3. Crear credenciales OAuth 2.0 de tipo "Aplicacion de escritorio"
4. Descargar el JSON de credenciales y guardarlo como client_secret.json
   en la raiz del proyecto (mismo nivel que este script).
"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = Path(__file__).resolve().parent.parent / "client_secret.json"


def main():
    if not CLIENT_SECRETS_FILE.exists():
        raise SystemExit(
            f"No se encontro {CLIENT_SECRETS_FILE}. Descarga el JSON de credenciales OAuth "
            "de Google Cloud Console y guardalo con ese nombre."
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
    credentials = flow.run_local_server(port=0)

    print("\n=== Guarda estos valores como secrets en GitHub (Settings > Secrets and variables > Actions) ===")
    print(f"YT_CLIENT_ID={credentials.client_id}")
    print(f"YT_CLIENT_SECRET={credentials.client_secret}")
    print(f"YT_REFRESH_TOKEN={credentials.refresh_token}")


if __name__ == "__main__":
    main()
