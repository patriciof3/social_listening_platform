import streamlit as st
import pandas as pd
from features_general import (
    plot_cumulative_articles_monthly,
    plot_weekly_trend,
    get_weekly_avg_per_media,
    get_data
)

st.set_page_config(layout="wide", page_title="Monitor Narcotráfico Santa Fe")

df = get_data()

# --- HEADER ---
st.title("Monitor de Cobertura Mediática del Narcotráfico en Santa Fe")
st.markdown(
    "<p style='color: white; font-size: 20px;'>Estos son los resultados de un scraping de noticias vinculadas al narcotráfico en portales de la provincia de Santa Fe. Todos los días a las 9pm se escanean secciones vinculadas a esta problemática en portales seleccionados y se almacenan título, fecha, link y contenido de los artículos en una base de datos.</p>",
    unsafe_allow_html=True
)

st.divider()

# --- CHARTS ---
fig_cumulative = plot_cumulative_articles_monthly(df)
st.plotly_chart(fig_cumulative, width="stretch")


st.divider()


# --- KPI CARDS ---
avg_per_media, change_per_media = get_weekly_avg_per_media(df)
medias = ['ellitoral', 'aire', 'lacapital']
labels = {'ellitoral': 'El Litoral', 'aire': 'Aire de Santa Fe', 'lacapital': 'La Capital'}
colors = {'ellitoral': '#5dade2', 'aire': '#F08080', 'lacapital': '#f1e85c'}

st.markdown("### Promedio de artículos por semana en el último año")
cols = st.columns(3)

for col, media in zip(cols, medias):
    avg = avg_per_media.get(media, 0)
    color = colors[media]

    col.markdown(
        f"""
        <div style="background-color:#1e1e1e; border-left: 5px solid {color};
                    border-radius:8px; padding:20px 24px; text-align:center;">
            <p style="color:#aaaaaa; font-size:14px; margin:0;">{labels[media]}</p>
            <p style="color:{color}; font-size:52px; font-weight:bold; margin:8px 0;">{avg}</p>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

fig_trend = plot_weekly_trend(df)
st.plotly_chart(fig_trend, width="stretch")