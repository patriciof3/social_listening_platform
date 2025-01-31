import streamlit as st
from mongodb_features import reading_data
from features_general import plot_cumulative_articles, plot_article_distribution, plot_avg_articles_per_day
from features_cuantitativa import plot_top_words, plot_word_count_by_period
import pandas as pd

st.set_page_config(layout="wide")
df = reading_data("social_listening", "drugtrafficking")


##### GENERAL SECTION #########        

def general_page():
    st.title("Descripción general")

    st.markdown("<p style='color: White; font-size: 20px;'>Esta app expone los resultados de un scrapping de noticias vinculadas al narcotráfico en portales de la provincia de Santa Fe. Todos los días a las 9pm se escanean secciones vinculadas a esta problemática en los portales seleccionados y se guarda el título, fecha, link y contenido de los mismos en una base de datos</p>", unsafe_allow_html=True)

    fig_line =plot_cumulative_articles(df)
    st.plotly_chart(fig_line, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig_bar = plot_avg_articles_per_day(df)
        st.plotly_chart(fig_bar, use_container_width=True)
    with col2:
        fig_pie =plot_article_distribution(df)
        st.plotly_chart(fig_pie, use_container_width=True)    
    

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
            word_to_count = st.text_input("Término para graficar:", "justicia")
  
        if word_to_count:
            fig, word_count, word_present = plot_word_count_by_period(st.session_state.filtered_df, word_to_count, period)
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"La palabra '{word_to_count}' aparece {word_count} veces, en un total de {word_present} artículos.")
        else:
            st.write("No hay palabra seleccionada.")


##### SEMANTIC SECTION #########        
def semantica_page():
    st.title("Semántica")
    st.write("This is the Semántica page. Here you can add semantic analysis, NLP techniques, etc.")

# Sidebar navigation
st.sidebar.title("Secciones")
page = st.sidebar.radio("Selecciona una página", ["General", "Cuantitativa", "Semántica"])

# Display the corresponding page based on the user's selection
if page == "General":
    general_page()
elif page == "Cuantitativa":
    cuantitativa_page()
elif page == "Semántica":
    semantica_page()
