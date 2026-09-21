import streamlit as st
import pandas as pd
import math
from fpdf import FPDF
import datetime

st.set_page_config(page_title="Ruido Ambiental 0627", page_icon="🔊", layout="wide")
st.title("🔊 Informe Ruido Ambiental - Res. 0627 de 2006")
st.caption("HD2010 Cirrus - LRAeq Corregido - Múltiples puntos")

# --- CONFIG ---
sector = st.selectbox("Sector Normativo", ["Sector A - Residencial", "Sector B - Comercial", "Sector C - Industrial", "Sector D - Tranquilidad"])
horario = st.selectbox("Horario", ["Diurno (7:01-21:00)", "Nocturno (21:01-7:00)"])
fuente = st.text_input("Fuente evaluada", "Planta trituradora de piedra")
empresa = st.text_input("Empresa / Proyecto", "Proyecto Trituradora")
responsable = st.text_input("Responsable", "Edwin - Medición en campo")

limites = {"Sector A - Residencial": (55, 50), "Sector B - Comercial": (65, 60), "Sector C - Industrial": (75, 75), "Sector D - Tranquilidad": (45, 45)}
lim_d, lim_n = limites[sector]
limite_actual = lim_d if "Diurno" in horario else lim_n

def leer_laeq(file):
    if not file: return None
    file.seek(0)
    try:
        df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip')
        if 'LAeq' not in str(df.columns):
            file.seek(0)
            df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip', engine='python')
    except:
        file.seek(0)
        df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip', engine='python')

    col = None
    for c in df.columns:
        if str(c).strip().upper() == 'LAEQ':
            col = c
            break
    if not col: col = df.columns[0]

    vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
    vals = vals[(vals>20)&(vals<140)]
    if len(vals)==0: return None
    laeq = 10*math.log10(sum(10**(v/10) for v in vals)/len(vals))
    return round(laeq,1), len(vals)

st.divider()
st.subheader("Carga de Puntos (hasta 10)")

if 'puntos' not in st.session_state:
    st.session_state.puntos = []

col1, col2, col3 = st.columns(3)
with col1:
    nombre_punto = st.text_input("Nombre Punto", f"Punto {len(st.session_state.puntos)+1}")
with col2:
    lat = st.number_input("Latitud", value=4.60971, format="%.6f")
with col3:
    lon = st.number_input("Longitud", value=-74.08175, format="%.6f")

c1, c2 = st.columns(2)
with c1:
    f_total = st.file_uploader(f"CSV TOTAL - {nombre_punto}", type=["csv"], key=f"t_{len(st.session_state.puntos)}")
with c2:
    f_res = st.file_uploader(f"CSV RESIDUAL - {nombre_punto}", type=["csv"], key=f"r_{len(st.session_state.puntos)}")

if st.button("➕ Agregar Punto") and f_total and f_res:
    lt_data = leer_laeq(f_total)
    lr_data = leer_laeq(f_res)
    if lt_data and lr_data:
        lt, nt = lt_data
        lr, nr = lr_data
        diff = lt - lr
        if lr >= lt:
            lra = lt
            corr = "Fondo >= Total - No corregible"
        elif diff >= 10:
            lra = lt
            corr = f"Diff {diff:.1f} >10dB - No se corrige"
        else:
            lra = round(10*math.log10(10**(lt/10)-10**(lr/10)),1)
            corr = f"Corregido -{lt-lra:.1f} dB"

        cumple = "CUMPLE" if lra <= limite_actual else "NO CUMPLE"
        st.session_state.puntos.append({
            "Punto": nombre_punto, "Lat": lat, "Lon": lon,
            "TOTAL": lt, "RESIDUAL": lr, "LRAeq": lra,
            "Correccion": corr, "Limite": limite_actual, "Cumple": cumple
        })
        st.success(f"Agregado {nombre_punto}: {lra} dB - {cumple}")
    else:
        st.error("No pude leer los CSV - verifica que sean tipo a.csv")

# --- TABLA Y MAPA ---
if st.session_state.puntos:
    st.divider()
    df_puntos = pd.DataFrame(st.session_state.puntos)
    st.dataframe(df_puntos, use_container_width=True)

    st.map(df_puntos.rename(columns={"Lat":"lat","Lon":"lon"}))

    # --- PDF ---
    if st.button("📄 Generar Informe PDF"):
        pdf = FPDF()
        pdf.add_page()
        try:
            pdf.image("logo.png", 10, 8, 33)
        except:
            pass
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"Informe Ruido Ambiental - {empresa}", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 6, f"Fuente: {fuente} | Sector: {sector} | {horario} | Limite: {limite_actual} dB | Fecha: {datetime.date.today()}", ln=True, align='C')
        pdf.cell(0, 6, f"Responsable: {responsable}", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 9)
        cols = ["Punto", "TOTAL", "RESIDUAL", "LRAeq", "Limite", "Cumple"]
        widths = [40, 20, 20, 20, 20, 30]
        for i, c in enumerate(cols):
            pdf.cell(widths[i], 7, c, border=1)
        pdf.ln()
        pdf.set_font("Arial", '', 9)
        for _, row in df_puntos.iterrows():
            pdf.cell(widths[0], 6, str(row["Punto"]), border=1)
            pdf.cell(widths[1], 6, str(row["TOTAL"]), border=1)
            pdf.cell(widths[2], 6, str(row["RESIDUAL"]), border=1)
            pdf.cell(widths[3], 6, str(row["LRAeq"]), border=1)
            pdf.cell(widths[4], 6, str(row["Limite"]), border=1)
            pdf.cell(widths[5], 6, str(row["Cumple"]), border=1)
            pdf.ln()

        pdf.ln(5)
        pdf.set_font("Arial", '', 8)
        pdf.multi_cell(0, 4, "Metodologia: Res. 0627 de 2006 MAVDT. Equipo: Sonometro Cirrus HD2010 Clase 1. Correccion LRAeq = 10*log(10^(LT/10)-10^(LR/10)). Si LR >= LT o Diff >10dB no se corrige.")

        out = pdf.output(dest='S').encode('latin1')
        st.download_button("⬇️ Descargar PDF", data=out, file_name=f"Informe_Ruido_{empresa}.pdf", mime="application/pdf")

    if st.button("🗑️ Borrar todo"):
        st.session_state.puntos = []
        st.rerun()

else:
    st.info("Tu captura que me mandaste ya es el Punto 1: TOTAL 63.3 dB / RESIDUAL 51.5 dB / LRAeq 63.3 dB - CUMPLE. Agrégalo arriba como 'Punto uno' con tus 2 archivos a.csv y f.csv")
