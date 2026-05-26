import os
import datetime
from pymongo import MongoClient
from google import genai
from dotenv import load_dotenv
load_dotenv()

MEDIAS = {
    "ellitoral": "El Litoral",
    "aire": "Aire de Santa Fe",
    "lacapital": "La Capital"
}

def generate_summaries():
    client_mongo = MongoClient(os.environ["MONGODB_URI"])
    collection = client_mongo["social_listening"]["drugtrafficking"]
    summaries_col = client_mongo["social_listening"]["daily_summaries"]

    client_gemini = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    today = datetime.date.today().isoformat()

    for media_key, media_label in MEDIAS.items():
        # Skip if already generated today
        if summaries_col.find_one({"date": today, "media": media_key}):
            print(f"[SKIP] {media_key} already summarized today")
            continue

        # Fetch last 5 articles
        docs = list(
            collection.find({"media": media_key})
            .sort("date", -1)
            .limit(5)
        )

        if not docs:
            print(f"[SKIP] No articles found for {media_key}")
            continue

        articles_text = "\n\n---\n\n".join([
            f"Título: {d.get('title', '')}\nFecha: {str(d.get('date', ''))[:10]}\nContenido: {d.get('content', '')[:500]}"
            for d in docs
        ])

        prompt = f"""Eres un analista especializado en narcotráfico y crimen organizado en Argentina.
Basándote en los siguientes artículos recientes del medio "{media_label}", redactá un párrafo 
de 4 a 6 oraciones que resuma los principales temas que este medio estuvo cubriendo en los 
últimos días en relación al narcotráfico y crimen organizado en Santa Fe.
Sé específico: mencioná lugares, personas, hechos concretos si aparecen.
No uses bullets. Solo texto corrido.

Artículos:
{articles_text}

Resumen:"""

        try:
            response = client_gemini.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            summary_text = response.text.strip()

            summaries_col.insert_one({
                "date": today,
                "media": media_key,
                "summary": summary_text
            })
            print(f"[OK] Summary generated for {media_key}")

        except Exception as e:
            print(f"[ERROR] {media_key}: {e}")


    # --- RESUMEN INTEGRATIVO ---
    # Verificar si ya existe para hoy
    if summaries_col.find_one({"date": today, "media": "integrativo"}):
        print("[SKIP] Resumen integrativo ya generado hoy")
    else:
        # Leer los 3 resúmenes recién generados (o los más recientes disponibles)
        resumenes = {}
        for media_key, media_label in MEDIAS.items():
            doc = summaries_col.find_one({"media": media_key}, sort=[("date", -1)])
            if doc:
                resumenes[media_label] = doc["summary"]

        if len(resumenes) == 3:
            resumenes_texto = "\n\n".join([
                f"{label}:\n{summary}"
                for label, summary in resumenes.items()
            ])

            prompt_integrativo = f"""Eres un analista especializado en narcotráfico y crimen organizado en Argentina.
A continuación tenés los resúmenes de cobertura reciente de tres medios de Santa Fe sobre narcotráfico y crimen organizado.

{resumenes_texto}

Redactá entre 1 y 3 párrafos que integren la cobertura de los tres medios. 
Identificá si están cubriendo los mismos hechos con distintas perspectivas o énfasis, 
si hay temas que solo cubre uno de los medios, o si existe una agenda común.
Sé específico con nombres, lugares y hechos cuando aparezcan.
No uses bullets. Solo texto corrido."""

            try:
                response = client_gemini.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_integrativo
                )
                summaries_col.insert_one({
                    "date": today,
                    "media": "integrativo",
                    "summary": response.text.strip()
                })
                print("[OK] Resumen integrativo generado")
            except Exception as e:
                print(f"[ERROR] Resumen integrativo: {e}")
        else:
            print(f"[SKIP] No hay suficientes resúmenes para integrar ({len(resumenes)}/3)")

    client_mongo.close()

if __name__ == "__main__":
    generate_summaries()