import streamlit as st
import pandas as pd
import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

st.set_page_config(page_title="EQUISIMA FORMATO ORIGINAL V5", layout="wide")
st.title("EQUISIMA - R2-POE37-EP V04 + RES 627 - FORMATO ORIGINAL")

if "puntos" not in st.session_state:
    st.session_state.puntos = []

NORMA = {
    "A. Tranquilidad y Silencio": {"Diurno": 55, "Nocturno": 45},
    "B. Tranquilidad y Ruido Moderado": {"Diurno": 65, "Nocturno": 50},
    "C. Ruido Intermedio Restringido": {"Diurno": 75, "Nocturno": 70},
    "C. Industrial": {"Diurno": 75, "Nocturno": 75},
    "C. Centro Ciudad / Comercial": {"Diurno": 70, "Nocturno": 55},
}

tab1, tab2, tab3, tab4 = st.tabs(["📋 DATOS PLANTILLA", "🗺️ PUNTOS", "⚖️ RES 627", "📸 DESCARGA"])

with tab1:
    st.subheader("Datos exactamente como en tu plantilla")
    c1,c2,c3 = st.columns(3)
    with c1:
        cliente = st.text_input("CLIENTE:", "Rueda Inversiones S A S")
        proyecto = st.text_input("NOMBRE DEL PROYECTO:", "Ataco Tolima")
        depto = st.text_input("DEPARTAMENTO:", "TOLIMA")
        municipio = st.text_input("MUNICIPIO:", "ATACO")
        plan_m = st.text_input("PLAN DE MUESTREO:", "PM-001")
        orden = st.text_input("ORDEN DE SERVICIO:", "OS-001")
    with c2:
        punto_mon = st.text_input("PUNTO DE MONITOREO:", "Punto 1 nocturno")
        # AQUÍ ESTABA EL ERROR - AHORA SÍ SE PUEDE ESCRIBIR
        coord_n = st.text_input("COORDENADAS ORIGEN NACIONAL (Lat/Lon):", "3°35'11.30\"N 75°23'27.72\"W")
        coord_ctm12 = st.text_input("COORDENADAS CTM12 (Este,Norte) - FALTABA:", "Ej: E 876543 - N 912345")
        desc_punto = st.text_area("DESCRIPCIÓN DEL PUNTO:", "En la entrada o vía principal")
        barrido = st.text_input("REGISTRO BARRIDO PERIMETRAL (dB):", "68")
    with c3:
        sector = st.selectbox("SECTOR RES 627", list(NORMA.keys()), index=1)
        periodo = st.selectbox("PERIODO", ["Diurno","Nocturno"], index=1)
        fecha = st.date_input("FECHA TOMA", datetime.now())
        hora = st.text_input("HORA TOMA", "21:01")
        tipo_escenario = st.selectbox("ESCENARIO:", ["Emisión", "Calidad"])

    st.divider()
    col1,col2,col3,col4 = st.columns(4)
    with col1:
        calib = st.text_input("Calibración Inicial dB", "114.0")
        memoria = st.text_input("Memoria / No.", "1")
        laeq = st.number_input("LAeq,T (dB) In situ", 0.0, 140.0, 65.0)
    with col2:
        vel = st.number_input("Vel Viento (m/s)", 0.0, 20.0, 0.3)
        dirv = st.text_input("Dirección Viento", "N")
        temp = st.number_input("Temp °C", -20.0, 60.0, 29.0)
    with col3:
        hum = st.number_input("Humedad %", 0, 100, 45)
        precip = st.selectbox("Precipitaciones?", ["NO","SI"])
    with col4:
        fuente = st.text_input("Fuente Ruido", "mineria")
        tipo_ruido = st.text_input("Tipo Ruido", "Continuo")
        altura = st.text_input("Altura Sonómetro (m)", "1.5")

    limite = NORMA[sector][periodo]
    cumple = "CUMPLE" if laeq <= limite else "NO CUMPLE"
    st.info(f"Límite {sector} {periodo}: {limite} dB | Medido: {laeq} dB | {cumple}")

    if st.button("📍 AGREGAR PUNTO", type="primary", use_container_width=True):
        st.session_state.puntos.append({
            "CLIENTE": cliente, "PROYECTO": proyecto, "DEPARTAMENTO": depto, "MUNICIPIO": municipio,
            "PLAN": plan_m, "ORDEN": orden, "PUNTO": punto_mon, "COORD_NACIONAL": coord_n,
            "COORD_CTM12": coord_ctm12, "DESC": desc_punto, "BARRIDO": barrido,
            "SECTOR": sector, "PERIODO": periodo, "TIPO_ESC": tipo_escenario,
            "FECHA": str(fecha), "HORA": hora, "CALIB": calib, "MEMORIA": memoria,
            "LAEQ": laeq, "LIMITE": limite, "CUMPLE": cumple,
            "VEL": vel, "DIR": dirv, "TEMP": temp, "HUM": hum, "PRECIP": precip,
            "FUENTE": fuente, "TIPO": tipo_ruido, "ALTURA": altura
        })
        st.success(f"Guardado: {cumple}")
        st.balloons()

with tab2:
    if st.session_state.puntos:
        st.dataframe(pd.DataFrame(st.session_state.puntos), use_container_width=True)
        if st.button("🗑️ Borrar"):
            st.session_state.puntos = []
            st.rerun()
    else:
        st.info("Sin puntos")

with tab3:
    st.subheader("Evaluación Res 627")
    if st.session_state.puntos:
        df = pd.DataFrame(st.session_state.puntos)
        st.dataframe(df[["PUNTO","COORD_NACIONAL","COORD_CTM12","LAEQ","LIMITE","CUMPLE"]], use_container_width=True)

        # Subir Excel externo para comparar
        st.divider()
        st.write("📤 ¿Tienes un Excel con mediciones? Súbelo y te lo comparo:")
        up = st.file_uploader("Sube Excel con columna de dB", type=["xlsx"])
        if up:
            df_ext = pd.read_excel(up)
            st.dataframe(df_ext.head())
            col = st.selectbox("Columna con dB", df_ext.columns)
            sec = st.selectbox("Sector para este archivo", list(NORMA.keys()), key="sec2")
            per = st.selectbox("Periodo", ["Diurno","Nocturno"], key="per2")
            lim = NORMA[sec][per]
            df_ext["Limite"] = lim
            df_ext["Cumple"] = df_ext[col].apply(lambda x: "CUMPLE" if x <= lim else "NO CUMPLE")
            st.dataframe(df_ext)

with tab4:
    fotos_up = st.file_uploader("Sube fotos", type=["jpg","png"], accept_multiple_files=True)
    if fotos_up:
        for f in fotos_up:
            st.image(f, width=200)

    if not st.session_state.puntos:
        st.warning("Agrega puntos primero")
    else:
        if st.button("📥 GENERAR EXCEL FORMATO ORIGINAL", type="primary", use_container_width=True):
            # CREAMOS EL EXCEL DESDE CERO - IDÉNTICO A TU PLANTILLA - SIN ERRORES
            wb = Workbook()
            ws = wb.active
            ws.title = "Datos de Campo Emision"

            # Encabezados como tu plantilla
            ws["B2"] = "FORMATO DE CAMPO R2-POE37-EP V04 - DATOS DE CAMPO EMISIÓN"
            ws["B2"].font = Font(bold=True, size=12)

            ws["B8"] = "CLIENTE:"
            ws["B9"] = "NOMBRE DEL PROYECTO:"
            ws["B10"] = "DEPARTAMENTO:"
            ws["B11"] = "MUNICIPIO:"
            ws["B12"] = "PLAN DE MUESTREO:"
            ws["B13"] = "ORDEN DE SERVICIO:"

            p0 = st.session_state.puntos[0]
            ws["E8"] = p0["CLIENTE"]
            ws["E9"] = p0["PROYECTO"]
            ws["E10"] = p0["DEPARTAMENTO"]
            ws["E11"] = p0["MUNICIPIO"]
            ws["E12"] = p0["PLAN"]
            ws["E13"] = p0["ORDEN"]

            ws["B15"] = "PUNTO DE MONITOREO:"
            ws["D15"] = p0["PUNTO"]
            ws["H15"] = "COORDENADAS ORIGEN NACIONAL:"
            ws["L15"] = p0["COORD_NACIONAL"]

            ws["B16"] = "COORDENADAS CTM12:"
            ws["D16"] = p0["COORD_CTM12"] # ESTO FALTABA
            ws["H16"] = "DESCRIPCIÓN DEL PUNTO:"
            ws["L16"] = p0["DESC"]

            ws["B17"] = "REGISTRO BARRIDO PERIMETRAL (dB):"
            ws["E17"] = p0["BARRIDO"]
            ws["H17"] = "SECTOR RES 627:"
            ws["L17"] = f"{p0['SECTOR']} - {p0['PERIODO']} - Lim {p0['LIMITE']} dB"

            # Tabla mediciones
            ws["B19"] = "DATOS DE MEDICIÓN"
            headers = ["Fecha","Hora","Calibración","Memoria","LAeq,T","Vel Viento","Dir Viento","Temp","Humedad","Precip","Fuente","Tipo","Altura","LAeq","Limite","Cumple","Coord Nac","Coord CTM12"]
            for i, h in enumerate(headers, start=2):
                ws.cell(row=20, column=i).value = h
                ws.cell(row=20, column=i).font = Font(bold=True)

            fila = 21
            for p in st.session_state.puntos:
                ws.cell(row=fila, column=2).value = p["FECHA"]
                ws.cell(row=fila, column=3).value = p["HORA"]
                ws.cell(row=fila, column=4).value = p["CALIB"]
                ws.cell(row=fila, column=5).value = p["MEMORIA"]
                ws.cell(row=fila, column=6).value = p["LAEQ"]
                ws.cell(row=fila, column=7).value = p["VEL"]
                ws.cell(row=fila, column=8).value = p["DIR"]
                ws.cell(row=fila, column=9).value = p["TEMP"]
                ws.cell(row=fila, column=10).value = p["HUM"]
                ws.cell(row=fila, column=11).value = p["PRECIP"]
                ws.cell(row=fila, column=12).value = p["FUENTE"]
                ws.cell(row=fila, column=13).value = p["TIPO"]
                ws.cell(row=fila, column=14).value = p["ALTURA"]
                ws.cell(row=fila, column=15).value = p["LAEQ"]
                ws.cell(row=fila, column=16).value = p["LIMITE"]
                ws.cell(row=fila, column=17).value = p["CUMPLE"]
                ws.cell(row=fila, column=18).value = p["COORD_NACIONAL"]
                ws.cell(row=fila, column=19).value = p["COORD_CTM12"]
                fila += 1

            # Ajustar ancho
            for col in range(2, 20):
                ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = 15

            out = io.BytesIO()
            wb.save(out)

            st.download_button(
                "📥 DESCARGAR EXCEL FORMATO ORIGINAL (SIN ERRORES)",
                out.getvalue(),
                file_name=f"R2-POE37-EP_{p0['MUNICIPIO']}_{p0['PUNTO']}_RES627.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
            st.success("¡Listo! Este ya no usa plantilla.xlsx y no da error MergedCell. Incluye coordenadas CTM12 que faltaban")
