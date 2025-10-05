import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Inventario Universal del Llano",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INICIALIZACIÓN DE DATOS (DataFrame Vacío y Persistencia) ---
# El inventario se almacena en st.session_state
if 'df_inventario' not in st.session_state:
    columnas = ['ID', 'Producto', 'Stock', 'Categoría', 'Presentación', 'Ventas', 'Compras']
    # Crear un DataFrame completamente vacío
    st.session_state.df_inventario = pd.DataFrame(columns=columnas)

# --- FUNCIÓN PARA AÑADIR PRODUCTO ---
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

# --- NAVEGACIÓN EN EL SIDEBAR ---
st.sidebar.header("Menú de Navegación")
ventana_seleccionada = st.sidebar.radio(
    "Selecciona una ventana:",
    ('Dashboard', 'Registro de Productos', 'Registro de Ventas', 'Registro de Compras')
)

# -------------------------------------------------------------------------
# CÓDIGO PARA MOSTRAR LA IMAGEN EN EL SIDEBAR (Opción 2)
# -------------------------------------------------------------------------
# **IMPORTANTE:** Debes subir tu imagen (ej. logo_empresa.png) al repositorio.
st.sidebar.markdown("---") 
try:
    st.sidebar.image(
        "logo_empresa.png", # <--- ¡CAMBIA ESTE NOMBRE SI TU IMAGEN SE LLAMA DIFERENTE!
        caption="Distribuidora Universal del Llano" 
    )
except FileNotFoundError:
    st.sidebar.warning("Logo no encontrado. Sube 'logo_empresa.png' a GitHub.")
# -------------------------------------------------------------------------

# ----------------------------------------------------
# --- ESTRUCTURA DE LA APLICACIÓN ---
# ----------------------------------------------------

# --- DASHBOARD ---
if ventana_seleccionada == 'Dashboard':
    df_inventario = st.session_state.df_inventario
    
    st.title("📋 Control de Inventario - Distribuidora Universal del Llano")
    st.header("📊 Dashboard KPI's de Inventario")

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
            fig_stock.update_traces(textposition='outside')
            fig_stock.update_layout(xaxis_title="", yaxis_title="Stock")
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

        # Gráfico 3: Top Productos Más Vendidos (usando datos simulados, ya que los reales son 0)
        with mov_col1:
            st.markdown("##### Top 5 Productos Más Vendidos")
            # Usamos una columna simulada si las ventas son todas 0 para evitar que se vea vacío
            df_ventas = df_inventario.assign(Ventas_Sim=lambda x: x['Ventas'] + 1).sort_values(by='Ventas_Sim', ascending=False).head(5)
            fig_ventas = px.bar(df_ventas, x='Producto', y='Ventas', text='Ventas', 
                                title="Top 5 Ventas (Unidades Vendidas)", color='Producto', height=350)
            fig_ventas.update_traces(textposition='outside')
            fig_ventas.update_layout(xaxis_title="", yaxis_title="Unidades Vendidas")
            st.plotly_chart(fig_ventas, use_container_width=True)

        # Gráfico 4: Top Productos Más Comprados
        with mov_col2:
            st.markdown("##### Top 5 Productos Más Comprados")
            df_compras = df_inventario.assign(Compras_Sim=lambda x: x['Compras'] + 1).sort_values(by='Compras_Sim', ascending=False).head(5)
            fig_compras = px.bar(df_compras, x='Producto', y='Compras', text='Compras', 
                                 title="Top 5 Compras (Unidades Compradas)", color='Producto', height=350)
            fig_compras.update_traces(textposition='outside')
            fig_compras.update_layout(xaxis_title="", yaxis_title="Unidades Compradas")
            st.plotly_chart(fig_compras, use_container_width=True)


# --- REGISTRO DE PRODUCTOS (CON FORMULARIO Y ELIMINACIÓN) ---
elif ventana_seleccionada == 'Registro de Productos':
    st.title("📝 Registro de Productos")
    st.header("Ingresa los datos del nuevo producto:")

    # --- 1. FORMULARIO DE INGRESO ---
    with st.form("registro_producto_form"):
        col_left, col_right = st.columns(2)

        # Columna Izquierda
        with col_left:
            id_producto = st.text_input("Identificador del Producto (ID)", key="id_input")
            nombre_producto = st.text_input("Nombre del Producto", key="name_input")
        
        # Columna Derecha
        with col_right:
            categoria = st.text_input("Categoría", key="category_input")
            presentacion = st.text_input("Presentación (Ej: Caja, Unidad, Litro)", key="presentation_input")

        # Campo Stock Inicial (Control numérico)
        stock_inicial = st.number_input("Stock Inicial", min_value=0, value=0, step=1, key="stock_input")

        submit_button = st.form_submit_button("Añadir Producto")
        
        # Lógica al enviar el formulario
        if submit_button:
            if not all([id_producto, nombre_producto, categoria, presentacion]):
                st.error("Por favor, completa todos los campos para añadir el producto.")
            else:
                if id_producto.upper() in st.session_state.df_inventario['ID'].str.upper().values:
                    st.error(f"Error: El ID '{id_producto}' ya existe. Por favor, usa un ID único.")
                else:
                    add_product(id_producto.upper(), categoria, nombre_producto, presentacion, stock_inicial)

    # --- 2. GESTIÓN Y ELIMINACIÓN ---
    st.markdown("---")
    st.subheader("🗑️ Eliminación de Productos")

    if st.session_state.df_inventario.empty:
        st.info("Aún no hay productos registrados para gestionar o eliminar.")
    else:
        df_inventario_actual = st.session_state.df_inventario.copy()

        # Opción de selección múltiple de IDs para eliminar
        productos_a_eliminar = st.multiselect(
            "Selecciona los IDs de los productos que deseas eliminar:",
            options=df_inventario_actual['ID'].tolist(),
            key='delete_multiselect'
        )

        delete_button = st.button("❌ Eliminar Productos Seleccionados")

        if delete_button:
            if productos_a_eliminar:
                st.session_state.df_inventario = st.session_state.df_inventario[
                    ~st.session_state.df_inventario['ID'].isin(productos_a_eliminar)
                ]
                st.success(f"Productos eliminados: {', '.join(productos_a_eliminar)}")
                st.rerun() 
            else:
                st.warning("No seleccionaste ningún producto para eliminar.")

    # --- 3. INVENTARIO ACTUAL ---
    st.markdown("---")
    st.subheader("Inventario Actual")
    st.dataframe(st.session_state.df_inventario, use_container_width=True)

# --- REGISTRO DE VENTAS (Simulación) ---
elif ventana_seleccionada == 'Registro de Ventas':
    st.title("📈 Registro de Ventas")
    st.info("Aquí se construiría el formulario y la tabla para registrar transacciones de venta.")
    if not st.session_state.df_inventario.empty:
        st.dataframe(st.session_state.df_inventario[['ID', 'Producto', 'Stock', 'Ventas']], use_container_width=True)

# --- REGISTRO DE COMPRAS (Simulación) ---
elif ventana_seleccionada == 'Registro de Compras':
    st.title("🛒 Registro de Compras")
    st.info("Aquí se construiría el formulario y la tabla para registrar entradas de inventario por compra.")
    if not st.session_state.df_inventario.empty:
        st.dataframe(st.session_state.df_inventario[['ID', 'Producto', 'Stock', 'Compras']], use_container_width=True)

