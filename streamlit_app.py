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
    
    # --- 1. TRADUCCIÓN Y LIMPIEZA DE COLUMNAS (CORREGIDO) ---
    columnas_limpias = {
        "ano": "Año",
        "id_comuna": "ID Comuna",
        "glosa_comuna": "Comuna",
        "id_provincia": "ID Provincia",
        "glosa_provincia": "Provincia",
        "id_region": "ID Región",
        "glosa_region": "Región",
        "categoria_vehiculo": "Categoría Vehículo",
        "tipo_vehiculo": "Tipo Vehículo",
        "tipo_emision": "Tipo Combustible",  # <- Aquí estaba el detalle: la API lo llama tipo_emision
        "tecnologia": "Tecnología",
        "emision_co2_t": "Emisiones CO2 (Toneladas)",
        "emision_ch4_t": "Emisiones CH4 (Toneladas)",
        "emision_n2o_t": "Emisiones N2O (Toneladas)"
    }
    df_emisiones = df_emisiones.rename(columns=columnas_limpias)
    
    # --- 2. BARRA LATERAL CON FILTROS DINÁMICOS ---
    st.sidebar.header("🎯 Filtros de Búsqueda")
    
    # Filtro de Tipo de Vehículo (Si la columna existe en los datos)
    if "Tipo Vehículo" in df_emisiones.columns:
        lista_vehiculos = ["Todos"] + sorted(list(df_emisiones["Tipo Vehículo"].dropna().unique()))
        vehiculo_sel = st.sidebar.selectbox("Selecciona Tipo de Vehículo:", lista_vehiculos)
        if vehiculo_sel != "Todos":
            df_emisiones = df_emisiones[df_emisiones["Tipo Vehículo"] == vehiculo_sel]
    
    # Filtro de Tipo de Combustible (Ahora buscará "Tipo Combustible" con éxito)
    if "Tipo Combustible" in df_emisiones.columns:
        lista_combustibles = ["Todos"] + sorted(list(df_emisiones["Tipo Combustible"].dropna().unique()))
        combustible_sel = st.sidebar.selectbox("Selecciona Tipo de Combustible:", lista_combustibles)
        if combustible_sel != "Todos":
            df_emisiones = df_emisiones[df_emisiones["Tipo Combustible"] == combustible_sel]
    # ----------------------------------------------------

    ## --- 3. TARJETAS DE MÉTRICAS CLAVE (KPIs) (REPARADO Y CONVERTIDO) ---
    st.markdown("### 📈 Indicadores Clave (Filtrados)")
    
    total_registros_filtrados = len(df_emisiones)
    
    # Identificamos el nombre de la columna
    col_toneladas = "cantidad_toneladas" if "cantidad_toneladas" in df_emisiones.columns else "Cantidad Toneladas"
    
    if col_toneladas in df_emisiones.columns:
        try:
            # CORRECCIÓN DE TIPO: Convertimos las comas a puntos y pasamos a número float
            if df_emisiones[col_toneladas].dtype == 'object':
                df_emisiones[col_toneladas] = df_emisiones[col_toneladas].astype(str).str.replace(',', '.')
                df_emisiones[col_toneladas] = pd.to_numeric(df_emisiones[col_toneladas], errors='coerce')
            
            # Operaciones matemáticas seguras
            toneladas_totales = df_emisiones[col_toneladas].sum()
            promedio_por_ruta = df_emisiones[col_toneladas].mean() if total_registros_filtrados > 0 else 0
        except Exception:
            toneladas_totales = 0
            promedio_por_ruta = 0
    else:
        toneladas_totales = 0
        promedio_por_ruta = 0
    
    # Desplegamos las tarjetas actualizadas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Muestra Activa", value=f"{total_registros_filtrados} filas")
    with col2:
        st.metric(label="Total Contaminantes (t)", value=f"{toneladas_totales:,.2f}")
    with col3:
        st.metric(label="Promedio por Registro (t)", value=f"{promedio_por_ruta:,.4f}")
    
    st.markdown("---")
    # ----------------------------------------------------
    
    # Mostrar la tabla de datos
    with st.expander("🔍 Ver tabla de datos detallada"):
        st.dataframe(df_emisiones, use_container_width=True)
    
    # --- SECCIÓN DE ANÁLISIS ESTADÍSTICO ---
    st.subheader("📊 Resumen Estadístico")
    st.write("Cálculo automático de promedios, máximos y mínimos:")
    
    resumen = df_emisiones.describe()
    resumen = resumen.rename(index={
        "count": "Total registros",
        "unique": "Valores únicos",
        "top": "Valor más común",
        "freq": "Frecuencia"
    })
    st.dataframe(resumen, use_container_width=True)
    # ----------------------------------------------------
    
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