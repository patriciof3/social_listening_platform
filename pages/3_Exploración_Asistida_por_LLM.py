import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient
from google import genai
from google.genai import types as gtypes
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(layout="wide", page_title="Búsqueda Semántica")

st.title("Búsqueda Semántica")
st.markdown(
    "<p style='color: white; font-size: 18px;'>Busca artículos por similitud semántica usando embeddings de Gemini y Atlas Vector Search.</p>",
    unsafe_allow_html=True
)

# --- API KEY ---
gemini_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")
if not gemini_key:
    st.info("Ingresa tu Gemini API Key para continuar.")
    st.stop()

# --- INPUTS ---
col1, col2 = st.columns(2)
with col1:
    subject = st.text_area(
        "Tema de búsqueda",
        placeholder="Ej: Barra brava de Newell's vinculada a Los Monos",
        height=100
    )
with col2:
    question = st.text_area(
        "Pregunta para el LLM",
        placeholder="Ej: ¿Cuál es el rol de Guille Cantero en la barra brava?",
        height=100
    )

# --- FILTERS ---
with st.expander("Filtros opcionales"):
    col1, col2, col3 = st.columns(3)
    with col1:
        source_options = ["Todos", "ellitoral", "lacapital", "aire"]
        selected_source = st.selectbox("Fuente", source_options)
    with col2:
        date_from = st.date_input("Desde", value=None)
    with col3:
        date_to = st.date_input("Hasta", value=None)

# --- TOP K ---
top_k = st.slider("Chunks similares a recuperar", min_value=1, max_value=20, value=5)

# --- SEARCH ---
run = st.button("🔍 Buscar", type="primary")

if not run:
    st.stop()
if not subject.strip():
    st.warning("Por favor ingresa un tema de búsqueda.")
    st.stop()
if not question.strip():
    st.warning("Por favor ingresa una pregunta para el LLM.")
    st.stop()

# --- GENERATE QUERY EMBEDDING ---
try:
    with st.spinner("Generando embedding de la consulta..."):
        client_gemini = genai.Client(api_key=gemini_key)
        result = client_gemini.models.embed_content(
            model="gemini-embedding-001",
            contents=subject,
            config=gtypes.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=768
            )
        )
        query_vector = result.embeddings[0].values
except Exception as e:
    st.error(f"Error generando embedding: {e}")
    st.stop()

# --- VECTOR SEARCH ---
try:
    with st.spinner(f"Buscando los {top_k} chunks más similares..."):
        mongo_client = MongoClient(
            os.getenv("MONGODB_URI"),
            serverSelectionTimeoutMS=30000,
            socketTimeoutMS=60000
        )
        chunks_col = mongo_client["social_listening"]["drugtrafficking_chunks"]

        filter_query = {}
        if selected_source != "Todos":
            filter_query["media"] = selected_source
        if date_from:
            filter_query["date"] = {"$gte": pd.Timestamp(date_from).isoformat()}
        if date_to:
            filter_query.setdefault("date", {})["$lte"] = pd.Timestamp(date_to).isoformat()

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                    **({"filter": filter_query} if filter_query else {})
                }
            },
            {
                "$project": {
                    "title": 1,
                    "date": 1,
                    "link": 1,
                    "media": 1,
                    "text_content": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        top_chunks = list(chunks_col.aggregate(pipeline))
        mongo_client.close()

        if not top_chunks:
            st.warning("No se encontraron chunks. Verifica que el índice vectorial esté creado en Atlas.")
            st.stop()

except Exception as e:
    st.error(f"Error en Vector Search: {e}")
    st.stop()

# --- RESULTS TABLE ---
st.success(f"✅ {len(top_chunks)} chunks recuperados")

results_df = pd.DataFrame([{
    "Score":     round(c.get("score", 0), 4),
    "Medio":     c.get("media", ""),
    "Fecha":     str(c.get("date", ""))[:10],
    "Título":    c.get("title", ""),
    "Fragmento": c.get("text_content", "")[:200] + "...",
    "Link":      c.get("link", "")
} for c in top_chunks])

gb = GridOptionsBuilder.from_dataframe(results_df)
gb.configure_default_column(wrapText=True, resizable=True)
gb.configure_column("Fragmento", wrapText=True, autoHeight=True)
gb.configure_column("Link", cellRenderer=JsCode("""
    function(params) {
        return params.value ? `<a href="${params.value}" target="_blank">↗ abrir</a>` : '—';
    }
"""))
AgGrid(
    results_df,
    gridOptions=gb.build(),
    height=400,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True
)

# --- LLM ANSWER ---
st.markdown("---")
st.subheader("Análisis del LLM")

context = "\n\n---\n\n".join([
    f"[{i+1}] ({c.get('media','')}, {str(c.get('date',''))[:10]}) {c.get('title','')}\n{c.get('text_content','')}"
    for i, c in enumerate(top_chunks)
])

prompt = f"""Eres un analista especializado en narcotráfico y crimen organizado en Argentina.
Responde la pregunta usando ÚNICAMENTE el contexto provisto.
Cita las fuentes por número [1], [2], etc.
Si el contexto no contiene suficiente información, dilo claramente.

Contexto:
{context}

Pregunta: {question}"""

try:
    with st.spinner("Generando respuesta..."):
        response = client_gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        st.markdown(response.text)
except Exception as e:
    st.error(f"Error generando respuesta: {e}")