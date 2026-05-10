import streamlit as st
from mongodb_features import reading_data
from features_general import *
from features_cuantitativa import plot_top_words, plot_word_count_by_period, plot_word_count_by_period_relative
import pandas as pd
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from st_aggrid import JsCode
from io import BytesIO
import json
import os
### Reading data ####
st.set_page_config(layout="wide")
df = reading_data("social_listening", "drugtrafficking")
strings_to_remove = ["santa_fe", "rosario", "argentina", "años", "narcotráfico", "drogas"]

for s in strings_to_remove:
    df["cleaned_content"] = df["cleaned_content"].str.replace(s, "", regex=False)

# Optional: clean extra spaces
df["cleaned_content"] = df["cleaned_content"].str.replace(r"\s+", " ", regex=True).str.strip()
##### GENERAL SECTION #########        

def general_page():
    st.title("Monitor de cobertura mediática del Narcotráfico en Santa Fe")

    st.markdown(
        "<p style='color: White; font-size: 20px;'>Estos son los resultados de un scraping de noticias vinculadas al narcotráfico en portales de la provincia de Santa Fe. Todos los días a las 9pm se escanean secciones vinculadas a esta problemática en los portales seleccionados y se guarda el título, fecha, link y contenido de los mismos en una base de datos</p>",
        unsafe_allow_html=True
    )

    # Cumulative articles
    fig_bar = plot_cumulative_articles_monthly(df)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        # Article distribution pie chart
        fig_pie = plot_article_distribution(df)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        # Articles last week bar chart
        fig_last_week = plot_articles_last_week(df)
        st.plotly_chart(fig_last_week, use_container_width=True)

    # Top TF-IDF Terms for last week
    st.subheader("¿Qué pasó en la última semana?")

    st.markdown(
        """
        <p style='color: White; font-size: 18px;'>
        Este gráfico muestra las palabras más representativas en las noticias publicadas durante los últimos siete días.
        Para detectarlas, se utiliza un método estadístico llamado <b>TF-IDF</b> (Frecuencia de Término – Frecuencia Inversa de Documento),
        que identifica los términos que aparecen con frecuencia en las notas recientes, pero no de forma tan común en el resto del corpus.
        En otras palabras, destaca los temas que ganaron relevancia esta semana.
        </p>
        """,
        unsafe_allow_html=True
    )

    fig_tfidf = plot_top_tfidf_last_week(df)
    st.plotly_chart(fig_tfidf, use_container_width=True)
    
##### QUANTITATIVE SECTION #########        

def cuantitativa_page():
    st.title("Sección Cuantitativa")

    st.subheader("Trackeo de términos")

    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("¿En qué intervalo de tiempo quieres visualizar el término?", ("Mensual", "Anual"))
    with col2:
        word_to_count = st.text_input("Término para graficar:", "monos")

    if word_to_count:
        fig, word_count, word_present = plot_word_count_by_period(df, word_to_count, period)
        st.plotly_chart(fig, use_container_width=True)
        st.write(f"La palabra '{word_to_count}' aparece {word_count} veces, en un total de {word_present} artículos.")

        fig, word_count, word_present = plot_word_count_by_period_relative(df, word_to_count, period)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.write("No hay palabra seleccionada.")


##### SEMANTIC SECTION #########        
#def semantica_page():
#    st.title("Semántica")
#    st.write("This is the Semántica page. Here you can add semantic analysis, NLP techniques, etc.")


##### CONSULTA SECTION #########        


from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

def consulta_bd_page(df):
    st.title("Consulta de Base de Datos")

    st.markdown(
        "<p style='color: white; font-size: 18px;'>Filtra los artículos por fecha, medio o palabras clave, y visualiza los resultados.</p>", 
        unsafe_allow_html=True
    )

    # --- FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha inicial", value=pd.to_datetime("2025-08-01"))
    with col2:
        end_date = st.date_input("Fecha final", value=df['date'].max())

    media_options = sorted(df['media'].dropna().unique().tolist())
    selected_media = st.multiselect("Selecciona medio(s)", media_options, default=media_options)

    keyword = st.text_input("Filtrar por palabra o frase en el contenido", "")

    # --- Apply filter only when user clicks button ---
    apply_filter = st.button("🔍 Aplicar filtros")

    if apply_filter:
        # --- FILTER DATA ---
        filtered_df = df[
            (df['date'] >= pd.to_datetime(start_date)) &
            (df['date'] <= pd.to_datetime(end_date)) &
            (df['media'].isin(selected_media))
        ].copy()

        if keyword:
            filtered_df["content"] = filtered_df["content"].astype(str)
            filtered_df = filtered_df[filtered_df["content"].str.contains(keyword, case=False, na=False, regex=False)]
        
        filtered_df = filtered_df[["link", "title", "date", "media", "content"]].reset_index(drop=True)

        st.markdown(f"### Resultados: {len(filtered_df)} artículos encontrados")

        # --- Configure Grid ---
        gb = GridOptionsBuilder.from_dataframe(filtered_df)
        gb.configure_default_column(editable=True, wrapText=True, resizable=True)
        grid_options = gb.build()

        AgGrid(filtered_df, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)

              # --- DOWNLOAD BUTTON ---
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name="articulos_filtrados.csv",
            mime='text/csv'
        )
    else:
        st.info("Selecciona los filtros y haz clic en **Aplicar filtros** para ver los resultados.")







  


# Sidebar navigation
st.sidebar.title("Secciones")
page = st.sidebar.radio("Selecciona una página", ["General", "Trackeo de términos", "Consulta"])

# Display the corresponding page based on the user's selection
if page == "General":
    general_page()
elif page == "Trackeo de términos":
    cuantitativa_page()
elif page == "Semántica":
    semantica_page()
elif page == "Consulta":
    consulta_bd_page(df)
