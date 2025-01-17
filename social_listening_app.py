import streamlit as st
from mongodb_features import reading_data
from features_general import plot_cumulative_articles, plot_article_distribution, plot_avg_articles_per_day

st.set_page_config(layout="wide")
df = reading_data("social_listening", "drugtrafficking")


# Define the content for the three pages
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
    


def cuantitativa_page():
    st.title("Cuantitativa")
    st.write("This is the Cuantitativa page. You can add quantitative analysis and visualizations here.")

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
