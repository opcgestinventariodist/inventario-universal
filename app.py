import streamlit as st
import pandas as pd
import plotly.express as px
from unidecode import unidecode 

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Inventario Universal del Llano",
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


def process_sales_from_df(df_ventas_new):
    """Procesa un DataFrame de ventas (carga masiva), actualiza el inventario y el historial."""
    
    # 1. Estandarizar y validar columnas
    df_ventas_new.columns = [clean_col_name(col) for col in df_ventas_new.columns]

    if 'ID' not in df_ventas_new.columns:
        return 0, [], "Columna 'ID' faltante."
        
    col_cantidad_vendida = [col for col in df_ventas_new.columns if 'CANTIDAD_VENDIDA' in col]
    if not col_cantidad_vendida:
         return 0, [], "Columna 'Cantidad Vendida' faltante."

    # Renombrar para facilitar el procesamiento
    df_ventas_new = df_ventas_new[['ID', col_cantidad_vendida[0]]].rename(columns={col_cantidad_vendida[0]: 'CANTIDAD_VENDIDA'})

    # 2. Preparar los datos
    df_ventas_new['ID'] = df_ventas_new['ID'].astype(str).str.upper().str.strip()
    df_ventas_new['CANTIDAD_VENDIDA'] = pd.to_numeric(df_ventas_new['CANTIDAD_VENDIDA'], errors='coerce').fillna(0).astype(int)
    df_ventas_new = df_ventas_new[df_ventas_new['CANTIDAD_VENDIDA'] > 0]
    
    if st.session_state.df_inventario.empty:
        return 0, [], "El inventario base está vacío."
        
    if df_ventas_new.empty:
        return 0, [], "El archivo de ventas no contiene datos válidos."

    # 3. Procesar las ventas
    ventas_exitosas = 0
    ventas_fallidas = []
    nuevos_registros_historial = []

    df_inventario_temp = st.session_state.df_inventario.copy()
    
    for index, row in df_ventas_new.iterrows():
        product_id = row['ID']
        cantidad = row['CANTIDAD_VENDIDA']
        
        match = df_inventario_temp[df_inventario_temp['ID'] == product_id]
        
        if not match.empty:
            idx = match.index[0]
            product_name = df_inventario_temp.loc[idx, 'Producto']
            
            # Aplica la venta (permite stock negativo)
            df_inventario_temp.loc[idx, 'Stock'] -= cantidad
            df_inventario_temp.loc[idx, 'Ventas'] += cantidad
            
            # Registrar para historial
            nuevos_registros_historial.append({
                'ID': product_id, 
                'Producto': product_name, 
                'Cantidad': cantidad
            })
            ventas_exitosas += 1
            
        else:
            ventas_fallidas.append(f"ID {product_id}: No encontrado en el inventario.")
            
    # 4. Aplicar cambios al state si hubo éxito
    if ventas_exitosas > 0:
        st.session_state.df_inventario = df_inventario_temp
        df_hist_new = pd.DataFrame(nuevos_registros_historial)
        # Se añade al historial de ventas y se CONSERVA
        st.session_state.df_ventas_hist = pd.concat([st.session_state.df_ventas_hist, df_hist_new], ignore_index=True)

    return ventas_exitosas, ventas_fallidas, None


def process_purchases_from_df(df_compras_new):
    """Procesa un DataFrame de compras (carga masiva), actualiza el inventario y el historial."""
    
    # 1. Estandarizar y validar columnas
    df_compras_new.columns = [clean_col_name(col) for col in df_compras_new.columns]

    if 'ID' not in df_compras_new.columns:
        return 0, [], "Columna 'ID' faltante."
        
    col_cantidad_comprada = [col for col in df_compras_new.columns if 'CANTIDAD_COMPRADA' in col]
    if not col_cantidad_comprada:
         return 0, [], "Columna 'Cantidad Comprada' faltante."

    # Renombrar para facilitar el procesamiento
    df_compras_new = df_compras_new[['ID', col_cantidad_comprada[0]]].rename(columns={col_cantidad_comprada[0]: 'CANTIDAD_COMPRADA'})

    # 2. Preparar los datos
    df_compras_new['ID'] = df_compras_new['ID'].astype(str).str.upper().str.strip()
    df_compras_new['CANTIDAD_COMPRADA'] = pd.to_numeric(df_compras_new['CANTIDAD_COMPRADA'], errors='coerce').fillna(0).astype(int)
    df_compras_new = df_compras_new[df_compras_new['CANTIDAD_COMPRADA'] > 0]
    
    if st.session_state.df_inventario.empty:
        return 0, [], "El inventario base está vacío."
        
    if df_compras_new.empty:
        return 0, [], "El archivo de compras no contiene datos válidos."

    # 3. Procesar las compras
    compras_exitosas = 0
    compras_fallidas = []
    nuevos_registros_historial = []

    df_inventario_temp = st.session_state.df_inventario.copy()
    
    for index, row in df_compras_new.iterrows():
        product_id = row['ID']
        cantidad = row['CANTIDAD_COMPRADA']
        
        match = df_inventario_temp[df_inventario_temp['ID'] == product_id]
        
        if not match.empty:
            idx = match.index[0]
            product_name = df_inventario_temp.loc[idx, 'Producto']
            
            # Aplica la compra (SUMA al stock)
            df_inventario_temp.loc[idx, 'Stock'] += cantidad
            df_inventario_temp.loc[idx, 'Compras'] += cantidad
            
            # Registrar para historial
            nuevos_registros_historial.append({
                'ID': product_id, 
                'Producto': product_name, 
                'Cantidad': cantidad
            })
            compras_exitosas += 1
            
        else:
            compras_fallidas.append(f"ID {product_id}: No encontrado en el inventario.")
            
    # 4. Aplicar cambios al state si hubo éxito
    if compras_exitosas > 0:
        st.session_state.df_inventario = df_inventario_temp
        df_hist_new = pd.DataFrame(nuevos_registros_historial)
        # Se añade al historial de compras y se CONSERVA
        st.session_state.df_compras_hist = pd.concat([st.session_state.df_compras_hist, df_hist_new], ignore_index=True)

    return compras_exitosas, compras_fallidas, None


# --- INICIALIZACIÓN DE DATOS (DataFrame Vacío y Persistencia) ---

# Inventario principal
if 'df_inventario' not in st.session_state:
    columnas = ['ID', 'Producto', 'Stock', 'Categoría', 'Presentación', 'Ventas', 'Compras']
    df_inventario_vacio = pd.DataFrame(columns=columnas)
    
    # === 1. LÓGICA DE CARGA AUTOMÁTICA DEL INVENTARIO INICIAL (inventario_inicial.xlsx) ===
    try:
        INVENTARIO_FILE_PATH = 'inventario_inicial.xlsx' 
        
        if INVENTARIO_FILE_PATH.endswith('.csv'):
            df_inicial = pd.read_csv(INVENTARIO_FILE_PATH)
        else:
            df_inicial = pd.read_excel(INVENTARIO_FILE_PATH) 
        
        df_inicial.columns = [clean_col_name(col) for col in df_inicial.columns]
        
        # 1. Inicializar el inventario base
        df_cargado = pd.DataFrame({
            'ID': df_inicial['ID'].astype(str).str.upper().str.strip(),
            'Producto': df_inicial['PRODUCTO'],
            'Stock': pd.to_numeric(df_inicial['STOCK_INICIAL'], errors='coerce').fillna(0).astype(int),
            'Categoría': df_inicial['CATEGORIA'], 
            'Presentación': df_inicial['PRESENTACION'],
            'Ventas': 0, # Inicializados en 0, los movimientos se sumarán en pasos 2 y 3
            'Compras': 0
        })
        
        st.session_state.df_inventario = df_cargado
        st.toast("✅ Inventario base cargado desde archivo inicial.", icon="📦")
        
    except FileNotFoundError:
        st.session_state.df_inventario = df_inventario_vacio
        st.warning("No se encontró 'inventario_inicial.xlsx'. Iniciando con inventario vacío.")
        
    except Exception as e:
        st.error(f"Error al cargar el archivo de inventario. Revise el formato y el error: {e}")
        st.session_state.df_inventario = df_inventario_vacio

# Historial de registros (Comienzan vacíos)
if 'df_ventas_hist' not in st.session_state:
    st.session_state.df_ventas_hist = pd.DataFrame(columns=['ID', 'Producto', 'Cantidad'])

if 'df_compras_hist' not in st.session_state:
    st.session_state.df_compras_hist = pd.DataFrame(columns=['ID', 'Producto', 'Cantidad'])


# === 2. LÓGICA DE CARGA AUTOMÁTICA DE VENTAS DE MOVIMIENTO (ventas_mes1.xlsx) ===
if not st.session_state.df_inventario.empty:
    
    VENTAS_FILE_PATH = 'ventas_mes1.xlsx' 
    
    try:
        if VENTAS_FILE_PATH.endswith('.csv'):
            df_ventas_github = pd.read_csv(VENTAS_FILE_PATH)
        else:
            df_ventas_github = pd.read_excel(VENTAS_FILE_PATH)
            
        ventas_exitosas, ventas_fallidas, error = process_sales_from_df(df_ventas_github)
        
        if error:
             st.warning(f"Error en el archivo '{VENTAS_FILE_PATH}': {error}")
             
        if ventas_exitosas > 0:
            st.toast(f"✅ {ventas_exitosas} ventas procesadas automáticamente desde '{VENTAS_FILE_PATH}'.", icon="💸")
        if ventas_fallidas:
            st.warning(f"⚠️ {len(ventas_fallidas)} ventas de '{VENTAS_FILE_PATH}' fallaron. Revise la ID de los productos faltantes.")
            
    except FileNotFoundError:
        pass
    except Exception as e:
        st.warning(f"No se pudo leer el archivo '{VENTAS_FILE_PATH}'. Asegúrese de que el formato (ID, Cantidad Vendida) sea correcto. Error: {e}")


# === 3. LÓGICA DE CARGA AUTOMÁTICA DE COMPRAS DE MOVIMIENTO (compras_mes1.xlsx) ===
if not st.session_state.df_inventario.empty:
    
    COMPRAS_FILE_PATH = 'compras_mes1.xlsx' 
    
    try:
        if COMPRAS_FILE_PATH.endswith('.csv'):
            df_compras_github = pd.read_csv(COMPRAS_FILE_PATH)
        else:
            df_compras_github = pd.read_excel(COMPRAS_FILE_PATH)
            
        compras_exitosas, compras_fallidas, error = process_purchases_from_df(df_compras_github)
        
        if error:
             st.warning(f"Error en el archivo '{COMPRAS_FILE_PATH}': {error}")
             
        if compras_exitosas > 0:
            st.toast(f"✅ {compras_exitosas} compras procesadas automáticamente desde '{COMPRAS_FILE_PATH}'.", icon="🛒")
        if compras_fallidas:
            st.warning(f"⚠️ {len(compras_fallidas)} compras de '{COMPRAS_FILE_PATH}' fallaron. Revise la ID de los productos faltantes.")
            
    except FileNotFoundError:
        pass 
    except Exception as e:
        st.warning(f"No se pudo leer el archivo '{COMPRAS_FILE_PATH}'. Asegúrese de que el formato (ID, Cantidad Comprada) sea correcto. Error: {e}")


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

        # Gráfico 3: Top Productos Más Vendidos
        with mov_col1:
            st.markdown("##### Top 5 Productos Más Vendidos")
            df_ventas = df_inventario.sort_values(by='Ventas', ascending=False).head(5)
            fig_ventas = px.bar(df_ventas, x='Producto', y='Ventas', text='Ventas', 
                                title="Top 5 Ventas (Unidades Vendidas)", color='Producto', height=350)
            st.plotly_chart(fig_ventas, use_container_width=True)

        # Gráfico 4: Top Productos Más Comprados
        with mov_col2:
            st.markdown("##### Top 5 Productos Más Comprados")
            df_compras = df_inventario.sort_values(by='Compras', ascending=False).head(5)
            fig_compras = px.bar(df_compras, x='Producto', y='Compras', text='Compras', 
                                 title="Top 5 Compras (Unidades Compradas)", color='Producto', height=350)
            st.plotly_chart(fig_compras, use_container_width=True)

# --- REGISTRO DE PRODUCTOS (Mantenido) ---
elif ventana_seleccionada == 'Registro de Productos':
    df_inventario = st.session_state.df_inventario
    st.title("➕ Registro de Productos")
    st.header("Registro Manual de Productos")

    # --- 1. FORMULARIO DE INGRESO MANUAL ---
    with st.form("registro_producto_form"):
        col_left, col_right = st.columns(2)

        # Columna Izquierda
        with col_left:
            id_producto = st.text_input("Identificador del Producto (ID)", key="id_manual_input")
            nombre_producto = st.text_input("Nombre del Producto", key="name_manual_input")
        
        # Columna Derecha
        with col_right:
            categoria = st.selectbox("Categoría", options=CATEGORIA_OPCIONES, key="category_manual_input")
            presentacion = st.selectbox("Presentación", options=PRESENTACION_OPCIONES, key="presentation_manual_input")

        # Campo Stock Inicial (Control numérico)
        stock_inicial = st.number_input("Stock Inicial", value=0, step=1, key="stock_manual_input")

        submit_button = st.form_submit_button("Añadir Producto Manualmente")
        
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
    st.subheader("⚠️ Gestión y Eliminación de Productos")

    if st.session_state.df_inventario.empty:
        st.info("Aún no hay productos registrados para gestionar o eliminar.")
    else:
        df_inventario_actual = st.session_state.df_inventario.copy()

        productos_a_eliminar = st.multiselect(
            "Selecciona los IDs de los productos que deseas eliminar:",
            options=df_inventario_actual['ID'].tolist(),
            key='delete_multiselect'
        )

        delete_button = st.button("🔴 Eliminar Productos Seleccionados")

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

# --- REGISTRO DE VENTAS (Mantenido) ---
elif ventana_seleccionada == 'Registro de Ventas':
    df_inventario = st.session_state.df_inventario
    st.title("💸 Registro de Ventas")

    if df_inventario.empty:
        st.info("No hay productos registrados. Por favor, añada productos desde 'Registro de Productos' para registrar ventas.")
    else:
        
        st.header("Registro de Venta Individual")
        st.info("Nota: El historial contiene los registros de la carga inicial automática. El stock negativo está permitido.")
        
        # --- Formulario de Registro Individual ---
        with st.form("registro_venta_form"):
            
            # 1. Selección de Producto
            productos_list = df_inventario['Producto'].tolist()
            selected_product_name = st.selectbox(
                "Selecciona un producto:",
                options=productos_list,
                key="venta_product_select"
            )
            
            producto_data = df_inventario[df_inventario['Producto'] == selected_product_name].iloc[0]
            current_stock = int(producto_data['Stock'])
            presentation = producto_data['Presentación']
            product_id = producto_data['ID']

            st.markdown("---")
            col_left, col_right = st.columns(2)
            
            # 2. Cantidad Vendida (NO tiene restricción de stock máximo)
            with col_left:
                cantidad_vendida = st.number_input(
                    "Cantidad Vendida",
                    min_value=1, 
                    value=1, 
                    step=1,
                    key="cantidad_vendida_input",
                    help="Si la cantidad es mayor al stock actual, el stock se volverá negativo."
                )
            
            # 3. Mostrar Presentación y Stock Actual
            with col_right:
                st.markdown(f"**Presentación:** `{presentation}`")
                st.markdown(f"**Stock Actual:** `{current_stock}`")

            submit_button = st.form_submit_button("Registrar Venta")

            if submit_button:
                if cantidad_vendida > 0:
                    idx = df_inventario[df_inventario['Producto'] == selected_product_name].index[0]
                    
                    # El código aplica la venta sin verificar stock
                    st.session_state.df_inventario.loc[idx, 'Stock'] -= cantidad_vendida
                    st.session_state.df_inventario.loc[idx, 'Ventas'] += cantidad_vendida

                    new_venta = pd.DataFrame([{'ID': product_id, 'Producto': selected_product_name, 'Cantidad': cantidad_vendida}])
                    # Las ventas (manuales y masivas) se añaden al historial
                    st.session_state.df_ventas_hist = pd.concat([st.session_state.df_ventas_hist, new_venta], ignore_index=True)
                    
                    new_stock = st.session_state.df_inventario.loc[idx, 'Stock']
                    if new_stock < 0:
                        st.warning(f"⚠️ Venta de {cantidad_vendida} unidades registrada. El stock es NEGATIVO: {new_stock}")
                    else:
                         st.success(f"Venta de {cantidad_vendida} unidades registrada. Nuevo stock: {new_stock}")
                    st.rerun() 
                else:
                    st.warning("La cantidad vendida debe ser mayor a cero.")

        st.markdown("---")
        st.subheader("Historial de Ventas")
        # Esta tabla muestra todas las ventas (automáticas y manuales)
        st.dataframe(st.session_state.df_ventas_hist, use_container_width=True)


# --- REGISTRO DE COMPRAS (Mantenido) ---
elif ventana_seleccionada == 'Registro de Compras':
    df_inventario = st.session_state.df_inventario
    st.title("🛒 Registro de Compras (Entradas)")

    if df_inventario.empty:
        st.info("No hay productos registrados. Por favor, añada productos desde 'Registro de Productos' para registrar compras.")
    else:
        with st.form("registro_compra_form"):
            st.header("Registrar una Compra")
            
            # 1. Selección de Producto
            productos_list = df_inventario['Producto'].tolist()
            selected_product_name = st.selectbox(
                "Selecciona un producto:",
                options=productos_list,
                key="compra_product_select"
            )
            
            producto_data = df_inventario[df_inventario['Producto'] == selected_product_name].iloc[0]
            current_stock = int(producto_data['Stock'])
            presentation = producto_data['Presentación']
            product_id = producto_data['ID']

            st.markdown("---")
            col_left, col_right = st.columns(2)
            
            # 2. Cantidad Comprada
            with col_left:
                cantidad_comprada = st.number_input(
                    "Cantidad Comprada",
                    min_value=1, 
                    value=1, 
                    step=1,
                    key="cantidad_comprada_input"
                )
            
            # 3. Mostrar Presentación y Stock Actual
            with col_right:
                st.markdown(f"**Presentación:** `{presentation}`")
                st.markdown(f"**Stock Actual:** `{current_stock}`")

            submit_button = st.form_submit_button("Registrar Compra")

            if submit_button:
                if cantidad_comprada > 0:
                    idx = df_inventario[df_inventario['Producto'] == selected_product_name].index[0]
                    
                    st.session_state.df_inventario.loc[idx, 'Stock'] += cantidad_comprada
                    st.session_state.df_inventario.loc[idx, 'Compras'] += cantidad_comprada

                    new_compra = pd.DataFrame([{'ID': product_id, 'Producto': selected_product_name, 'Cantidad': cantidad_comprada}])
                    st.session_state.df_compras_hist = pd.concat([st.session_state.df_compras_hist, new_compra], ignore_index=True)
                    
                    st.success(f"Compra de {cantidad_comprada} unidades de '{selected_product_name}' registrada con éxito. Nuevo stock: {st.session_state.df_inventario.loc[idx, 'Stock']}")
                    st.rerun() 
                else:
                    st.warning("La cantidad comprada debe ser mayor a cero.")

        st.markdown("---")
        st.subheader("Historial de Compras")
        st.dataframe(st.session_state.df_compras_hist, use_container_width=True)
