"""Genera el tema, guion y metadatos de un short biblico usando OpenAI."""
import json
from openai import OpenAI
from src import config

SYSTEM_PROMPT = """Eres el guionista de Shorts de YouTube de reflexion cristiana en español.
Escribes textos breves, calidos y contemplativos para una persona que necesita animo, descanso,
esperanza o consuelo. El video debe comenzar con un gancho emocional que conecte una situacion
cotidiana con la promesa del versiculo, por ejemplo: "¿Estas cansado? Escucha este versiculo...".
El tono es sereno, cercano y respetuoso, pensado para una voz relajante, con pausas naturales,
en 35-50 segundos y unas 85-120 palabras.

Reglas biblicas y de precision:
- Elige un pasaje real y conocido de la Biblia y menciona su referencia de forma clara.
- Usa la traduccion Reina-Valera 1909, de dominio publico, o una breve paráfrasis fiel. No
  inventes versiculos ni presentes como cita literal algo que no recuerdes con seguridad.
- El mensaje debe explicar brevemente por que el pasaje acompaña la situacion del inicio y cerrar
  con una frase de paz o esperanza, sin prometer resultados materiales.
- No uses lenguaje de miedo, culpa, condena, sensacionalismo ni afirmaciones medicas.
- Las palabras clave visuales deben describir escenas pacificas y relacionadas con el mensaje.
Debes responder EXCLUSIVAMENTE con un JSON valido, sin texto adicional ni markdown."""

USER_PROMPT_TEMPLATE = """Genera un Short NUEVO de reflexion biblica, distinto a estos temas ya usados
(el historial antiguo de noticias puede ignorarse):
{used_topics}

Devuelve un JSON con estas claves exactas:
- "topic": situacion emocional y tema del pasaje, 3-6 palabras
- "title": titulo calido para YouTube, maximo 90 caracteres, debe incluir #Shorts
- "description": descripcion breve de 2-3 frases con 3-5 hashtags relevantes al final
- "tags": lista de 8-12 tags de YouTube relacionados con Biblia, oracion, paz y esperanza
- "script": guion completo para narrar, 85-120 palabras, sin encabezados ni acotaciones. Debe
  iniciar con una pregunta o frase emocional del tipo "¿Estas cansado? Escucha este versiculo...",
  incluir la referencia biblica, el mensaje y un cierre sereno.
- "keywords": lista de 4-6 palabras clave en ingles para buscar videos verticales de Pexels,
  acordes con el estado de animo y el versiculo (ej. "peaceful sunrise nature", "calm ocean waves",
  "person praying sunset", "forest light", "rain window")
- "music_mood": siempre "peaceful", "hopeful" o "comforting", segun el mensaje
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
