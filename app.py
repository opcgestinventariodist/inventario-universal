import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# --- CONFIGURACIÓN DE LA PÁGINA (Debe ser lo primero) ---
st.set_page_config(
    page_title="Inventario Universal del Llano",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIMULACIÓN DE DATOS (Para replicar el Dashboard) ---

# Crear un DataFrame de inventario
data = {
    'Producto': ['Silla', 'Mueble'],
    'Stock': [80, 25], # Stock total de 105 (80+25)
    'Categoría': ['Sala', 'Cocina'], # 50/50 de las 2 unidades únicas
    'Ventas': [35, 20], # Silla más vendida (35) y Mueble (20)
    'Compras': [0, 10]  # Mueble más comprado (10)
}
df_inventario = pd.DataFrame(data)

# --- NAVEGACIÓN EN EL SIDEBAR (Menú de Navegación) ---
st.sidebar.header("Menú de Navegación")
ventana_seleccionada = st.sidebar.radio(
    "Selecciona una ventana:",
    ('Dashboard', 'Registro de Productos', 'Registro de Ventas', 'Registro de Compras')
)

# ----------------------------------------------------
# --- ESTRUCTURA DE LA APLICACIÓN: DASHBOARD (Ventana Principal) ---
# ----------------------------------------------------

if ventana_seleccionada == 'Dashboard':
    # Título Principal
    st.title("📦 Control de Inventario - Distribuidora Universal del Llano")
    st.header("📊 Dashboard de Inventario")
    
    # --- 1. INDICADORES CLAVE (KPIs) ---
    st.subheader("Indicadores Clave (KPIs)")
    
    # Cálculo de los KPIs
    total_productos_unicos = df_inventario['Producto'].nunique()
    total_unidades_stock = df_inventario['Stock'].sum()
    productos_bajo_stock = df_inventario[df_inventario['Stock'] <= 10].shape[0]

    # Mostrar los KPIs en columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Productos Únicos", f"{total_productos_unicos}")

    with col2:
        st.metric("Total de Unidades en Stock", f"{total_unidades_stock}")
        
    with col3:
        st.metric("Productos con Bajo Stock (<=10)", f"{productos_bajo_stock}")

    st.markdown("---") # Separador visual

    # --- 2. VISUALIZACIONES (Gráficos) ---
    st.subheader("Visualizaciones")
    
    # Crear dos columnas para los gráficos de Stock y Categoría
    viz_col1, viz_col2 = st.columns(2)

    # Gráfico 1: Niveles de Stock por Producto (Bar Chart)
    with viz_col1:
        st.markdown("##### Niveles de Stock por Producto")
        fig_stock = px.bar(
            df_inventario, 
            x='Producto', 
            y='Stock', 
            text='Stock', 
            title="Stock por Producto",
            color='Producto',
            height=350
        )
        fig_stock.update_traces(textposition='outside')
        fig_stock.update_layout(xaxis_title="", yaxis_title="Stock")
        st.plotly_chart(fig_stock, use_container_width=True)

    # Gráfico 2: Distribución de Productos por Categoría (Pie Chart)
    with viz_col2:
        st.markdown("##### Distribución de Productos por Categoría")
        # Usamos el conteo de filas, que es 1 por cada producto único.
        df_categoria = df_inventario.groupby('Categoría').size().reset_index(name='Count')
        fig_categoria = px.pie(
            df_categoria, 
            names='Categoría', 
            values='Count', 
            title='Productos por Categoría',
            height=350
        )
        st.plotly_chart(fig_categoria, use_container_width=True)

    st.markdown("---") # Separador visual

    # --- 3. ANÁLISIS DE MOVIMIENTOS (Ventas y Compras) ---
    st.subheader("Análisis de Movimientos")

    # Crear dos columnas para los gráficos de Ventas y Compras
    mov_col1, mov_col2 = st.columns(2)

    # Gráfico 3: Top Productos Más Vendidos
    with mov_col1:
        st.markdown("##### Top 5 Productos Más Vendidos")
        df_ventas = df_inventario.sort_values(by='Ventas', ascending=False).head(5)
        fig_ventas = px.bar(
            df_ventas, 
            x='Producto', 
            y='Ventas', 
            text='Ventas', 
            title="Top 5 Ventas (Unidades Vendidas)",
            color='Producto',
            height=350
        )
        fig_ventas.update_traces(textposition='outside')
        fig_ventas.update_layout(xaxis_title="", yaxis_title="Unidades Vendidas")
        st.plotly_chart(fig_ventas, use_container_width=True)

    # Gráfico 4: Top Productos Más Comprados
    with mov_col2:
        st.markdown("##### Top 5 Productos Más Comprados")
        df_compras = df_inventario.sort_values(by='Compras', ascending=False).head(5)
        fig_compras = px.bar(
            df_compras, 
            x='Producto', 
            y='Compras', 
            text='Compras', 
            title="Top 5 Compras (Unidades Compradas)",
            color='Producto',
            height=350
        )
        fig_compras.update_traces(textposition='outside')
        fig_compras.update_layout(xaxis_title="", yaxis_title="Unidades Compradas")
        st.plotly_chart(fig_compras, use_container_width=True)

# ----------------------------------------------------
# --- ESTRUCTURA DE LA APLICACIÓN: OTRAS PESTAÑAS (Funcionalidad Simulada) ---
# ----------------------------------------------------

elif ventana_seleccionada == 'Registro de Productos':
    st.title("➕ Registro de Productos")
    st.info("Aquí se construiría la interfaz para agregar, editar o eliminar productos del inventario.")
    st.dataframe(df_inventario) # Muestra los datos de ejemplo

elif ventana_seleccionada == 'Registro de Ventas':
    st.title("💸 Registro de Ventas")
    st.info("Aquí se construiría el formulario y la tabla para registrar transacciones de venta.")

elif ventana_seleccionada == 'Registro de Compras':
    st.title("🛒 Registro de Compras")
    st.info("Aquí se construiría el formulario y la tabla para registrar entradas de inventario por compra.")