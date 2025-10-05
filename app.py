import streamlit as st
import pandas as pd
import plotly.express as px
from unidecode import unidecode 

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Inventario Universal del Llano (Desde Cero)",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definición de las opciones de Presentación y Categoría
PRESENTACION_OPCIONES = ['libra', 'kilogramo', 'litro', 'paquete', 'unidad']
CATEGORIA_OPCIONES = [
    'Harinas',
    'Margarinas',
    'Embutidos',
    'Esencias y colorantes',
    'Salsas y conservas',
    'Varios y acompañantes, Panadería y pastelería',
    'Lácteos',
    'Desechables',
    'Moldes, motivos y utensilios'
]

# --- FUNCIONES DE AYUDA ---

def clean_col_name(col):
    """Limpia el nombre de la columna: elimina tildes, espacios, y convierte a mayúsculas."""
    return unidecode(col).strip().replace(' ', '_').upper()

def add_product(new_id, new_category, new_name, new_presentation, new_stock):
    """Añade un nuevo producto al DataFrame de inventario."""
    new_row = pd.DataFrame([{
        'ID': new_id,
        'Producto': new_name,
        'Stock': new_stock,
        'Categoría': new_category,
        'Presentación': new_presentation,
        'Ventas': 0,
        'Compras': 0
    }])
    st.session_state.df_inventario = pd.concat([st.session_state.df_inventario, new_row], ignore_index=True)
    st.success(f"Producto '{new_name}' (ID: {new_id}) añadido con éxito!")

# NOTA: Las funciones de carga masiva (process_sales_from_df y process_purchases_from_df)
# han sido eliminadas ya que no hay archivos iniciales que cargar.

# --- INICIALIZACIÓN DE DATOS (Completamente Vacío) ---

# Inventario principal
if 'df_inventario' not in st.session_state:
    columnas = ['ID', 'Producto', 'Stock', 'Categoría', 'Presentación', 'Ventas', 'Compras']
    st.session_state.df_inventario = pd.DataFrame(columns=columnas)
    st.warning("⚠️ Inventario inicial vacío. Añade productos desde 'Registro de Productos'.")

# Historial de registros (Completamente vacíos al inicio)
if 'df_ventas_hist' not in st.session_state:
    st.session_state.df_ventas_hist = pd.DataFrame(columns=['ID', 'Producto', 'Cantidad'])

if 'df_compras_hist' not in st.session_state:
    st.session_state.df_compras_hist = pd.DataFrame(columns=['ID', 'Producto', 'Cantidad'])


# --- NAVEGACIÓN EN EL SIDEBAR ---
st.sidebar.header("Menú de Navegación")
ventana_seleccionada = st.sidebar.radio( 
    "Selecciona una ventana:",
    ('Dashboard', 'Registro de Productos', 'Registro de Ventas', 'Registro de Compras')
)

# -------------------------------------------------------------------------
# CÓDIGO PARA MOSTRAR LA IMAGEN EN EL SIDEBAR
# -------------------------------------------------------------------------
st.sidebar.markdown("---") 
try:
    st.sidebar.image(
        "logo_empresa.png", 
        caption="Distribuidora Universal del Llano" 
    )
except FileNotFoundError:
    st.sidebar.info("Sube tu logo (ej: 'logo_empresa.png') a GitHub para verlo aquí.")
# -------------------------------------------------------------------------

# ----------------------------------------------------
# --- ESTRUCTURA DE LA APLICACIÓN ---
# ----------------------------------------------------

# --- DASHBOARD (Mantenido) ---
if ventana_seleccionada == 'Dashboard':
    df_inventario = st.session_state.df_inventario
    st.title("📦 Control de Inventario - Distribuidora Universal del Llano")
    st.header("📊 Dashboard de Inventario")

    if df_inventario.empty:
        st.info("No hay productos en el inventario. Añada productos desde 'Registro de Productos' para ver el Dashboard.")
    else:
        # Cálculo de KPIs
        total_productos_unicos = df_inventario['Producto'].nunique()
        total_unidades_stock = df_inventario['Stock'].astype(int).sum()
        productos_bajo_stock = df_inventario[df_inventario['Stock'].astype(int) <= 10].shape[0]

        # Mostrar KPIs
        st.subheader("Indicadores Clave (KPIs)")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total de Productos Únicos", f"{total_productos_unicos}")
        with col2: st.metric("Total de Unidades en Stock", f"{total_unidades_stock}")
        with col3: st.metric("Productos con Bajo Stock (<=10)", f"{productos_bajo_stock}")

        st.markdown("---") 
        st.subheader("Visualizaciones")
        viz_col1, viz_col2 = st.columns(2)

        # Gráfico 1: Niveles de Stock por Producto
        with viz_col1:
            st.markdown("##### Niveles de Stock por Producto")
            df_stock_sorted = df_inventario.sort_values(by='Stock', ascending=False)
            fig_stock = px.bar(df_stock_sorted, x='Producto', y='Stock', text='Stock', 
                               title="Stock por Producto", color='Producto', height=350)
            st.plotly_chart(fig_stock, use_container_width=True)

        # Gráfico 2: Distribución de Productos por Categoría 
        with viz_col2:
            st.markdown("##### Distribución de Productos por Categoría")
            df_categoria = df_inventario.groupby('Categoría').size().reset_index(name='Count')
            fig_categoria = px.pie(df_categoria, names='Categoría', values='Count', 
                                   title='Productos por Categoría', height=350)
            st.plotly_chart(fig_categoria, use_container_width=True)

        st.markdown("---") 
        st.subheader("Análisis de Movimientos")
        mov_col1, mov_col2 = st.columns(2)

        # Gráfico 3: Top Productos Más Vendidos (Comienza en 0)
        with mov_col1:
            st.markdown("##### Top 5 Productos Más Vendidos")
            df_ventas = df_inventario.sort_values(by='Ventas', ascending=False).head(5)
            fig_ventas = px.bar(df_ventas, x='Producto', y='Ventas', text='Ventas', 
                                title="Top 5 Ventas (Unidades Vendidas)", color='Producto', height=350)
            st.plotly_chart(fig_ventas, use_container_width=True)

        # Gráfico 4: Top Productos Más Comprados (Comienza en 0)
        with mov_col2:
            st.markdown("##### Top 5 Productos Más Comprados")
            # --- LÍNEA CORREGIDA AQUÍ: Cerrar el paréntesis después de head(5) ---
            df_compras = df_inventario.sort_values(by='Compras', ascending=False).head(5) 
            # -------------------------------------------------------------------
            fig_compras = px.bar(df_compras, x='Producto', y='Compras', text='Compras', 
                                 title="Top 5 Compras (Unidades Compradas)", color='Producto', height=350)
            st.plotly_chart(fig_compras, use_container_width=True)

