# Automatización de Shorts de YouTube (datos curiosos)

Pipeline que cada 6 horas, de forma automática en la nube (GitHub Actions):

1. Genera un tema y guion de "dato curioso" con OpenAI (evitando repetir temas ya usados).
2. Convierte el guion a voz narrada con el TTS de OpenAI.
3. Transcribe el audio con Whisper (OpenAI) para obtener el tiempo exacto de cada palabra.
4. Descarga un video de fondo vertical relacionado desde Pexels (gratis).
5. Ensambla el short final (1080x1920, <60s) con subtítulos animados quemados en el video.
6. Sube el video a tu canal de YouTube como Short, con título, descripción y tags.

## Estructura

```
src/
  config.py            # rutas y variables de entorno
  script_generator.py  # genera tema/guion con OpenAI + historial anti-repetición
  tts.py                # texto a voz + transcripción con timestamps (OpenAI)
  visuals.py            # descarga video de fondo de Pexels
  video_builder.py      # ensambla el video final con subtítulos (moviepy)
  youtube_uploader.py   # sube el video a YouTube (OAuth)
  main.py               # orquesta todo el pipeline
scripts/
  generate_youtube_token.py  # script de un solo uso para obtener el refresh token
used_topics.json        # historial de temas ya usados (se actualiza solo)
.github/workflows/shorts.yml  # corre el pipeline cada 6 horas en GitHub Actions
```

## 1. Requisitos que debes crear tú (una sola vez)

### a) API Key de OpenAI
Ve a https://platform.openai.com/api-keys y crea una clave. Necesitarás crédito
cargado en tu cuenta (chat + TTS + Whisper son de pago, pero muy baratos: un
short completo cuesta centavos de dólar).

### b) API Key de Pexels (gratis)
Regístrate en https://www.pexels.com/api/ y copia tu API key gratuita. Se usa
solo para descargar los videos de fondo, no tiene costo.

### c) Credenciales de YouTube (OAuth) — la parte que requiere más pasos
1. Entra a https://console.cloud.google.com/ y crea un proyecto nuevo.
2. En "APIs y servicios" > "Biblioteca", busca **YouTube Data API v3** y habilítala.
3. En "APIs y servicios" > "Pantalla de consentimiento OAuth":
   - Tipo de usuario: Externo.
   - Completa el nombre de la app y tu correo.
   - En "Scopes" no hace falta agregar nada manualmente.
   - En "Test users" agrega tu propio correo de Gmail/YouTube (mientras la app
     esté en modo "Testing" solo tú podrás usarla, lo cual está bien).
4. En "Credenciales" > "Crear credenciales" > "ID de cliente de OAuth":
   - Tipo de aplicación: **Aplicación de escritorio**.
   - Descarga el JSON generado.
5. Guarda ese archivo descargado como `client_secret.json` en la raíz de este
   proyecto (mismo nivel que `requirements.txt`).
6. Instala las dependencias localmente y corre el script de un solo uso:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python scripts\generate_youtube_token.py
   ```

   Esto abrirá tu navegador para iniciar sesión con la cuenta de YouTube donde
   quieres publicar los shorts y pedirá autorización. Al terminar, la terminal
   imprimirá:

   ```
   YT_CLIENT_ID=...
   YT_CLIENT_SECRET=...
   YT_REFRESH_TOKEN=...
   ```

   Guarda esos tres valores, los necesitarás en el paso siguiente.
   **No subas `client_secret.json` al repositorio** (ya está en `.gitignore`).

## 2. Configurar los secrets en GitHub

En tu repositorio de GitHub: **Settings > Secrets and variables > Actions > New repository secret**,
crea estos 5 secrets:

| Nombre              | Valor                                   |
|---------------------|------------------------------------------|
| `OPENAI_API_KEY`     | tu API key de OpenAI                      |
| `PEXELS_API_KEY`     | tu API key de Pexels                      |
| `YT_CLIENT_ID`       | obtenido en el paso anterior              |
| `YT_CLIENT_SECRET`   | obtenido en el paso anterior              |
| `YT_REFRESH_TOKEN`   | obtenido en el paso anterior              |

El workflow en [.github/workflows/shorts.yml](.github/workflows/shorts.yml) ya
está configurado para correr **cada 6 horas** (`cron: "0 */6 * * *"`) y también
se puede ejecutar manualmente desde la pestaña "Actions" > "Generar y publicar
Short cada 6 horas" > "Run workflow".

## 3. Probar localmente antes de subir a GitHub

1. Copia `.env.example` a `.env` y rellena tus claves.
2. Copia una fuente `.ttf` cualquiera (por ejemplo `C:\Windows\Fonts\arialbd.ttf`)
   a `assets\font.ttf`.
3. Instala [ImageMagick](https://imagemagick.org/script/download.php) (necesario
   para renderizar los subtítulos con moviepy) y asegúrate de que esté en el PATH.
4. Instala ffmpeg (`choco install ffmpeg` o descárgalo manualmente) y que esté en el PATH.
5. Ejecuta:

   ```powershell
   pip install -r requirements.txt
   python -m src.main
   ```

   El video final se guarda en `output/<run_id>/short_final.mp4` y luego se
   sube automáticamente a tu canal.

## 4. Notas y personalización

- **Frecuencia**: cambia el `cron` en `.github/workflows/shorts.yml` si quieres
  otra frecuencia (ej. `0 */4 * * *` para cada 4 horas).
- **Voz**: cambia `TTS_VOICE` en `src/config.py` (voces disponibles de OpenAI TTS:
  alloy, echo, fable, onyx, nova, shimmer, coral, verse, ballad, ash, sage).
- **Privacidad**: `YT_PRIVACY_STATUS` puede ser `public`, `unlisted` o `private`
  (útil para revisar los primeros videos antes de hacerlos públicos).
- **Evitar contenido repetido**: `used_topics.json` guarda los temas ya usados;
  el workflow lo commitea de vuelta al repo tras cada ejecución exitosa.
- **Costo aproximado**: OpenAI (chat + TTS + Whisper) suele costar unos pocos
  centavos por short. Pexels y GitHub Actions (2000 min/mes gratis en repos
  públicos) no tienen costo.
