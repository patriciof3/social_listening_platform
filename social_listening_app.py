import streamlit as st

# Define the content for the three pages
def general_page():
    st.title("General")
    st.write("Esta app expone los resultados de un scrapping de noticias vinculadas al narcotráfico en portales de la provincia de Santa Fe")

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
