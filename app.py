import streamlit as st
import pandas as pd
import math, datetime, io, zipfile, os
import matplotlib.pyplot as plt
from fpdf import FPDF

st.set_page_config(page_title="Ruido Final", layout="wide")
st.title("📁 App Ruido - Fotos + Meteo + Informe Final")

with st.sidebar:
    empresa = st.text_input("Empresa", "Cantera La Esmeralda")
    proyecto = st.text_input("Proyecto", "Trituradora")
    responsable = st.text_input("Responsable", "Edwin")
    fecha = st.date_input("Fecha", datetime.date.today())
    limite = 75

def leer_laeq(file):
    file.seek(0)
    df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip', engine='python')
    col = next((c for c in df.columns if 'LAEQ' in str(c).upper()), df.columns[1])
    vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
    vals = vals[(vals>20)&(vals<140)]
    laeq = 10*math.log10(sum(10**(v/10) for v in vals)/len(vals))
    return round(laeq,1)

if 'puntos' not in st.session_state:
    st.session_state.puntos = []

st.subheader("➕ Agregar punto")
with st.form("form", clear_on_submit=True):
    c1,c2,c3 = st.columns(3)
    nombre = c1.text_input("Nombre", f"Punto {len(st.session_state.puntos)+1}")
    lat = c2.number_input("Lat", 4.60971, format="%.6f")
    lon = c3.number_input("Lon", -74.08175, format="%.6f")

    foto = st.file_uploader("📸 Foto punto", type=["jpg","png","jpeg"])

    m1,m2,m3,m4 = st.columns(4)
    temp = m1.number_input("Temp °C", 18.5)
    hum = m2.number_input("Hum %", 65.0)
    viento = m3.number_input("Viento m/s", 1.2)
    cielo = m4.selectbox("Cielo", ["Despejado","Parcial","Nublado"])

    f1,f2 = st.columns(2)
    ft = f1.file_uploader("CSV TOTAL", type="csv")
    fr = f2.file_uploader("CSV RESIDUAL", type="csv")
    obs = st.text_input("Obs", "Trituradora en operación")

    if st.form_submit_button("Guardar"):
        if ft and fr:
            lt = leer_laeq(ft)
            lr = leer_laeq(fr)
            diff = lt-lr
            lra = lt if diff>=10 else round(10*math.log10(10**(lt/10)-10**(lr/10)),1)
            cumple = "CUMPLE" if lra<=limite else "NO CUMPLE"
            st.session_state.puntos.append({"nombre":nombre,"lat":lat,"lon":lon,"foto":foto,"temp":temp,"hum":hum,"viento":viento,"cielo":cielo,"lt":lt,"lr":lr,"lra":lra,"cumple":cumple,"obs":obs,"ft":ft,"fr":fr})
            st.success(f"{nombre} {lra} dB {cumple}")
            st.rerun()

if st.session_state.puntos:
    df = pd.DataFrame([{"Punto":p["nombre"],"LRAeq":p["lra"],"Limite":limite,"Cumple":p["cumple"]} for p in st.session_state.puntos])
    st.dataframe(df, use_container_width=True)

    # GRAFICA
    fig, ax = plt.subplots()
    ax.bar(df["Punto"], df["LRAeq"])
    ax.axhline(limite, color='r', linestyle='--', label='Limite 75 dB')
    ax.legend()
    st.pyplot(fig)

    if st.button("📄 GENERAR INFORME FINAL + CARPETA"):
        # Guardar grafica
        fig.savefig("/tmp/graf.png", dpi=150)

        # PDF
        pdf = FPDF()
        pdf.add_page()
        # Logo
        if os.path.exists("logo.png"):
            try: pdf.image("logo.png",10,8,30)
            except: pass
        pdf.set_font("Arial",'B',14)
        pdf.cell(0,10,f"Informe Ruido {proyecto}", align='C', ln=True)
        pdf.set_font("Arial",'',9)
        pdf.cell(0,5,f"{empresa} | {fecha} | Sector C Industrial 75 dB | {responsable}", align='C', ln=True)
        pdf.ln(10)

        pdf.image("/tmp/graf.png", w=190)
        pdf.ln(5)

        pdf.set_font("Arial",'B',10)
        pdf.cell(0,7,"Resultados", ln=True)
        pdf.set_font("Arial",'',8)
        for p in st.session_state.puntos:
            pdf.cell(0,5,f"{p['nombre']}: LT {p['lt']} dB | LR {p['lr']} dB | LRAeq {p['lra']} dB | {p['cumple']} | {p['lat']},{p['lon']} | Meteo {p['temp']}C {p['hum']}% Viento {p['viento']}m/s {p['cielo']}", ln=True)
            if p["foto"]:
                try:
                    p["foto"].seek(0)
                    open(f"/tmp/foto_{p['nombre']}.jpg","wb").write(p["foto"].read())
                    pdf.image(f"/tmp/foto_{p['nombre']}.jpg", w=80)
                except: pass
            pdf.ln(3)

        # CORRECCION DEL ERROR
        out = pdf.output(dest='S')
        pdf_bytes = out.encode('latin1') if isinstance(out,str) else bytes(out)

        # ZIP
        zb = io.BytesIO()
        with zipfile.ZipFile(zb,"w") as z:
            z.writestr(f"{proyecto}/Informe_Final.pdf", pdf_bytes)
            z.write("/tmp/graf.png", f"{proyecto}/Grafica.png")
            for p in st.session_state.puntos:
                p["ft"].seek(0); z.writestr(f"{proyecto}/CSV/{p['nombre']}_TOTAL.csv", p["ft"].read())
                p["fr"].seek(0); z.writestr(f"{proyecto}/CSV/{p['nombre']}_RESIDUAL.csv", p["fr"].read())
                if p["foto"]:
                    p["foto"].seek(0); z.writestr(f"{proyecto}/Fotos/{p['nombre']}.jpg", p["foto"].read())

        zb.seek(0)
        st.download_button("⬇️ DESCARGAR CARPETA", zb, f"{proyecto}.zip", "application/zip")
        st.download_button("⬇️ DESCARGAR SOLO PDF", pdf_bytes, f"Informe_{proyecto}.pdf", "application/pdf")
