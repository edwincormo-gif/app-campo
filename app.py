import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Ruido Campo", page_icon="🔊", layout="centered")
st.title("🔊 Medición Ruido - Campo Individual")
st.caption("HD2010 - Res. 0627 de 2006 | v2 Robust")

sector = st.selectbox("Sector", ["Sector A - Residencial", "Sector B - Comercial", "Sector C - Industrial", "Sector D - Tranquilidad"])
horario = st.selectbox("Horario", ["Diurno (7:01 - 21:00)", "Nocturno (21:01 - 7:00)"])
direccion = st.text_input("Dirección / Punto", "punto uno")
fuente = st.text_input("Fuente generadora", "planta trituradora de piedra")

st.divider()
st.subheader("1. Carga CSV del sonómetro Cirrus HD2010")

file_total = st.file_uploader("CSV TOTAL - Fuente prendida", type=["csv","txt"], key="t")
file_res = st.file_uploader("CSV RESIDUAL - Fuente apagada (fondo)", type=["csv","txt"], key="r")

def leer_laeq(file):
    if not file: return None
    try:
        file.seek(0)
        # Prueba 1: ; y coma decimal (formato Cirrus español)
        try:
            df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', on_bad_lines='skip')
            if df.shape[1] < 2: raise Exception("pocas cols")
        except:
            file.seek(0)
            # Prueba 2:, y punto decimal
            df = pd.read_csv(file, sep=',', encoding='latin1', on_bad_lines='skip')

        # Busca columna con dB
        col_db = None
        for c in reversed(df.columns): # busca desde el final
            vals_test = pd.to_numeric(df[c].astype(str).str.replace(',','.'), errors='coerce').dropna()
            if len(vals_test) > 20 and 30 < vals_test.mean() < 120:
                col_db = c
                break
        if not col_db:
            col_db = df.columns[-1]

        vals = pd.to_numeric(df[col_db].astype(str).str.replace(',','.'), errors='coerce').dropna()
        vals = vals[(vals>20) & (vals<140)]
        if len(vals)==0: return None
        suma = sum([10**(v/10) for v in vals])
        laeq = 10*math.log10(suma/len(vals))
        return round(laeq,1), len(vals), str(col_db)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

if file_total:
    res = leer_laeq(file_total)
    if res:
        lt, n, col = res
        st.success(f"TOTAL: {lt} dB ({n} datos - col: {col})")
    else:
        lt = None
        st.warning("No pude leer el TOTAL")
else:
    lt = None

if file_res:
    res = leer_laeq(file_res)
    if res:
        lr, n, col = res
        st.info(f"RESIDUAL: {lr} dB ({n} datos - col: {col})")
    else:
        lr = None
        st.warning("No pude leer el RESIDUAL - prueba abrir el CSV en Excel y guardarlo como CSV delimitado por comas")
else:
    lr = None

if file_total and file_res and 'lt' in locals() and 'lr' in locals() and lt and lr:
    st.divider()
    if lt - lr >= 10:
        lra = lt
        st.metric("LRAeq FINAL", f"{lra} dB", "Diferencia >10dB, no se corrige")
    else:
        lra = 10*math.log10(10**(lt/10) - 10**(lr/10))
        lra = round(lra,1)
        st.metric("LRAeq CORREGIDO", f"{lra} dB", f"Corregido -{round(lt-lra,1)} dB")

    limites = {"Sector A - Residencial": (55, 50), "Sector B - Comercial": (65, 60), "Sector C - Industrial": (75, 75), "Sector D - Tranquilidad": (45, 45)}
    lim_d, lim_n = limites[sector]
    limite = lim_d if "Diurno" in horario else lim_n

    if lra <= limite:
        st.balloons()
        st.success(f"✅ CUMPLE - {lra} dB <= Límite {limite} dB")
    else:
        st.error(f"❌ NO CUMPLE - {lra} dB > Límite {limite} dB")
