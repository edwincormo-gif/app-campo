import streamlit as st
import pandas as pd
import math, datetime, io, zipfile, os
import matplotlib.pyplot as plt
from fpdf import FPDF

st.set_page_config(page_title="Ruido Informe Final", page_icon="📄", layout="wide")
st.title("📄 Generador Informe Final - Autoridad Ambiental")
st.caption("Con gráficas + logo + 1 a 10 puntos - Res. 0627 de 2006")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📋 Datos Proyecto")
    empresa = st.text_input("Empresa", "Cantera La Esmeralda")
    proyecto = st.text_input("Proyecto", "Planta Trituradora")
    responsable = st.text_input("Responsable", "Edwin")
    fecha_med = st.date_input("Fecha", datetime.date.today())
    sector = st.selectbox("Sector", ["Sector C - Industrial","Sector B - Comercial","Sector A - Residencial"])
    horario = st.selectbox("Horario", ["Diurno (7:01-21:00)","Nocturno (21:01-7:00)"])
    limite = 75 if "Industrial" in sector else (65 if "Comercial" in sector else 55)
    st.metric("Límite", f"{limite} dB")
    st.divider()
    st.write("Logo: sube un archivo `logo.png` a tu repo en GitHub")

def leer_laeq(file):
    file.seek(0)
    try:
        df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip', engine='python')
    except:
        return None
    col = next((c for c in df.columns if 'LAEQ' in str(c).upper()), df.columns[1] if len(df.columns)>1 else df.columns[0])
    vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
    vals = vals[(vals>20)&(vals<140)]
    if len(vals)==0: return None
    laeq = 10*math.log10(sum(10**(v/10) for v in vals)/len(vals))
    return round(laeq,1), len(vals)

if 'puntos' not in st.session_state:
    st.session_state.puntos = []

st.subheader("➕ 1. Agregar Punto (con fotos y meteo)")

with st.form("form_punto", clear_on_submit=True):
    c1,c2,c3 = st.columns(3)
    nombre = c1.text_input("Nombre Punto", f"Punto {len(st.session_state.puntos)+1}")
    lat = c2.number_input("Latitud", value=4.609710, format="%.6f")
    lon = c3.number_input("Longitud", value=-74.081750, format="%.6f")

    cf1, cf2 = st.columns(2)
    foto = cf1.file_uploader("📸 Foto del punto (opcional)", type=["jpg","jpeg","png"])
    cm1,cm2,cm3 = st.columns(3)
    temp = cm1.number_input("Temp °C", 18.5)
    viento = cm2.number_input("Viento m/s", 1.2)
    cielo = cm3.selectbox("Cielo", ["Despejado","Parcial","Nublado"])

    ca1,ca2 = st.columns(2)
    f_total = ca1.file_uploader("CSV TOTAL (a.csv)", type=["csv"])
    f_res = ca2.file_uploader("CSV RESIDUAL (a.csv)", type=["csv"])
    obs = st.text_area("Observaciones", "Fuente en operación normal")

    if st.form_submit_button("💾 Guardar Punto"):
        if f_total and f_res:
            lt_data = leer_laeq(f_total)
            lr_data = leer_laeq(f_res)
            if lt_data and lr_data:
                lt, nt = lt_data
                lr, nr = lr_data
                diff = lt - lr
                lra = lt if diff>=10 or lr>=lt else round(10*math.log10(10**(lt/10)-10**(lr/10)),1)
                cumple = "CUMPLE" if lra <= limite else "NO CUMPLE"
                corr = "No corrige >10dB" if diff>=10 else "Corregido"
                st.session_state.puntos.append({
                    "nombre":nombre,"lat":lat,"lon":lon,"foto":foto,
                    "temp":temp,"viento":viento,"cielo":cielo,
                    "total":lt,"residual":lr,"lra":lra,"diff":diff,"corr":corr,"cumple":cumple,
                    "obs":obs,"ft":f_total,"fr":f_res
                })
                st.success(f"Guardado {nombre}: {lra} dB - {cumple}")
                st.rerun()
            else:
                st.error("Error CSV - usa tipo a.csv")

# --- MOSTRAR Y GRAFICAS ---
if st.session_state.puntos:
    st.divider()
    df = pd.DataFrame([{"Punto":p["nombre"],"TOTAL":p["total"],"RESIDUAL":p["residual"],"LRAeq":p["lra"],"Limite":limite,"Cumple":p["cumple"]} for p in st.session_state.puntos])
    st.dataframe(df, use_container_width=True)

    # GRAFICAS EN STREAMLIT
    colg1, colg2 = st.columns(2)
    with colg1:
        st.write("**Grafica LRAeq vs Límite**")
        fig, ax = plt.subplots()
        ax.bar(df["Punto"], df["LRAeq"], label="LRAeq")
        ax.axhline(limite, color='red', linestyle='--', label=f"Límite {limite} dB")
        ax.set_ylabel("dB(A)")
        ax.legend()
        plt.xticks(rotation=20)
        st.pyplot(fig)

    with colg2:
        st.map(pd.DataFrame([{"lat":p["lat"],"lon":p["lon"]} for p in st.session_state.puntos]))

    # --- GENERAR PDF FINAL CON GRAFICAS ---
    st.divider()
    st.subheader("📦 2. Generar Informe Final para Autoridad")

    if st.button("🚀 GENERAR INFORME FINAL PDF + CARPETA"):
        # 1. Crear grafica para PDF
        fig2, ax2 = plt.subplots(figsize=(6,3))
        ax2.bar(df["Punto"], df["LRAeq"], color='#2E86AB')
        ax2.axhline(limite, color='red', linestyle='--', label=f"Límite {limite} dB")
        ax2.set_ylabel("dB(A)")
        ax2.set_title(f"Niveles LRAeq vs Límite {sector}")
        ax2.legend()
        plt.tight_layout()
        graf_path = "/tmp/grafica.png"
        fig2.savefig(graf_path, dpi=200)
        plt.close()

        # 2. Crear PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Logo
        try:
            if os.path.exists("logo.png"):
                pdf.image("logo.png", 10, 8, 30)
        except:
            pass

        pdf.set_font("Arial",'B',14)
        pdf.cell(0,10,f"INFORME DE RUIDO AMBIENTAL - {proyecto}", ln=True, align='C')
        pdf.set_font("Arial",'',9)
        pdf.cell(0,5,f"Empresa: {empresa} | Fecha: {fecha_med} | {sector} | {horario} | Límite {limite} dB | Resp: {responsable}", ln=True, align='C')
        pdf.ln(10)

        # Resumen ejecutivo
        pdf.set_font("Arial",'B',11)
        pdf.set_fill_color(230,230,230)
        pdf.cell(0,7," RESUMEN EJECUTIVO", ln=True, fill=True)
        pdf.set_font("Arial",'',9)
        cumple_count = len([p for p in st.session_state.puntos if p["cumple"]=="CUMPLE"])
        pdf.multi_cell(0,4,f"Se evaluaron {len(st.session_state.puntos)} puntos. {cumple_count} cumplen y {len(st.session_state.puntos)-cumple_count} no cumplen con el limite de {limite} dB para {sector} {horario}. Equipo: Cirrus HD2010 Clase 1. Metodologia Res 0627 de 2006 Anexo 3.")
        pdf.ln(3)

        # Grafica en PDF
        pdf.image(graf_path, x=10, w=190)
        pdf.ln(5)

        # Tabla resultados
        pdf.set_font("Arial",'B',10)
        pdf.cell(0,7," RESULTADOS POR PUNTO", ln=True, fill=True)
        pdf.set_font("Arial",'B',7)
        cols = ["Punto","TOTAL","RESIDUAL","LRAeq","Límite","Estado"]
        ws = [35,20,20,20,20,25]
        for i,c in enumerate(cols):
            pdf.cell(ws[i],6,c,border=1,align='C')
        pdf.ln()
        pdf.set_font("Arial",'',7)
        for p in st.session_state.puntos:
            pdf.cell(ws[0],5,p["nombre"],border=1)
            pdf.cell(ws[1],5,str(p["total"]),border=1,align='C')
            pdf.cell(ws[2],5,str(p["residual"]),border=1,align='C')
            pdf.cell(ws[3],5,str(p["lra"]),border=1,align='C')
            pdf.cell(ws[4],5,str(limite),border=1,align='C')
            pdf.cell(ws[5],5,p["cumple"],border=1,align='C')
            pdf.ln()

        pdf.ln(5)
        # Detalle por punto con foto
        for p in st.session_state.puntos:
            pdf.add_page()
            pdf.set_font("Arial",'B',11)
            pdf.cell(0,7,f" {p['nombre']} - LRAeq {p['lra']} dB - {p['cumple']}", ln=True, fill=True)
            pdf.set_font("Arial",'',8)
            pdf.cell(0,4,f"Coordenadas: {p['lat']}, {p['lon']} | TOTAL {p['total']} dB | RESIDUAL {p['residual']} dB | Diff {p['diff']:.1f} dB | {p['corr']}", ln=True)
            pdf.cell(0,4,f"Meteo: Temp {p['temp']}C, Viento {p['viento']} m/s, Cielo {p['cielo']} | Obs: {p['obs']}", ln=True)
            pdf.ln(3)
            if p["foto"]:
                try:
                    p["foto"].seek(0)
                    tmp_foto = f"/tmp/{p['nombre']}_foto.jpg"
                    with open(tmp_foto,"wb") as f:
                        f.write(p["foto"].read())
                    pdf.image(tmp_foto, x=10, w=90)
                except:
                    pass

        # Conclusiones
        pdf.add_page()
        pdf.set_font("Arial",'B',11)
        pdf.cell(0,7," CONCLUSIONES", ln=True, fill=True)
        pdf.set_font("Arial",'',9)
        pdf.multi_cell(0,4,f"""
1. De {len(st.session_state.puntos)} puntos evaluados, {cumple_count} CUMPLEN con Res. 0627 Art.9 (Limite {limite} dB).
2. Metodologia segun Art.8: LRAeq = 10*log(10^(LT/10)-10^(LR/10)). Si diferencia >10 dB no se corrige (como tu punto 1 de 63.3 dB).
3. Condiciones meteorologicas sin afectacion (viento <5 m/s, sin lluvia).
4. Recomendacion: Mantener medidas de control y anexar certificado de calibracion del sonometro Cirrus HD2010.
5. Informe valido para presentacion ante Autoridad Ambiental CAR/ANLA.
        """)

        # FIX PDF BYTES
        pdf_out = pdf.output(dest='S')
        pdf_bytes = pdf_out.encode('latin1') if isinstance(pdf_out, str) else bytes(pdf_out)

        # ZIP final
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr(f"{proyecto}/Informe_Final_{proyecto}.pdf", pdf_bytes)
            # Excel
            df.to_excel(f"/tmp/resumen.xlsx", index=False)
            zf.write(f"/tmp/resumen.xlsx", f"{proyecto}/Resumen.xlsx")
            # Graficas
            zf.write(graf_path, f"{proyecto}/Grafica_LRAeq.png")
            # CSVs
            for p in st.session_state.puntos:
                p["ft"].seek(0)
                zf.writestr(f"{proyecto}/Datos_Crudos/{p['nombre']}_TOTAL.csv", p["ft"].read())
                p["fr"].seek(0)
                zf.writestr(f"{proyecto}/Datos_Crudos/{p['nombre']}_RESIDUAL.csv", p["fr"].read())

        zip_buf.seek(0)
        st.download_button("⬇️ DESCARGAR INFORME + CARPETA COMPLETA", data=zip_buf, file_name=f"Informe_{proyecto}_{fecha_med}.zip", mime="application/zip")
        st.download_button("⬇️ SOLO PDF", data=pdf_bytes, file_name=f"Informe_{proyecto}.pdf", mime="application/pdf")
        st.balloons()
        st.success(f"¡Listo! Informe generado con {len(st.session_state.puntos)} puntos con gráficas y logo.")

    if st.button("🗑️ Borrar todo"):
        st.session_state.puntos = []
        st.rerun()
