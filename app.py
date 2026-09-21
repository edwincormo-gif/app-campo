import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Ruido Campo", page_icon="🔊", layout="centered")
st.title("🔊 Medición Ruido - Campo Individual")
st.write("App para HD2010 - Res. 0627 de 2006")

sector = st.selectbox("Sector", ["Sector A - Residencial", "Sector B - Comercial", "Sector C - Industrial", "Sector D - Tranquilidad"])
horario = st.selectbox("Horario", ["Diurno (7:01 - 21:00)", "Nocturno (21:01 - 7:00)"])
direccion = st.text_input("Dirección / Punto", "punto uno")
fuente = st.text_input("Fuente generadora", "planta trituradora de piedra")

st.divider()
st.subheader("1. Carga CSV del sonómetro Cirrus HD2010")

file_total = st.file_uploader("CSV TOTAL - Fuente prendida", type=["csv","txt"])
file_res = st.file_uploader("CSV RESIDUAL - Fuente apagada (fondo)", type=["csv","txt"])

def leer_laeq(file):
    if not file:
        return None
    try:
        df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', on_bad_lines='skip')
        # buscar columna de dB
        col_db = None
        for c in df.columns:
            if 'dB' in str(c) or 'Leq' in str(c) or 'LAF' in str(c):
                col_db = c
                break
        if not col_db:
            col_db = df.columns[-1]

        vals = pd.to_numeric(df[col_db].astype(str).str.replace(',','.'), errors='coerce').dropna()
        if len(vals) == 0:
            return None
        suma = sum([10**(v/10) for v in vals])
        laeq = 10*math.log10(suma/len(vals))
        return round(laeq, 1)
    except Exception as e:
        st.error(f"Error leyendo: {e}")
        return None

lt = leer_laeq(file_total) if file_total else None
lr = leer_laeq(file_res) if file_res else None

if lt:
    st.success(f"LAeq TOTAL: {lt} dB")
if lr:
    st.info(f"LAeq RESIDUAL: {lr} dB")

if lt and lr:
    st.divider()
    # Corrección Res 0627
    if lt - lr >= 10:
        lra = lt
        st.metric("LRAeq FINAL (sin corrección)", f"{lra} dB")
    else:
        try:
            lra = 10*math.log10(10**(lt/10) - 10**(lr/10))
            lra = round(lra,1)
            st.metric("LRAeq CORREGIDO", f"{lra} dB", f"Se corrigió -{round(lt-lra,1)} dB")
        except:
            lra = lt
            st.metric("LRAeq FINAL", f"{lra} dB")

    limites = {"Sector A - Residencial": (55, 50), "Sector B - Comercial": (65, 60), "Sector C - Industrial": (75, 75), "Sector D - Tranquilidad": (45, 45)}
    lim_d, lim_n = limites[sector]
    limite = lim_d if "Diurno" in horario else lim_n

    st.subheader("Resultado Normativo")
    if lra <= limite:
        st.balloons()
        st.success(f"✅ CUMPLE - {lra} dB <= Límite {limite} dB ({sector} {horario})")
    else:
        st.error(f"❌ NO CUMPLE - {lra} dB > Límite {limite} dB ({sector} {horario})")

st.divider()
st.caption(f"Punto: {direccion} | Fuente: {fuente}")
