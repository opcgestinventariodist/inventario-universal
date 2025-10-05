import streamlit as st
import pandas as pd
import plotly.express as px
from unidecode import unidecode 
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Inventario Universal del Llano (Base Precargada)",
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

def to_excel(df):
    """Convierte un DataFrame a un objeto BytesIO para descarga en Excel."""
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Reporte')
    writer.close()
    return output.getvalue()

# --- FUNCIONES DE PROCESAMIENTO MASIVO (USADAS TAMBIÉN PARA CARGA INICIAL) ---

def process_sales_from_df(df_ventas_new):
    """
    Procesa un DataFrame de ventas (carga masiva o inicial).
    IMPORTANTE: Solo procesa IDs que existen en el inventario.
    """
    if st.session_state.df_inventario.empty:
        return 0, [], "El inventario base está vacío."

    df_ventas_new.columns = [clean_col_name(col) for col in df_ventas_new.columns]
    
    # Validación de columnas
    if 'ID' not in df_ventas_new.columns:
        return 0, [], "Columna 'ID' faltante en el archivo."
        
    col_cantidad_vendida = [col for col in df_ventas_new.columns if 'CANTIDAD' in col.upper()]
    if not col_cantidad_vendida:
         return 0, [], "Columna de 'CANTIDAD' faltante. Debe llamarse 'Cantidad' o similar."

    df_ventas_new = df_ventas_new[['ID', col_cantidad_vendida[0]]].rename(columns={col_cantidad_vendida[0]: 'CANTIDAD'})
    df_ventas_new['ID'] = df_ventas_new['ID'].astype(str).str.upper().str.strip()
    df_ventas_new['CANTIDAD'] = pd.to_numeric(df_ventas_new['CANTIDAD'], errors='coerce').fillna(0).astype(int)
    df_ventas_new = df_ventas_new[df_ventas_new['CANTIDAD'] > 0]
    
    # 1. Filtro de ID Válidas (Asegura coherencia)
    valid_ids = st.session_state.df_inventario['ID'].tolist()
    invalid_sales_ids = df_ventas_new[~df_ventas_new['ID'].isin(valid_ids)]['ID'].unique()
    ventas_fallidas = [f"ID {pid}" for pid in invalid_sales_ids]
    df_ventas_valid = df_ventas_new[df_ventas_new['ID'].isin(valid_ids)]
    
    ventas_exitosas = 0
    nuevos_registros_historial = []
    df_inventario_temp = st.session_state.df_inventario.copy()
    
    for index, row in df_ventas_valid.iterrows():
        product_id = row['ID']
        cantidad = row['CANTIDAD']
        
        match = df_inventario_temp[df_inventario_temp['ID'] == product_id]
        
        if not match.empty:
            idx = match.index[0]
            product_name = df_inventario_temp.loc[idx, 'Producto']
            
            # Aplicar la venta
            df_inventario_temp.loc[idx, 'Stock'] -= cantidad
            df_inventario_temp.loc[idx, 'Ventas'] += cantidad
            
            nuevos_registros_historial.append({'ID': product_id, 'Producto': product_name, 'Cantidad': cantidad})
            ventas_exitosas += 1
            
    if ventas_exitosas > 0 or not df_ventas_valid.empty:
        st.session_state.df_inventario = df_inventario_temp
        df_hist_new = pd.DataFrame(nuevos_registros_historial)
        st.session_state.df_ventas_hist = pd.concat([st.session_state.df_ventas_hist, df_hist_new], ignore_index=True)

    return ventas_exitosas, ventas_fallidas, None


def process_purchases_from_df(df_compras_new):
    """
    Procesa un DataFrame de compras (carga masiva o inicial).
    IMPORTANTE: Solo procesa IDs que existen en el inventario.
    """
    if st.session_state.df_inventario.empty:
        return 0, [], "El inventario base está vacío."
        
    df_compras_new.columns = [clean_col_name(col) for col in df_compras_new.columns]

    # Validación de columnas
    if 'ID' not in df_compras_new.columns:
        return 0, [], "Columna 'ID' faltante en el archivo."
        
    col_cantidad_comprada = [col for col in df_compras_new.columns if 'CANTIDAD' in col.upper()]
    if not col_cantidad_comprada:
         return 0, [], "Columna de 'CANTIDAD' faltante. Debe llamarse 'Cantidad' o similar."

    df_compras_new = df_compras_new[['ID', col_cantidad_comprada[0]]].rename(columns={col_cantidad_comprada[0]: 'CANTIDAD'})
    df_compras_new['ID'] = df_compras_new['ID'].astype(str).str.upper().str.strip()
    df_compras_new['CANTIDAD'] = pd.to_numeric(df_compras_new['CANTIDAD'], errors='coerce').fillna(0).astype(int)
    df_compras_new = df_compras_new[df_compras_new['CANTIDAD'] > 0]
    
    # 1. Filtro de ID Válidas (Asegura coherencia)
    valid_ids = st.session_state.df_inventario['ID'].tolist()
    invalid_purchase_ids = df_compras_new[~df_compras_new['ID'].isin(valid_ids)]['ID'].unique()
    compras_fallidas = [f"ID {pid}" for pid in invalid_purchase_ids]
    df_compras_valid = df_compras_new[df_compras_new['ID'].isin(valid_ids)]

    compras_exitosas = 0
    nuevos_registros_historial = []
    df_inventario_temp = st.session_state.df_inventario.copy()
    
    for index, row in df_compras_valid.iterrows():
        product_id = row['ID']
        cantidad = row['CANTIDAD']
        
        match = df_inventario_temp[df_inventario_temp['ID'] == product_id]
        
        if not match.empty:
            idx = match.index[0]
            product_name = df_inventario_temp.loc[idx, 'Producto']
            
            # Aplicar la compra
            df_inventario_temp.loc[idx, 'Stock'] += cantidad
            df_inventario_temp.loc[idx, 'Compras'] += cantidad

            nuevos_registros_historial.append({'ID': product_id, 'Producto': product_name, 'Cantidad': cantidad})
            compras_exitosas += 1
            
    if compras_exitosas > 0 or not df_compras_valid.empty:
        st.session_state.df_inventario = df_inventario_temp
        df_hist_new = pd.DataFrame(nuevos_registros_historial)
        st.session_state.df_compras_hist = pd.concat([st.session_state.df_compras_hist, df_hist_new], ignore_index=True)

    return compras_exitosas, compras_fallidas, None


# --- INICIALIZACIÓN DE DATOS ---

# Inventario principal
if 'df_inventario' not in st.session_state:
    columnas = ['ID', 'Producto', 'Stock', 'Categoría', 'Presentación', 'Ventas', 'Compras']
    df_inventario_vacio = pd.DataFrame(columns=columnas)
    
    # === 1. LÓGICA DE CARGA AUTOMÁTICA DEL INVENTARIO INICIAL ===
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
            'Ventas': 0, 
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
    
# Umbral de bajo stock por defecto (configurable)
if 'low_stock_threshold' not in st.session_state:
    st.session_state.low_stock_threshold = 10 

# Bandera de control para evitar la doble carga de movimientos
if 'initial_movements_loaded' not in st.session_state:
    st.session_state.initial_movements_loaded = False 
    

# === 2. LÓGICA DE CARGA AUTOMÁTICA DE MOVIMIENTOS (Solo se ejecuta UNA VEZ) ===
if not st.session_state.initial_movements_loaded and not st.session_state.df_inventario.empty:
    
    # --- A. Carga de VENTAS ---
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
            st.warning(f"⚠️ {len(ventas_fallidas)} ventas de '{VENTAS_FILE_PATH}' **FALLARON** porque el producto no existe en el inventario. ID no procesadas: {', '.join(ventas_fallidas)}")
            
    except FileNotFoundError:
        pass
    except Exception as e:
        st.warning(f"No se pudo leer el archivo '{VENTAS_FILE_PATH}'. Asegúrese de que el formato (ID, Cantidad) sea correcto. Error: {e}")


    # --- B. Carga de COMPRAS ---
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
             st.warning(f"⚠️ {len(compras_fallidas)} compras de '{COMPRAS_FILE_PATH}' **FALLARON** porque el producto no existe en el inventario. ID no procesadas: {', '.join(compras_fallidas)}")
            
    except FileNotFoundError:
        pass 
    except Exception as e:
        st.warning(f"No se pudo leer el archivo '{COMPRAS_FILE_PATH}'. Asegúrese de que el formato (ID, Cantidad) sea correcto. Error: {e}")

    # Establecer la bandera en True para que no se vuelva a ejecutar
    st.session_state.initial_movements_loaded = True 


# --- NAVEGACIÓN EN EL SIDEBAR ---
st.sidebar.header("Menú de Navegación")
ventana_seleccionada = st.sidebar.radio( 
    "Selecciona una ventana:",
    ('Dashboard', 'Registro de Productos', 'Registro de Ventas', 'Registro de Compras', 'Carga de Movimientos', 'Reportes y Descarga', 'Configuración')
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

# ----------------------------------------------------
# 1. DASHBOARD
# ----------------------------------------------------
if ventana_seleccionada == 'Dashboard':
    df_inventario = st.session_state.df_inventario
    threshold = st.session_state.low_stock_threshold
    
    st.title("📦 Control de Inventario - Distribuidora Universal del Llano")
    st.header("📊 Dashboard de Inventario")

    if df_inventario.empty:
        st.info("No hay productos en el inventario. Añada productos desde 'Registro de Productos'.")
    else:
        # Cálculo de KPIs
        total_productos_unicos = df_inventario['Producto'].nunique()
        total_unidades_stock = df_inventario['Stock'].astype(int).sum()
        productos_bajo_stock = df_inventario[df_inventario['Stock'].astype(int) <= threshold].shape[0]

        # Mostrar KPIs
        st.subheader("Indicadores Clave (KPIs)")
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Total de Productos Únicos", f"{total_productos_unicos}")
        with col2: st.metric("Total de Unidades en Stock", f"{total_unidades_stock}")
        with col3: st.metric(f"Productos con Bajo Stock (<= {threshold})", f"{productos_bajo_stock}", delta_color="inverse")

        st.markdown("---") 
        
        # Alerta de Bajo Stock 
        st.subheader("🚨 Productos con Bajo Stock")
        df_bajo_stock = df_inventario[df_inventario['Stock'].astype(int) <= threshold].sort_values(by='Stock', ascending=True)
        if df_bajo_stock.empty:
            st.success("¡Todo el inventario está por encima del umbral de bajo stock!")
        else:
            st.dataframe(
                df_bajo_stock[['ID', 'Producto', 'Stock', 'Categoría']], 
                use_container_width=True,
                hide_index=True
            )
            
        st.markdown("---") 
        st.subheader("Visualizaciones y Movimientos")
        viz_col1, viz_col2 = st.columns(2)

        # Gráfico 1: Niveles de Stock por Producto
        with viz_col1:
            st.markdown("##### Niveles de Stock por Producto")
            df_stock_sorted = df_inventario.sort_values(by='Stock', ascending=False).head(10)
            fig_stock = px.bar(df_stock_sorted, x='Producto', y='Stock', text='Stock', 
                               title="Top 10 Productos por Stock", color='Producto', height=350)
            st.plotly_chart(fig_stock, use_container_width=True)

        # Gráfico 2: Distribución de Productos por Categoría 
        with viz_col2:
            st.markdown("##### Distribución de Productos por Categoría")
            df_categoria = df_inventario.groupby('Categoría').size().reset_index(name='Count')
            fig_categoria = px.pie(df_categoria, names='Categoría', values='Count', 
                                   title='Productos por Categoría', height=350)
            st.plotly_chart(fig_categoria, use_container_width=True)

        st.markdown("---") 
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

# ----------------------------------------------------
# 2. REGISTRO DE PRODUCTOS
# ----------------------------------------------------
elif ventana_seleccionada == 'Registro de Productos':
    df_inventario = st.session_state.df_inventario
    st.title("➕ Registro de Productos")
    st.header("Registro Manual de Productos")

    # --- 1. FORMULARIO DE INGRESO MANUAL ---
    with st.form("registro_producto_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            id_producto = st.text_input("Identificador del Producto (ID)", key="id_manual_input")
            nombre_producto = st.text_input("Nombre del Producto", key="name_manual_input")
        
        with col_right:
            categoria = st.selectbox("Categoría", options=CATEGORIA_OPCIONES, key="category_manual_input")
            presentacion = st.selectbox("Presentación", options=PRESENTACION_OPCIONES, key="presentation_manual_input")

        stock_inicial = st.number_input("Stock Inicial", value=0, step=1, min_value=0, key="stock_manual_input")

        submit_button = st.form_submit_button("Añadir Producto Manualmente")
        
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

# ----------------------------------------------------
# 3. REGISTRO DE VENTAS
# ----------------------------------------------------
elif ventana_seleccionada == 'Registro de Ventas':
    df_inventario = st.session_state.df_inventario
    st.title("💸 Registro de Ventas")

    if df_inventario.empty:
        st.info("No hay productos registrados. Añada productos para registrar ventas.")
    else:
        st.header("Registro de Venta Individual")
        
        with st.form("registro_venta_form"):
            
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
            
            with col_left:
                cantidad_vendida = st.number_input(
                    "Cantidad Vendida",
                    min_value=1, 
                    value=1, 
                    step=1,
                    key="cantidad_vendida_input",
                    help="Si la cantidad es mayor al stock actual, el stock se volverá negativo."
                )
            
            with col_right:
                st.markdown(f"**Presentación:** `{presentation}`")
                st.markdown(f"**Stock Actual:** `{current_stock}`")

            submit_button = st.form_submit_button("Registrar Venta")

            if submit_button:
                if cantidad_vendida > 0:
                    idx = df_inventario[df_inventario['Producto'] == selected_product_name].index[0]
                    
                    st.session_state.df_inventario.loc[idx, 'Stock'] -= cantidad_vendida
                    st.session_state.df_inventario.loc[idx, 'Ventas'] += cantidad_vendida

                    new_venta = pd.DataFrame([{'ID': product_id, 'Producto': selected_product_name, 'Cantidad': cantidad_vendida}])
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
        st.dataframe(st.session_state.df_ventas_hist, use_container_width=True)

# ----------------------------------------------------
# 4. REGISTRO DE COMPRAS
# ----------------------------------------------------
elif ventana_seleccionada == 'Registro de Compras':
    df_inventario = st.session_state.df_inventario
    st.title("🛒 Registro de Compras (Entradas)")

    if df_inventario.empty:
        st.info("No hay productos registrados. Añada productos para registrar compras.")
    else:
        with st.form("registro_compra_form"):
            st.header("Registrar una Compra")
            
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
            
            with col_left:
                cantidad_comprada = st.number_input(
                    "Cantidad Comprada",
                    min_value=1, 
                    value=1, 
                    step=1,
                    key="cantidad_comprada_input"
                )
            
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

# ----------------------------------------------------
# 5. CARGA DE MOVIMIENTOS (MASIVA)
# ----------------------------------------------------
elif ventana_seleccionada == 'Carga de Movimientos':
    st.title("⬆️ Carga Masiva de Movimientos")
    st.header("Sube tus archivos de Excel (Ventas o Compras)")

    if st.session_state.df_inventario.empty:
        st.warning("No puedes cargar movimientos masivos si el inventario está vacío. Por favor, registra productos primero.")
    else:
        st.markdown("""
            **Requisitos del Archivo:**
            - Debe ser un archivo **.xlsx** o **.csv**.
            - Debe contener una columna con el **ID** del producto (ej: 'ID', 'ID Producto').
            - Debe contener una columna con la **Cantidad** del movimiento (ej: 'Cantidad', 'Cantidad Vendida', 'Cantidad Comprada').
        """)

        uploaded_file = st.file_uploader("Sube el archivo de Ventas o Compras", type=['xlsx', 'csv'])

        if uploaded_file is not None:
            # 1. Leer el archivo
            try:
                if uploaded_file.name.endswith('.csv'):
                    df_upload = pd.read_csv(uploaded_file)
                else:
                    df_upload = pd.read_excel(uploaded_file)
                
                st.success(f"Archivo '{uploaded_file.name}' cargado exitosamente.")
                
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")
                df_upload = None

            if df_upload is not None:
                st.subheader("Vista Previa del Archivo Cargado")
                st.dataframe(df_upload.head())
                
                # 2. Selección del Tipo de Movimiento
                tipo_movimiento = st.radio(
                    "Selecciona el tipo de movimiento en este archivo:",
                    ('Ventas', 'Compras'),
                    key='movimiento_type_select'
                )
                
                process_button = st.button(f"⚙️ Procesar Carga de {tipo_movimiento}")

                if process_button:
                    with st.spinner(f"Procesando {tipo_movimiento} en el inventario..."):
                        if tipo_movimiento == 'Ventas':
                            exitosas, fallidas, error = process_sales_from_df(df_upload)
                        else: # Compras
                            exitosas, fallidas, error = process_purchases_from_df(df_upload)

                        if error:
                            st.error(f"Error Crítico: {error}")
                        else:
                            st.success(f"¡Procesamiento completado! Se registraron **{exitosas}** movimientos exitosos.")
                            if fallidas:
                                st.warning(f"⚠️ **{len(fallidas)}** movimientos fallaron. La ID de los siguientes productos no fue encontrada: {', '.join(fallidas)}")
                            st.balloons()
                            st.rerun()
# ----------------------------------------------------
# 6. REPORTES Y DESCARGA 
# ----------------------------------------------------
elif ventana_seleccionada == 'Reportes y Descarga':
    st.title("⬇️ Reportes y Descarga de Datos")
    st.header("Genera y Descarga tus Archivos")

    df_inventario = st.session_state.df_inventario
    df_ventas_hist = st.session_state.df_ventas_hist
    df_compras_hist = st.session_state.df_compras_hist
    
    col_inv, col_ventas, col_compras = st.columns(3)

    # Reporte de Inventario Actual
    with col_inv:
        st.subheader("Inventario Actual")
        st.info(f"Productos únicos: {df_inventario.shape[0]}")
        if not df_inventario.empty:
            excel_data = to_excel(df_inventario)
            st.download_button(
                label="Descargar Inventario Actual (Excel)",
                data=excel_data,
                file_name="inventario_actual.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # Reporte de Historial de Ventas
    with col_ventas:
        st.subheader("Historial de Ventas")
        st.info(f"Total de Ventas: {df_ventas_hist.shape[0]} registros")
        if not df_ventas_hist.
