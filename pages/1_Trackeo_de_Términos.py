import streamlit as st
from features_cuantitativa import plot_word_count_by_period, plot_word_count_by_period_relative
from features_general import get_data

st.set_page_config(layout="wide", page_title="Trackeo de Términos")

df = get_data()

st.title("Trackeo de Términos")

st.markdown(
    """<p style='color: white; font-size: 20px;'>
    Ingresá un término para ver con qué frecuencia apareció en los artículos scrapeados. 
    El primer gráfico muestra la cantidad de artículos que lo mencionan por período — 
    al pasar el cursor sobre cada barra podés ver también las menciones totales, contando 
    repeticiones dentro del mismo artículo. El segundo gráfico normaliza ese recuento 
    por el total de artículos publicados en cada período, para comparar la relevancia 
    del término independientemente del volumen de cobertura.
    </p>""",
    unsafe_allow_html=True
)
col1, col2 = st.columns(2)
with col1:
    period = st.selectbox("¿En qué intervalo de tiempo quieres visualizar el término?", ("Mensual", "Anual"))
with col2:
    word_to_count = st.text_input("Término para graficar:", "monos")

if word_to_count:
    fig, word_count, word_present = plot_word_count_by_period(df, word_to_count, period)
    st.plotly_chart(fig, width='stretch')
    st.write(f"La palabra '{word_to_count}' aparece {word_count} veces, en un total de {word_present} artículos.")

    fig, word_count, word_present = plot_word_count_by_period_relative(df, word_to_count, period)
    st.plotly_chart(fig, width='stretch')
else:
    st.write("No hay palabra seleccionada.")