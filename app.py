import streamlit as st
import pandas as pd
import numpy as np
import os
from PIL import Image

st.set_page_config(page_title="EQUISIMA OFFLINE", page_icon="🟡", layout="wide")

# --- PWA PARA QUE FUNCIONE SIN DATOS ---
st.markdown("""
<script>
if ('serviceWorker' in navigator) {
  let sw = `self.addEventListener('install', e=>{e.waitUntil(caches.open('equisima-v2').then(c=>c.addAll(['./'])))}); self.addEventListener('fetch', e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).catch(()=>caches.match('./'))))});`;
  let blob = new Blob([sw], {type: 'text/javascript'});
  navigator.serviceWorker.register(URL.createObjectURL(blob)).then(()=>console.log('OFFLINE OK'));
}
</script>
""", unsafe_allow_html=True)

# Logo
if os.path.exists("logo.png"):
    st.image("logo.png", width=120)

st.title("🟡 EQUISIMA SAS - APP CAMPO OFFLINE")
st.caption("3224523451 | edwincormo@gmail.com | Funciona sin internet despues de instalar")

def calcular_laeq(file):
    try:
        df = pd.read_csv(file, sep=';', encoding='latin-1', engine='python')
        # Buscar columna con dB
        col = None
        for c in df.columns:
            if 'LAeq' in str(c) or 'Leq' in str(c) or 'dB' in str(c) or 'LAF' in str(c):
                col = c
                break
        if col is None:
            col = df.columns[1] if len(df.columns)>1 else df.columns[0]
        vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
        vals = vals[(vals>20)&(vals<140)]
        if len(vals)==0:
            return None, "No hay valores"
        laeq = 10*np.log10((10**(vals/10)).mean())
        return round(laeq,1), len(vals)
    except Exception as e:
        return None, str(e)

# FORMULARIO
with st.form("punto"):
    st.subheader("1️⃣ Datos del Punto")
    c1,c2 = st.columns(2)
    nombre = c1.text_input("Nombre Punto", "R-1 K0+500")
    limite = c2.selectbox("Limite dB", [75, 55, 65], index=0)
    macro = st.text_input("Macrolocalizacion", "Par Vial Puente Tierra")
    micro = st.text_input("Microlocalizacion", "Costado via")
    c3,c4 = st.columns(2)
    lat = c3.text_input("Latitud", "7.123456")
    lon = c4.text_input("Longitud", "-73.123456")
    c5,c6,c7 = st.columns(3)
    temp = c5.text_input("Temp C", "22")
    viento = c6.text_input("Viento m/s", "1.2")
    hum = c7.text_input("Hum %", "65")
    cielo = st.selectbox("Cielo", ["Despejado","Parcial","Nublado"])
    fuente = st.text_input("Fuente sonora", "Trituradora")

    st.subheader("2️⃣ Archivos a.csv del sonometro")
    f_total = st.file_uploader("CSV TOTAL a.csv", type=['csv'], key='t')
    f_res = st.file_uploader("CSV RESIDUAL a.csv", type=['csv'], key='r')
    foto = st.camera_input("📸 Foto del punto")

    guardar = st.form_submit_button("💾 CALCULAR LRAeq Y GUARDAR OFFLINE", use_container_width=True)

if guardar:
    if not f_total or not f_res:
        st.error("Carga los 2 CSV a.csv")
    else:
        lt, n1 = calcular_laeq(f_total)
        lr, n2 = calcular_laeq(f_res)
        if lt and lr:
            diff = lt - lr
            if diff >= 10:
                lra = lt
            else:
                lra = 10*np.log10(10**(lt/10)-10**(lr/10))
                lra = round(lra,1)
            cumple = "CUMPLE" if lra <= limite else "NO CUMPLE"
            color = "green" if cumple=="CUMPLE" else "red"
            st.markdown(f"<h2 style='color:{color}'>LTotal: {lt} dB | LResidual: {lr} dB | LRAeq: {lra} dB | {cumple}</h2>", unsafe_allow_html=True)

            if 'puntos' not in st.session_state:
                st.session_state.puntos = []
            st.session_state.puntos.append({
                "Punto": nombre, "LT": lt, "LR": lr, "LRAeq": lra,
                "Estado": cumple, "Lat": lat, "Lon": lon,
                "Macro": macro, "Micro": micro, "Temp": temp
            })
            st.success(f"Guardado OFFLINE: {nombre} - {lra} dB")
        else:
            st.error(f"Error: {n1} {n2}")

# TABLA
if 'puntos' in st.session_state and st.session_state.puntos:
    st.subheader("📋 Puntos guardados en este celular (offline)")
    df = pd.DataFrame(st.session_state.puntos)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📄 Descargar Excel Informe", csv, "Informe_EQUISIMA_OFFLINE.csv", "text/csv", use_container_width=True)

    if st.button("🗑️ Borrar todo"):
        st.session_state.puntos = []
        st.rerun()

st.info("💡 **Para que funcione SIN DATOS en obra:** 1) Abre esta app UNA VEZ con datos 2) En Chrome, 3 puntitos > Agregar a pantalla principal > Instalar 3) Abre desde el icono amarillo, ya funciona sin internet")
