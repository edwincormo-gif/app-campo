import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Ruido Campo", page_icon="🔊", layout="centered")
st.title("🔊 Medición Ruido - Campo Individual")
st.caption("HD2010 - Res. 0627 | vFinal")

sector = st.selectbox("Sector", ["Sector A - Residencial", "Sector B - Comercial", "Sector C - Industrial", "Sector D - Tranquilidad"])
horario = st.selectbox("Horario", ["Diurno (7:01 - 21:00)", "Nocturno (21:01 - 7:00)"])
direccion = st.text_input("Dirección / Punto", "punto uno")
fuente = st.text_input("Fuente generadora", "planta trituradora de piedra")

st.divider()
file_total = st.file_uploader("CSV TOTAL - Fuente prendida", type=["csv","txt"], key="t")
file_res = st.file_uploader("CSV RESIDUAL - Fuente apagada", type=["csv","txt"], key="r")

def leer_laeq(file):
    if not file: return None
    try:
        file.seek(0)
        try:
            df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', on_bad_lines='skip')
            if df.shape[1] < 2: raise Exception("pocas")
        except:
            file.seek(0)
            df = pd.read_csv(file, sep=',', encoding='latin1', on_bad_lines='skip')

        # 1. Busca columna buena primero
        col_db = None
        for c in df.columns:
            cn = str(c).upper()
            if 'LAEQ' in cn or 'LEQ' in cn or c == 'LAF' or 'LA' == str(c)[:2]:
                if 'L90' not in cn and 'L10' not in cn and 'L50' not in cn:
                    col_db = c
                    break

        # 2. Si no encuentra, busca la de promedio más alto (que suele ser LAeq)
        if not col_db:
            mejor = None
            mejor_mean = 0
            for c in df.columns:
                vals = pd.to_numeric(df[c].astype(str).str.replace(',','.'), errors='coerce').dropna()
                if len(vals) > 20 and 30 < vals.mean() < 120:
                    if vals.mean() > mejor_mean:
                        mejor_mean = vals.mean()
                        mejor = c
            col_db = mejor

        vals = pd.to_numeric(df[col_db].astype(str).str.replace(',','.'), errors='coerce').dropna()
        vals = vals[(vals>20) & (vals<140)]
        if len(vals)==0: return None
        suma = sum([10**(v/10) for v in vals])
        laeq = 10*math.log10(suma/len(vals))
        return round(laeq,1), len(vals), str(col_db)
    except Exception as e:
        st.error(f"Error leyendo: {e}")
        return None

lt = lr = None
if file_total:
    res = leer_laeq(file_total)
    if res:
        lt, n, col = res
        st.success(f"TOTAL: {lt} dB ({n} datos - col: {col})")

if file_res:
    res = leer_laeq(file_res)
    if res:
        lr, n, col = res
        st.info(f"RESIDUAL: {lr} dB ({n} datos - col: {col})")

if lt and lr:
    st.divider()
    if lr >= lt:
        st.warning(f"⚠️ No se puede corregir. Residual {lr} dB >= Total {lt} dB. El fondo es más alto que la fuente. Verifica que el CSV residual sea el correcto.")
        lra = lt
        st.metric("LRAeq (sin corrección - fondo muy alto)", f"{lra} dB")
    else:
        if lt - lr >= 10:
            lra = lt
            st.metric("LRAeq FINAL", f"{lra} dB", "Diferencia >10dB, no se corrige")
        else:
            lra = 10*math.log10(10**(lt/10) - 10**(lr/10))
            lra = round(lra,1)
            st.metric("LRAeq CORREGIDO", f"{lra} dB", f"Corregido -{round(lt-lra,1)} dB")

    if 'lra' in locals() and lra:
        limites = {"Sector A - Residencial": (55, 50), "Sector B - Comercial": (65, 60), "Sector C - Industrial": (75, 75), "Sector D - Tranquilidad": (45, 45)}
        lim_d, lim_n = limites[sector]
        limite = lim_d if "Diurno" in horario else lim_n
        if lra <= limite:
            st.balloons()
            st.success(f"✅ CUMPLE - {lra} dB <= {limite} dB")
        else:
            st.error(f"❌ NO CUMPLE - {lra} dB > {limite} dB")
