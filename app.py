import streamlit as st
import pandas as pd
import math, datetime, io, zipfile
from fpdf import FPDF
from PIL import Image

st.set_page_config(page_title="Ruido Pro - Carpeta Completa", page_icon="📁", layout="wide")
st.title("📁 Sistema Completo Ruido Ambiental Res. 0627")
st.caption("Fotos + Meteo + Coordenadas + Carpeta Final - FIXED")

# --- PROYECTO ---
with st.sidebar:
    st.header("📋 Datos Proyecto")
    empresa = st.text_input("Empresa", "Cantera La Esmeralda")
    proyecto = st.text_input("Proyecto", "Trituradora Primaria")
    responsable = st.text_input("Responsable", "Edwin")
    fecha_med = st.date_input("Fecha medición", datetime.date.today())
    sector = st.selectbox("Sector", ["Sector C - Industrial","Sector A - Residencial","Sector B - Comercial","Sector D - Tranquilidad"])
    horario = st.selectbox("Horario", ["Diurno","Nocturno"])
    limite = 75 if "Industrial" in sector else 65
    st.metric("Límite", f"{limite} dB")

def leer_laeq(file):
    if not file: return None
    file.seek(0)
    try:
        df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip', engine='python')
    except Exception as e:
        st.error(f"Error leyendo CSV: {e}")
        return None
    col = next((c for c in df.columns if 'LAEQ' in str(c).upper()), None)
    if not col:
        col = df.columns[1] if len(df.columns)>1 else df.columns[0]
    vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
    vals = vals[(vals>20)&(vals<140)]
    if len(vals)==0: return None
    laeq = 10*math.log10(sum(10**(v/10) for v in vals)/len(vals))
    return round(laeq,1), len(vals), df

if 'puntos' not in st.session_state:
    st.session_state.puntos = []

st.subheader("➕ Agregar Nuevo Punto de Medición")

with st.form("form_punto", clear_on_submit=True):
    c1,c2,c3 = st.columns(3)
    nombre = c1.text_input("Nombre Punto", f"Punto {len(st.session_state.puntos)+1}")
    lat = c2.number_input("Latitud", value=4.609710, format="%.6f")
    lon = c3.number_input("Longitud", value=-74.081750, format="%.6f")

    st.write("**📸 Fotos del punto (hasta 3)**")
    cf1, cf2, cf3 = st.columns(3)
    foto1 = cf1.file_uploader("Foto 1 - Vista general", type=["jpg","jpeg","png"], key=f"f1_{len(st.session_state.puntos)}")
    foto2 = cf2.file_uploader("Foto 2 - Sonómetro", type=["jpg","jpeg","png"], key=f"f2_{len(st.session_state.puntos)}")
    foto3 = cf3.file_uploader("Foto 3 - Fuente", type=["jpg","jpeg","png"], key=f"f3_{len(st.session_state.puntos)}")

    st.write("**🌦️ Datos Meteorológicos**")
    cm1,cm2,cm3,cm4 = st.columns(4)
    temp = cm1.number_input("Temp °C", value=18.5)
    hum = cm2.number_input("Humedad %", value=65.0)
    viento_vel = cm3.number_input("Viento m/s", value=1.2)
    viento_dir = cm4.selectbox("Dir Viento", ["N","NE","E","SE","S","SW","W","NW"])
    presion = st.number_input("Presión hPa", value=1012.0)
    cielo = st.selectbox("Cielo", ["Despejado","Parcial nublado","Nublado","Lluvia ligera"])

    st.write("**🔊 Datos Acústicos**")
    ca1,ca2 = st.columns(2)
    file_total = ca1.file_uploader("CSV TOTAL (a.csv prendida)", type=["csv"])
    file_res = ca2.file_uploader("CSV RESIDUAL (a.csv apagada)", type=["csv"])
    obs = st.text_area("Observaciones", "Fuente: trituradora en operación normal. Suelo: afirmado.")

    submitted = st.form_submit_button("💾 Guardar Punto")

    if submitted:
        if not file_total or not file_res:
            st.warning("Debes subir los 2 CSV tipo a.csv")
        else:
            lt_data = leer_laeq(file_total)
            lr_data = leer_laeq(file_res)
            if lt_data and lr_data:
                lt, nt, _ = lt_data
                lr, nr, _ = lr_data
                diff = lt - lr
                if lr >= lt:
                    lra = lt
                    corr = "No corregible"
                elif diff >= 10:
                    lra = lt
                    corr = f"Diff {diff:.1f}>10 - No corrige"
                else:
                    lra = round(10*math.log10(10**(lt/10)-10**(lr/10)),1)
                    corr = f"Corregido"
                cumple = "CUMPLE" if lra <= limite else "NO CUMPLE"

                punto = {
                    "nombre": nombre, "lat": lat, "lon": lon,
                    "fotos": [f for f in [foto1,foto2,foto3] if f],
                    "temp": temp, "hum": hum, "viento_vel": viento_vel, "viento_dir": viento_dir,
                    "presion": presion, "cielo": cielo,
                    "total": lt, "residual": lr, "lra": lra, "diff": diff, "corr": corr, "cumple": cumple,
                    "obs": obs, "file_total": file_total, "file_res": file_res,
                    "fecha": str(fecha_med)
                }
                st.session_state.puntos.append(punto)
                st.success(f"{nombre} guardado: {lra} dB - {cumple}")
                st.rerun()
            else:
                st.error("Error leyendo CSV - usa solo tipo a.csv (Section1 Date;LAeq)")

# --- MOSTRAR PUNTOS ---
if st.session_state.puntos:
    st.divider()
    df_show = pd.DataFrame([{"Punto":p["nombre"],"TOTAL":p["total"],"RESIDUAL":p["residual"],"LRAeq":p["lra"],"Cumple":p["cumple"],"Lat":p["lat"],"Lon":p["lon"],"Temp":p["temp"],"Viento":f"{p['viento_vel']} {p['viento_dir']}"} for p in st.session_state.puntos])
    st.dataframe(df_show, use_container_width=True)
    st.map(df_show.rename(columns={"Lat":"lat","Lon":"lon"}))

    # --- GENERAR CARPETA ZIP ---
    st.divider()
    st.subheader("📦 Generar Carpeta Final del Proyecto")

    if st.button("🚀 GENERAR CARPETA.ZIP COMPLETA"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:

            # 1. Excel Resumen
            output_excel = io.BytesIO()
            df_show.to_excel(output_excel, index=False)
            zf.writestr(f"{proyecto}/05_Resumen_Excel/Resumen_Puntos.xlsx", output_excel.getvalue())

            # 2. Fotos
            for p in st.session_state.puntos:
                for i, foto in enumerate(p["fotos"]):
                    try:
                        foto.seek(0)
                        zf.writestr(f"{proyecto}/04_Fotos_Puntos/{p['nombre']}_Foto{i+1}.jpg", foto.read())
                    except:
                        pass

            # 3. CSVs crudos
            for p in st.session_state.puntos:
                try:
                    p["file_total"].seek(0)
                    zf.writestr(f"{proyecto}/03_Datos_Crudos_CSV/{p['nombre']}_TOTAL.csv", p["file_total"].read())
                    p["file_res"].seek(0)
                    zf.writestr(f"{proyecto}/03_Datos_Crudos_CSV/{p['nombre']}_RESIDUAL.csv", p["file_res"].read())
                except:
                    pass

            # 4. PDF Final - CORREGIDO
            pdf = FPDF()
            pdf.add_page()
            try:
                if os.path.exists("logo.png"):
                    pdf.image("logo.png", 10, 8, 35)
            except:
                pass
            pdf.set_font("Arial",'B',14)
            pdf.cell(0,10,f"Informe Ruido Ambiental - {proyecto}",ln=True,align='C')
            pdf.set_font("Arial",'',9)
            pdf.cell(0,5,f"Empresa: {empresa} | Fecha: {fecha_med} | Sector: {sector} | {horario} | Limite {limite} dB | Resp: {responsable}",ln=True,align='C')
            pdf.ln(8)

            for p in st.session_state.puntos:
                pdf.set_font("Arial",'B',11)
                pdf.set_fill_color(240,240,240)
                pdf.cell(0,7,f" {p['nombre']} - {p['lra']} dB - {p['cumple']}",ln=True,fill=True)
                pdf.set_font("Arial",'',8)
                # Evitar caracteres especiales que rompen latin1
                obs_clean = p['obs'].encode('latin1','ignore').decode('latin1')
                pdf.cell(0,4,f"Coord: {p['lat']}, {p['lon']} | TOTAL {p['total']} dB | RESIDUAL {p['residual']} dB | {p['corr']} | Meteo: {p['temp']}C, {p['hum']}%, Viento {p['viento_vel']}m/s {p['viento_dir']}, {p['cielo']}, {p['presion']}hPa",ln=True)
                pdf.cell(0,4,f"Obs: {obs_clean}",ln=True)
                pdf.ln(2)

            # FIX DEFINITIVO PDF
            pdf_out = pdf.output(dest='S')
            if isinstance(pdf_out, str):
                pdf_bytes = pdf_out.encode('latin1', 'ignore')
            else:
                pdf_bytes = bytes(pdf_out)

            zf.writestr(f"{proyecto}/01_Informe_PDF/Informe_Final_{proyecto}.pdf", pdf_bytes)
            zf.writestr(f"{proyecto}/Informe_Final.pdf", pdf_bytes)

        zip_buffer.seek(0)
        st.download_button("⬇️ DESCARGAR CARPETA COMPLETA.ZIP", data=zip_buffer, file_name=f"{proyecto}_{fecha_med}.zip", mime="application/zip")
        st.balloons()
        st.success("¡Carpeta generada! Ya tienes todo organizado para entregar.")

    if st.button("🗑️ Borrar todos los puntos"):
        st.session_state.puntos = []
        st.rerun()
else:
    st.info("Agrega tu primer punto arriba. Usa los CSV tipo a.csv que ya te funcionaron (63.3 dB y 51.5 dB)")
