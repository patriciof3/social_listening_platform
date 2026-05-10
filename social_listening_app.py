import streamlit as st
import pandas as pd
from mongodb_features import reading_data
from features_general import (
    plot_cumulative_articles_monthly,
    plot_article_distribution,
    plot_articles_last_week,
)

st.set_page_config(layout="wide", page_title="Monitor Narcotráfico Santa Fe")

@st.cache_data(ttl=3600)
def load_data():
    df = reading_data("social_listening", "drugtrafficking")
    strings_to_remove = ["santa_fe", "rosario", "argentina", "años", "narcotráfico", "drogas"]
    for s in strings_to_remove:
        df["cleaned_content"] = df["cleaned_content"].str.replace(s, "", regex=False)
    df["cleaned_content"] = df["cleaned_content"].str.replace(r"\s+", " ", regex=True).str.strip()
    return df

df = load_data()

# --- PAGE ---
st.title("Monitor de cobertura mediática del Narcotráfico en Santa Fe")

st.markdown(
    "<p style='color: white; font-size: 20px;'>Estos son los resultados de un scraping de noticias vinculadas al narcotráfico en portales de la provincia de Santa Fe. Todos los días a las 9pm se escanean secciones vinculadas a esta problemática en los portales seleccionados y se guarda el título, fecha, link y contenido de los mismos en una base de datos</p>",
    unsafe_allow_html=True
)

fig_bar = plot_cumulative_articles_monthly(df)
st.plotly_chart(fig_bar, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    fig_pie = plot_article_distribution(df)
    st.plotly_chart(fig_pie, use_container_width=True)
with col2:
    fig_last_week = plot_articles_last_week(df)
    st.plotly_chart(fig_last_week, use_container_width=True)