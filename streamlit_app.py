import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# 1. CONFIGURACIÓN Y TÍTULO
st.set_page_config(page_title="Dashboard Emisiones Transporte")
st.title("🌱 Análisis de Emisiones - Transporte en Ruta")
st.markdown("Datos obtenidos de la API de **datos.gob.cl**")

# 2. EXTRACCIÓN Y LIMPIEZA DE DATOS (API)

API_URL = "https://datos.gob.cl/api/3/action/datastore_search"
RESOURCE_ID = "901174b2-5caf-411c-96f0-866fedf7f838"

@st.cache_data
def cargar_datos(limite=500):
    # Obtener datos de la API
    params = {"resource_id": RESOURCE_ID, "limit": limite}
    try:
        response = requests.get(API_URL, params=params, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()
        
        datos = response.json()
        df = pd.DataFrame(datos["result"]["records"])
        
        # Limpieza básica
        if "_id" in df.columns:
            df = df.drop(columns=["_id"])
        
        df = df.replace(["NULL", "null", "", "None"], pd.NA)
        return df
        
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()
    
# 3. INTERFAZ DE USUARIO 
limite = st.slider("Cantidad de registros a descargar:", 50, 2000, 500, step=50)

with st.spinner("Descargando datos..."):
    df_emisiones = cargar_datos(limite)

if not df_emisiones.empty:
    st.success(f"Se cargaron {len(df_emisiones)} registros.")
    
    # Mostrar la tabla de datos
    with st.expander("Ver tabla de datos"):
        st.dataframe(df_emisiones, use_container_width=True)
    
    # --- NUEVA SECCIÓN DE ANÁLISIS ESTADÍSTICO ---
    st.subheader("📊 Resumen Estadístico")
    st.write("Cálculo automático de promedios, máximos y mínimos de las columnas numéricas:")
    st.dataframe(df_emisiones.describe())
    # ---------------------------------------------
    
    # 4. GRÁFICO DE BARRAS

    st.subheader("Análisis de Categorías")
    

    
    # Filtramos solo las columnas que son texto (categorías)
    columnas_cat = df_emisiones.select_dtypes(include=["object"]).columns.tolist()
    
    if columnas_cat:
        # Selector para elegir qué graficar
        col_seleccionada = st.selectbox("Seleccione la categoría a graficar:", columnas_cat)
        
        # Crear el gráfico
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # Contar los 10 valores más comunes de la columna elegida
        conteo = df_emisiones[col_seleccionada].value_counts().head(10)
        
        # Dibujar las barras
        conteo.plot(kind='bar', color="#2ca02c", edgecolor="black", ax=ax)
        
        ax.set_title(f"Top 10: {col_seleccionada}", fontsize=14, fontweight='bold')
        ax.set_ylabel("Cantidad de Registros", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Mostrar el gráfico en la web
        st.pyplot(fig)
    else:
        st.warning("No se encontraron columnas de texto para graficar.")
else:
    st.error("No se pudo cargar la base de datos.")