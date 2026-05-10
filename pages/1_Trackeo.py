import streamlit as st
from social_listening_app import load_data
from features_cuantitativa import plot_word_count_by_period, plot_word_count_by_period_relative

st.set_page_config(layout="wide", page_title="Trackeo de Términos")

df = load_data()

st.title("Trackeo de Términos")

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