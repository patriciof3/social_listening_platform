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

st.set_page_config(layout="wide")
df = reading_data("social_listening", "drugtrafficking")


##### GENERAL SECTION #########        

def general_page():
    st.title("Monitor de noticias de Narcotráfico en Santa Fe")

    st.markdown(
        "<p style='color: White; font-size: 20px;'>Estos son los resultados de un scraping de noticias vinculadas al narcotráfico en portales de la provincia de Santa Fe. Todos los días a las 9pm se escanean secciones vinculadas a esta problemática en los portales seleccionados y se guarda el título, fecha, link y contenido de los mismos en una base de datos</p>",
        unsafe_allow_html=True
    )

    # Cumulative articles
    fig_bar = plot_cumulative_articles_monthly(df)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Article distribution pie chart
    fig_pie = plot_article_distribution(df)
    st.plotly_chart(fig_pie, use_container_width=True)

    # Articles last week bar chart
    fig_last_week = plot_articles_last_week(df)
    st.plotly_chart(fig_last_week, use_container_width=True)

    # WordCloud for previous week
    st.subheader("Word Cloud: Artículos de la última semana")
    plt.figure(figsize=(10,5))
    wordcloud_previous_week(df)  # generate WordCloud on plt
    plt.axis('off')
    st.pyplot(plt)
    
##### QUANTITATIVE SECTION #########        

def cuantitativa_page():
    st.title("Sección Cuantitativa")
    st.divider()
    st.subheader("Selecciona un marco temporal")
    st.write("De no seleccionar ninguno se computarán todos los artículos disponibles.")

    # Initialize session state variables
    if "first_date" not in st.session_state:
        st.session_state.first_date = None
    if "second_date" not in st.session_state:
        st.session_state.second_date = None
    if "filtered_df" not in st.session_state:
        st.session_state.filtered_df = df  # Default to full dataset
    if "filter_btn_clicked" not in st.session_state:
        st.session_state.filter_btn_clicked = False

    # Date inputs
    col1, col2, col3 = st.columns([1, 1, 0.5])
    with col1:
        date1 = st.date_input("Fecha inicial", value=st.session_state.first_date)
    with col2:
        date2 = st.date_input("Fecha final", value=st.session_state.second_date)
    with col3:
        filter_btn = st.button("Filtrar")  # Button to apply filter

    # Store the selected dates in session state
    st.session_state.first_date = date1
    st.session_state.second_date = date2

    # Apply filtering only when button is clicked
    if filter_btn:
        st.session_state.filter_btn_clicked = True
        # Only update filtered_df when button is pressed
        filtered_df = df.copy()
        first_date = pd.to_datetime(st.session_state.first_date) if st.session_state.first_date else None
        second_date = pd.to_datetime(st.session_state.second_date) if st.session_state.second_date else None

        if first_date:
            filtered_df = filtered_df[filtered_df["date"] >= first_date]
        if second_date:
            filtered_df = filtered_df[filtered_df["date"] <= second_date]

        st.session_state.filtered_df = filtered_df  # Save filtered results

    # Display filtered results
    st.write(f"Artículos seleccionados: {len(st.session_state.filtered_df)}")

    st.divider()  

    # **Only update plots when the "Filtrar" button is clicked or on first load**
    if st.session_state.filter_btn_clicked or not st.session_state.filter_btn_clicked:
        st.subheader("Términos más frecuentes")
        top_n = st.slider("¿Cuántos términos quieres visualizar?", 1, 50, 10)
        fig = plot_top_words(st.session_state.filtered_df, column='cleaned_content', top_n=top_n)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("Trackeo de términos")

        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox("¿En qué intervalo de tiempo quieres visualizar el término?", ("Mensual", "Anual", "Diario"))
        with col2:
            word_to_count = st.text_input("Término para graficar:", "monos")
  
        if word_to_count:
            fig, word_count, word_present = plot_word_count_by_period(st.session_state.filtered_df, word_to_count, period)
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"La palabra '{word_to_count}' aparece {word_count} veces, en un total de {word_present} artículos.")

            fig, word_count, word_present = plot_word_count_by_period_relative(st.session_state.filtered_df, word_to_count, period)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.write("No hay palabra seleccionada.")


##### SEMANTIC SECTION #########        
def semantica_page():
    st.title("Semántica")
    st.write("This is the Semántica page. Here you can add semantic analysis, NLP techniques, etc.")


##### CONSULTA SECTION #########        

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

def consulta_bd_page(df):
    st.title("Consulta de Base de Datos")

    st.markdown(
        "<p style='color: White; font-size: 18px;'>Filtra los artículos por fecha y medio, visualiza los resultados y descárgalos en CSV.</p>", 
        unsafe_allow_html=True
    )

    # --- FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Fecha inicial", value='2025-08-01')
    with col2:
        end_date = st.date_input("Fecha final", value=df['date'].max())

    media_options = df['media'].unique().tolist()
    selected_media = st.multiselect("Selecciona medio(s)", media_options, default=media_options)

    # --- FILTER DATA ---
    filtered_df = df[
        (df['date'] >= pd.to_datetime(start_date)) & 
        (df['date'] <= pd.to_datetime(end_date)) &
        (df['media'].isin(selected_media))
    ][["link", "title", "date", "media", "content"]]

    st.markdown(f"### Resultados: {len(filtered_df)} artículos encontrados")

    # --- DISPLAY DATAFRAME WITH AGGRID ---

    gb = GridOptionsBuilder.from_dataframe(filtered_df)
    gb.configure_default_column(editable=False, filterable=True, groupable=True, auto_size=True, tooltip_field=None)
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


# Sidebar navigation
st.sidebar.title("Secciones")
page = st.sidebar.radio("Selecciona una página", ["General", "Cuantitativa", "Semántica", "Consulta"])

# Display the corresponding page based on the user's selection
if page == "General":
    general_page()
elif page == "Cuantitativa":
    cuantitativa_page()
elif page == "Semántica":
    semantica_page()
elif page == "Consulta":
    consulta_bd_page(df)
