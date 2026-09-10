"""Genera el tema, guion y metadatos de un short usando OpenAI, evitando repetir temas."""
import json
from openai import OpenAI
from src import config

SYSTEM_PROMPT = """Eres un guionista experto en Shorts de YouTube de analisis politico sobre
Abelardo de la Espriella, abogado y figura politica colombiana. Escribes guiones cortos,
con un gancho fuerte en la primera frase, en español neutro, para ser narrados en voz alta
en 35-50 segundos (unas 100-140 palabras).

Reglas de precision y responsabilidad (obligatorias, no negociables):
- No inventes fechas, cifras, declaraciones textuales, procesos judiciales ni hechos especificos
  que no puedas verificar; no tienes acceso a noticias en tiempo real.
- Enfocate en su rol publico conocido (abogado litigante, comentarista, precandidato/candidato
  presidencial), su estilo discursivo y temas generales de su agenda publica, sin afirmar como
  "hecho reciente" algo que no esta confirmado.
- Usa lenguaje condicional/atribuido ("se le conoce por...", "ha declarado publicamente que...",
  "es conocido en medios por...") en vez de afirmaciones tajantes sobre eventos puntuales.
- Manten un tono informativo y neutral, sin insultos, sin difamacion, sin acusaciones no verificadas.
Debes responder EXCLUSIVAMENTE con un JSON valido, sin texto adicional ni markdown."""

USER_PROMPT_TEMPLATE = """Genera un short de analisis politico NUEVO sobre Abelardo de la Espriella,
distinto a estos angulos ya usados:
{used_topics}

Devuelve un JSON con estas claves exactas:
- "topic": angulo corto (3-6 palabras), ej. "su rol como precandidato"
- "title": titulo llamativo para YouTube, maximo 90 caracteres, debe incluir la palabra Shorts o #Shorts
- "description": descripcion breve (2-3 frases) con 3-5 hashtags relevantes al final (incluye #Colombia)
- "tags": lista de 8-12 tags de YouTube (strings cortos, relacionados a Colombia y politica)
- "script": el guion a narrar, 100-140 palabras, gancho en la primera frase, sin encabezados ni acotaciones,
  siguiendo estrictamente las reglas de precision y responsabilidad
- "keywords": lista de 3-5 palabras clave en ingles para buscar video de stock generico relacionado
  (ej. "colombia flag", "courthouse justice", "bogota city", "government building", "gavel court")
"""


def _load_used_topics() -> list[str]:
    if config.USED_TOPICS_FILE.exists():
        data = json.loads(config.USED_TOPICS_FILE.read_text(encoding="utf-8"))
        return data.get("topics", [])
    return []


def save_used_topic(topic: str) -> None:
    data = {"topics": _load_used_topics()}
    data["topics"].append(topic)
    # conservar solo los ultimos 200 para no inflar el prompt indefinidamente
    data["topics"] = data["topics"][-200:]
    config.USED_TOPICS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def generate_script() -> dict:
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    used_topics = _load_used_topics()
    used_topics_text = ", ".join(used_topics[-50:]) if used_topics else "(ninguno todavia)"

    response = client.chat.completions.create(
        model=config.CHAT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(used_topics=used_topics_text)},
        ],
        temperature=1.0,
    )

    data = json.loads(response.choices[0].message.content)
    required = {"topic", "title", "description", "tags", "script", "keywords"}
    if not required.issubset(data.keys()):
        raise ValueError(f"Respuesta de OpenAI incompleta, faltan claves: {required - data.keys()}")

    return data
