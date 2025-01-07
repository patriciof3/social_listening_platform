import streamlit as st
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from word_count_plot import plot_word_count_by_period

sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-mpnet-base-v2")

# Initialize Chroma client with the local path to your database
persist_directory = r"C:\Users\patricio\Documents\Python\drugtrafficking_rag\data/chroma_db_storage"

client = chromadb.PersistentClient(
        path=persist_directory,  # Directory in Google Drive
                                  )

# Load the collection
collection = client.get_collection(name="rag_2008_2011_web", embedding_function=sentence_transformer_ef)



# Streamlit App

st.set_page_config(layout="wide")

st.title("Buscador de fragmentos CaroTheBest :female-student:")

 # Query Input
query = st.text_input("Ingresa tu consulta:", "")

# # Execute Query
if query:
       result = collection.query(
           query_texts=[query],
           n_results=20,
           include=["metadatas", "documents"],
           #where=filter_dict,
       )
       
       # Format Results
       if result["metadatas"]:
           df_results = pd.DataFrame(result["metadatas"][0])
           df_results["Document"] = result["documents"][0]
           st.write("Resultados:")
           st.dataframe(df_results,
                        column_order=["Document","title", "date", "link", "media"],
                        use_container_width=True)
       else:
           st.write("No results found.")

# Display Query Results
st.write("Modifica filtros o consulta para refinar los resultados.")

st.title("Trackeo de palabras")

# Word count barplot input

period = st.selectbox(
    "¿Qué intervalo de tiempo quieres visualizar?",
    ("Diario", "Mensual", "Anual"),
)

word_to_count = st.text_input("Palabra para graficar:", "")

        # Plotting Word Counts
if word_to_count:
    st.write(f"Recuento de la palabra '{word_to_count}':")
    fig = plot_word_count_by_period(word_to_count, period)  # Call the function
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("No hay palabra seleccionada.")
