# streamlit_app.py
# Este es el archivo principal de tu aplicación Streamlit.
# Para ejecutarlo, guarda este código como streamlit_app.py e
# ingresa el comando: streamlit run streamlit_app.py en tu terminal.

import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# ==============================================================================
#                      CONFIGURACIÓN DE GOOGLE SHEETS
# ==============================================================================
# Ahora la app lee las credenciales directamente desde st.secrets
# Para usar esto, necesitas un archivo llamado secrets.toml en el mismo
# repositorio de GitHub, con el formato que se te proporcionó.

# ID de tu hoja de cálculo.
SPREADSHEET_ID = '1b_Ud2KcCKmLW3yp3tjrfWLvywieKwp6LclmetIGtsXA'

# ==============================================================================
#                 CONEXIÓN Y LECTURA DE DATOS (Con caché)
# ==============================================================================
@st.cache_resource
def get_google_sheets_client():
    """
    Establece la conexión con Google Sheets y devuelve el cliente y la hoja.
    Usa el decorador de caché para no reconectar en cada interacción.
    """
    try:
        # Usa el método from_service_account_info de gspread con st.secrets
        # para una autenticación segura.
        client = gspread.service_account_from_dict(st.secrets["gspread"])
        st.success("Conexión con Google Sheets exitosa. ¡Listo para trabajar!")
        return client
    except Exception as e:
        st.error(f"Error de autenticación o de hoja de cálculo: {e}")
        st.warning("Por favor, asegúrate de que el archivo secrets.toml está correctamente configurado.")
        return None

client = get_google_sheets_client()

@st.cache_data
def load_data():
    """Carga los datos de la hoja en un DataFrame de Pandas para su uso."""
    if client is None:
        return pd.DataFrame(), []
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        vins = df['VIN'].tolist()
        return df, vins
    except Exception as e:
        st.error(f"Error al cargar los datos de la hoja: {e}")
        return pd.DataFrame(), []

# ==============================================================================
#                      INTERFAZ DE USUARIO (UI) DE STREAMLIT
# ==============================================================================

st.title("Registro de Orden de Servicio")
st.markdown("---")

if client is None:
    st.warning("No se pudo conectar a Google Sheets. Por favor, revisa tus credenciales.")
else:
    df, vins = load_data()

    # Menú principal con un selectbox
    action = st.selectbox(
        "Selecciona una opción:",
        ["Ingresar Camión", "Actualizar Estado"]
    )
    st.markdown("---")

    if action == "Ingresar Camión":
        st.header("Ingresar Nuevo Camión")

        with st.form(key='new_truck_form'):
            # Campos del formulario
            cliente = st.text_input("CLIENTE:").upper()
            fecha_ingreso = st.date_input("FECHA DE INGRESO:")
            
            marcas = ['VOLVO', 'MERCEDES-BENZ', 'KENWORTH', 'FREIGHTLINER', 'PETERBILT', 'INTERNATIONAL', 'MACK', 'SCANIA', 'FORD', 'CHEVROLET', 'DODGE', 'GMC', 'NISSAN', 'HYUNDAI', 'MITSUBISHI', 'TOYOTA', 'ISUZU', 'HINO', 'WESTERN STAR', 'TATRA', 'KAMAZ', 'IVECO', 'MAN', 'DAF']
            marca = st.selectbox("MARCA:", marcas)

            modelo = st.text_input("MODELO:").upper()
            vin = st.text_input("VIN:").upper()
            aplicacion = st.selectbox(
                "APLICACION:",
                ['TRACTOCAMION', 'VOLTEO', 'PLATAFORMA', 'CISTERNA']
            )
            
            submit_button = st.form_submit_button(label='Guardar Nuevo Camión')
            
            if submit_button:
                if not cliente or not fecha_ingreso or not marca or not modelo or not vin or not aplicacion:
                    st.error("Por favor, llena todos los campos obligatorios.")
                elif vin in vins:
                    st.error(f"El VIN '{vin}' ya existe. Por favor, usa la opción de 'Actualizar Estado'.")
                else:
                    try:
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        sheet.append_row([cliente, str(fecha_ingreso), marca, modelo, vin, aplicacion, '', '', ''])
                        st.success("Datos de nuevo camión enviados exitosamente. Ahora puedes actualizar su estado.")
                        st.balloons()
                        load_data.clear()  # Limpia la caché para recargar los datos
                    except Exception as e:
                        st.error(f"Ocurrió un error al guardar los datos: {e}")

    elif action == "Actualizar Estado":
        st.header("Actualizar Estado del Camión")
        vin_search = st.selectbox("VIN:", [''] + vins)

        if vin_search:
            # Buscar el estado actual del VIN
            row_data = df[df['VIN'] == vin_search].iloc[0]
            
            fecha_inicio = row_data.get('FECHA DE INICIO', '')
            fecha_termino = row_data.get('FECHA DE TERMINO', '')
            fecha_entrega = row_data.get('FECHA DE ENTREGA', '')

            if not fecha_inicio:
                st.subheader("Registrar Inicio de Labores")
                fecha_inicio_input = st.date_input("FECHA DE INICIO:")
                if st.button("Guardar Fecha de Inicio"):
                    try:
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        row_index = df[df['VIN'] == vin_search].index[0] + 2 # +2 por el encabezado y el índice 0
                        sheet.update_cell(row_index, 7, str(fecha_inicio_input))
                        st.success(f"Fecha de inicio de labores para VIN {vin_search} actualizada.")
                        load_data.clear() # Limpia la caché
                    except Exception as e:
                        st.error(f"Ocurrió un error al actualizar la fecha: {e}")
            elif not fecha_termino:
                st.subheader("Registrar Término de Labores (Pre-entrega)")
                fecha_termino_input = st.date_input("FECHA DE TERMINO:")
                if st.button("Guardar Fecha de Término"):
                    try:
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        row_index = df[df['VIN'] == vin_search].index[0] + 2
                        sheet.update_cell(row_index, 8, str(fecha_termino_input))
                        st.success(f"Fecha de término para VIN {vin_search} actualizada.")
                        load_data.clear()
                    except Exception as e:
                        st.error(f"Ocurrió un error al actualizar la fecha: {e}")
            elif not fecha_entrega:
                st.subheader("Registrar Entrega a Cliente")
                fecha_entrega_input = st.date_input("FECHA DE ENTREGA:")
                if st.button("Guardar Fecha de Entrega"):
                    try:
                        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
                        row_index = df[df['VIN'] == vin_search].index[0] + 2
                        sheet.update_cell(row_index, 9, str(fecha_entrega_input))
                        st.success(f"Fecha de entrega para VIN {vin_search} actualizada.")
                        load_data.clear()
                    except Exception as e:
                        st.error(f"Ocurrió un error al actualizar la fecha: {e}")
            else:
                st.info(f"El VIN '{vin_search}' ya ha sido entregado al cliente.")


