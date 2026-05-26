import streamlit as st
import pandas as pd
from pymongo import MongoClient
import os
from features_general import (
    plot_cumulative_articles_monthly,
    plot_weekly_trend,
    get_weekly_avg_per_media,
    get_data
)

st.set_page_config(layout="wide", page_title="Monitor Narcotráfico Santa Fe")

df = get_data()

medias = ['ellitoral', 'aire', 'lacapital']
labels = {'ellitoral': 'El Litoral', 'aire': 'Aire de Santa Fe', 'lacapital': 'La Capital'}
colors = {'ellitoral': '#5dade2', 'aire': '#F08080', 'lacapital': '#f1e85c'}

# --- HEADER ---
st.title("Monitor de Cobertura Mediática del Narcotráfico en Santa Fe")
st.markdown(
    "<p style='color: white; font-size: 20px;'>Resultados de un scraping diario de noticias vinculadas al narcotráfico en portales de la provincia de Santa Fe. Todos los días se escanean secciones vinculadas a esta problemática y se almacenan título, fecha, link y contenido de los artículos en una base de datos.</p>",
    unsafe_allow_html=True
)

st.divider()

# --- TOTAL ARTICLES BANNER ---
total_articles = len(df)
st.markdown(
    f"""
    <div style="background-color:#1e1e1e; border: 1px solid #444;
                border-radius:10px; padding:18px 32px;
                display:flex; align-items:center; gap:20px; margin-bottom:8px;">
        <span style="font-size:36px;">📰</span>
        <div>
            <p style="color:#aaaaaa; font-size:13px; margin:0; text-transform:uppercase; letter-spacing:1px;">Total de artículos scrapeados</p>
            <p style="color:#ffffff; font-size:42px; font-weight:bold; margin:2px 0; line-height:1;">{total_articles:,}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# --- KPI CARDS ---
avg_per_media, change_per_media = get_weekly_avg_per_media(df)
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
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# --- CHARTS ---
fig_cumulative = plot_cumulative_articles_monthly(df)
st.plotly_chart(fig_cumulative, width="stretch")

st.divider()

fig_trend = plot_weekly_trend(df)
st.plotly_chart(fig_trend, width="stretch")

st.divider()

# --- DAILY SUMMARIES ---
@st.cache_data(ttl=3600)
def load_summaries():
    client_mongo = MongoClient(os.getenv("MONGODB_URI"))
    summaries_col = client_mongo["social_listening"]["daily_summaries"]
    result = {}
    for media_key in ['ellitoral', 'aire', 'lacapital', 'integrativo']:
        doc = summaries_col.find_one({"media": media_key}, sort=[("date", -1)])
        result[media_key] = doc["summary"] if doc else "Resumen no disponible aún."
    client_mongo.close()
    return result

summaries = load_summaries()

st.markdown("### ¿De qué habló cada medio esta semana?")
cols = st.columns(3)
for col, media in zip(cols, medias):
    color = colors[media]
    label = labels[media]
    summary = summaries.get(media, "")
    col.markdown(
        f"""
        <div style="background-color:#1e1e1e; border-left: 5px solid {color};
                    border-radius:8px; padding:20px 24px;">
            <p style="color:{color}; font-size:15px; font-weight:bold; margin:0 0 10px 0;">{label}</p>
            <p style="color:#dddddd; font-size:14px; line-height:1.6; margin:0;">{summary}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# --- RESUMEN INTEGRATIVO ---
st.markdown("### Agenda mediática del día")
integrativo = summaries.get("integrativo", "")
if integrativo:
    st.markdown(
        f"""
        <div style="background-color:#1e1e1e; border-left: 5px solid #aaaaaa;
                    border-radius:8px; padding:20px 28px;">
            <p style="color:#dddddd; font-size:15px; line-height:1.7; margin:0;">{integrativo}</p>
        </div>
        """,
        unsafe_allow_html=True
    )