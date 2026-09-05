import os
import json
import datetime

from pymongo import MongoClient
from google import genai


MEDIAS = {
    "ellitoral": "El Litoral",
    "aire": "Aire de Santa Fe",
    "lacapital": "La Capital"
}


def generate_summaries():
    # MongoDB
    client_mongo = MongoClient(os.getenv("MONGODB_URI"))
    collection = client_mongo["social_listening"]["drugtrafficking"]
    summaries_col = client_mongo["social_listening"]["daily_summaries"]

    # Gemini
    client_gemini = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    today = datetime.date.today().isoformat()

    # --------------------------------------------------
    # Check existing summaries
    # --------------------------------------------------
    existing = set(
        doc["media"]
        for doc in summaries_col.find(
            {"date": today},
            {"media": 1}
        )
    )

    all_keys = set(MEDIAS.keys()) | {"integrativo"}

    if all_keys.issubset(existing):
        print("[SKIP] All summaries already generated today")
        client_mongo.close()
        return

    # --------------------------------------------------
    # Fetch last 5 articles per media
    # --------------------------------------------------
    all_articles = {}

    for media_key, media_label in MEDIAS.items():

        docs = list(
            collection.find(
                {"media": media_key}
            )
            .sort("date", -1)
            .limit(5)
        )

        if docs:

            articles_text = "\n\n---\n\n".join(
                [
                    (
                        f"Título: {d.get('title', '')}\n"
                        f"Fecha: {str(d.get('date', ''))[:10]}\n"
                        f"Contenido: {d.get('content', '')[:500]}"
                    )
                    for d in docs
                ]
            )

            all_articles[media_key] = {
                "label": media_label,
                "articles": articles_text
            }

            print(
                f"[FETCH] {media_key}: "
                f"{len(docs)} articles"
            )

        else:
            print(
                f"[SKIP] No articles found for {media_key}"
            )

    # --------------------------------------------------
    # Stop if no articles were found
    # --------------------------------------------------
    if not all_articles:
        print("[ERROR] No articles fetched for any media")
        client_mongo.close()
        return

    # --------------------------------------------------
    # Build articles text for prompt
    # --------------------------------------------------
    medias_text = "\n\n========\n\n".join(
        [
            (
                f"MEDIO: {data['label']}\n\n"
                f"{data['articles']}"
            )
            for media_key, data in all_articles.items()
        ]
    )

    # --------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------
    prompt = f"""
Eres un analista especializado en narcotráfico y crimen organizado en Argentina.

A continuación encontrarás los últimos 5 artículos de tres medios de Santa Fe.

Tu tarea es producir un JSON válido con EXACTAMENTE esta estructura:

{{
  "ellitoral": [
    "Tema o suceso 1",
    "Tema o suceso 2"
  ],
  "aire": [
    "Tema o suceso 1",
    "Tema o suceso 2"
  ],
  "lacapital": [
    "Tema o suceso 1",
    "Tema o suceso 2"
  ],
    "integrativo": "Entre 1 y 3 párrafos integrando la cobertura de los tres medios. Debes usar un tono neutro, no evaluativo. Desde una perspectiva de análisis de discurso que ponga el foco en cómo se construye lo noticiable en relación al narcotráfico"
}}

IMPORTANTE:

- ellitoral, aire y lacapital DEBEN ser arrays JSON de strings.
- Cada elemento del array debe representar un tema o suceso.
- Si varios artículos se refieren al mismo hecho, unifícalos en un único elemento.
- Sé específico con nombres, lugares y hechos concretos.
- integrativo DEBE ser un string, no un array.
- Para el integrativo, identificá temas comunes entre los medios, diferencias de énfasis, temas exclusivos o agendas particulares de cada medio.
- No inventes información que no esté presente en los artículos proporcionados.
- Si no hay información suficiente para un medio, devolvé un array vacío [].

Respondé SOLO con JSON válido.
No agregues texto antes ni después.
No uses bloques de código Markdown.

Artículos:

{medias_text}
"""

    # --------------------------------------------------
    # Generate summaries
    # --------------------------------------------------
    try:

        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw = response.text.strip()

        # Parse JSON
        result = json.loads(raw)

        # --------------------------------------------------
        # Debug response types
        # --------------------------------------------------
        print("\n[DEBUG] Response types:")

        for key, value in result.items():
            print(
                f"[DEBUG] {key}: "
                f"{type(value).__name__}"
            )

        # --------------------------------------------------
        # Save summaries
        # --------------------------------------------------
        for key in list(MEDIAS.keys()) + ["integrativo"]:

            # Skip if already generated today
            if key in existing:
                print(
                    f"[SKIP] {key} already exists for today"
                )
                continue

            # Check key exists
            if key not in result:
                print(
                    f"[WARN] Key '{key}' missing "
                    f"from LLM response"
                )
                continue

            summary = result[key]

            # ----------------------------------------------
            # Media summaries: expected list -> bullets
            # ----------------------------------------------
            if key in MEDIAS:

                if isinstance(summary, list):

                    summary = "\n".join(
                        (
                            f"- {str(item).strip()}"
                        )
                        for item in summary
                        if str(item).strip()
                    )

                else:

                    print(
                        f"[WARN] Expected list for '{key}', "
                        f"got {type(summary).__name__}. "
                        f"Converting to string."
                    )

                    summary = str(summary).strip()

            # ----------------------------------------------
            # Integrative summary: expected string
            # ----------------------------------------------
            else:

                if isinstance(summary, list):

                    print(
                        "[WARN] Expected string for "
                        "'integrativo', got list. "
                        "Joining elements."
                    )

                    summary = "\n\n".join(
                        str(item).strip()
                        for item in summary
                        if str(item).strip()
                    )

                else:

                    summary = str(summary).strip()

            # ----------------------------------------------
            # Save to MongoDB
            # ----------------------------------------------
            summaries_col.insert_one(
                {
                    "date": today,
                    "media": key,
                    "summary": summary
                }
            )

            print(
                f"[OK] Summary saved for {key}"
            )

    except json.JSONDecodeError as e:

        print(
            f"[ERROR] Failed to parse JSON response: {e}"
        )

        print(
            f"[RAW] {raw[:1000]}"
        )

    except Exception as e:

        print(
            f"[ERROR] API call failed: {e}"
        )

    finally:

        client_mongo.close()


if __name__ == "__main__":
    generate_summaries()