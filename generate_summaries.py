import os
import datetime
from pymongo import MongoClient
from google import genai

MEDIAS = {
    "ellitoral": "El Litoral",
    "aire": "Aire de Santa Fe",
    "lacapital": "La Capital"
}

def generate_summaries():
    client_mongo = MongoClient(os.getenv("MONGODB_URI"))
    collection = client_mongo["social_listening"]["drugtrafficking"]
    summaries_col = client_mongo["social_listening"]["daily_summaries"]
    client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    today = datetime.date.today().isoformat()

    # Skip if everything already generated today
    existing = set(
        doc["media"] for doc in summaries_col.find({"date": today}, {"media": 1})
    )
    all_keys = set(MEDIAS.keys()) | {"integrativo"}
    if all_keys.issubset(existing):
        print("[SKIP] All summaries already generated today")
        client_mongo.close()
        return

    # Fetch last 5 articles per media
    all_articles = {}
    for media_key, media_label in MEDIAS.items():
        docs = list(
            collection.find({"media": media_key})
            .sort("date", -1)
            .limit(5)
        )
        if docs:
            all_articles[media_key] = {
                "label": media_label,
                "articles": "\n\n---\n\n".join([
                    f"Título: {d.get('title', '')}\nFecha: {str(d.get('date', ''))[:10]}\nContenido: {d.get('content', '')[:500]}"
                    for d in docs
                ])
            }
            print(f"[FETCH] {media_key}: {len(docs)} articles")
        else:
            print(f"[SKIP] No articles found for {media_key}")

    if not all_articles:
        print("[ERROR] No articles fetched for any media")
        client_mongo.close()
        return

    # Build single prompt
    medias_text = "\n\n========\n\n".join([
        f"MEDIO: {data['label']}\n\n{data['articles']}"
        for media_key, data in all_articles.items()
    ])

    prompt = f"""Eres un analista especializado en narcotráfico y crimen organizado en Argentina.
A continuación encontrarás los últimos 5 artículos de tres medios de Santa Fe.
Tu tarea es producir 4 textos en total, respondiendo ÚNICAMENTE en el siguiente formato JSON y nada más:

{{
  "ellitoral": "Bullets con los temas y sucesos que cubrieron los artículos de El Litoral, si más de un artículo se refiere al mismo tema, únelos",
  "aire": "Bullets con los temas y sucesos que cubrieron los artículos de Aire de Santa Fe, si más de un artículo se refiere al mismo tema, únelos",
  "lacapital": "Bullets con los temas y sucesos que cubrieron los artículos de La Capital, si más de un artículo se refiere al mismo tema, únelos",
  "integrativo": "entre 1 y 3 párrafos integrando la cobertura de los tres medios, identificando temas comunes, perspectivas distintas o agendas exclusivas de cada uno"
}}

Para cada resumen: sé específico con nombres, lugares y hechos concretos. 
Para el integrativo: identificá si cubren los mismos hechos con distinto énfasis, temas exclusivos de algún medio, o agenda común.

Artículos:

{medias_text}

Respondé SOLO con el JSON, sin texto adicional, sin backticks."""

    try:
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw = response.text.strip()

        import json
        result = json.loads(raw)

        for key in list(MEDIAS.keys()) + ["integrativo"]:
            if key in existing:
                print(f"[SKIP] {key} already exists for today")
                continue
            if key in result:
                summaries_col.insert_one({
                    "date": today,
                    "media": key,
                    "summary": result[key].strip()
                })
                print(f"[OK] Summary saved for {key}")
            else:
                print(f"[WARN] Key '{key}' missing from LLM response")

    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print(f"[RAW] {raw[:500]}")
    except Exception as e:
        print(f"[ERROR] API call failed: {e}")

    client_mongo.close()

if __name__ == "__main__":
    generate_summaries()