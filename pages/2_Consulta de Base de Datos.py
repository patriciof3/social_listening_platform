import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from features_general import get_data
st.set_page_config(layout="wide", page_title="Consulta de Base de Datos")

df = get_data()

st.title("Consulta de Base de Datos")
st.markdown(
    "<p style='color: white; font-size: 18px;'>Filtra los artículos por fecha, medio o palabras clave, y visualiza los resultados.</p>",
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Fecha inicial", value=pd.to_datetime("2025-08-01"))
with col2:
    end_date = st.date_input("Fecha final", value=df['date'].max())

media_options = sorted(df['media'].dropna().unique().tolist())
selected_media = st.multiselect("Selecciona medio(s)", media_options, default=media_options)

keyword = st.text_input("Filtrar por palabra o frase en el contenido", "")

apply_filter = st.button("🔍 Aplicar filtros")

if apply_filter:
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

    gb = GridOptionsBuilder.from_dataframe(filtered_df)
    gb.configure_default_column(editable=True, wrapText=True, resizable=True)
    AgGrid(filtered_df, gridOptions=gb.build(), height=400, fit_columns_on_grid_load=True)

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="articulos_filtrados.csv",
        mime='text/csv'
    )
else:
    st.info("Selecciona los filtros y haz clic en **Aplicar filtros** para ver los resultados.")