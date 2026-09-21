import streamlit as st
import pandas as pd

st.set_page_config(page_title="Ruido - Campo", page_icon="🔊", layout="centered")
st.title("🔊 Medición Ruido Ambiental")

# Campos
st.subheader("Datos de Campo")
sector = st.selectbox("Sector", ["Sector A - Residencial", "Sector B - Comercial", "Sector C - Industrial", "Sector D - Tranquilidad"])
horario = st.selectbox("Horario", ["Diurno (7:01 - 21:00)", "Nocturno (21:01 - 7:00)"])
direccion = st.text_input("Dirección del punto")
fuente = st.text_input("Fuente generadora")

st.divider()
st.subheader("Cargar CSV del HD2010")

col1, col2 = st.columns(2)
with col1:
    file_total = st.file_uploader("TOTAL (fuente prendida)", type=["csv", "txt"])
with col2:
    file_res = st.file_uploader("RESIDUAL (fuente apagada)", type=["csv", "txt"])

def calcular_laeq(file):
    if file is None: return None
    try:
        df = pd.read_csv(file, sep=';', decimal=',', encoding='latin1', on_bad_lines='skip')
        # Busca columna que tenga dB
        for col in df.columns:
            if 'dB' in str(col) or 'Leq' in str(col) or 'LAF' in str(col):
                vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
                if len(vals)>0:
                    import math
                    suma = sum([10**(v/10) for v in vals])
                    laeq = 10*math.log10(suma/len(vals))
                    return round(laeq,1), len(vals)
        return None, 0
    except Exception as e:
        st.error(f"Error leyendo CSV: {e}")
        return None, 0

if file_total:
    laeq_total, n = calcular_laeq(file_total)
    if laeq_total: st.success(f"TOTAL LAF: {laeq_total} dB - {n} datos")

if file_res:
    laeq_res, n = calcular_laeq(file_res)
    if laeq_res: st.info(f"RESIDUAL LAF: {laeq_res} dB - {n} datos")

if file_total and file_res:
    lt, _ = calcular_laeq(file_total)
    lr, _ = calcular_laeq(file_res)
    if lt and lr:
        import math
        # Correccion por ruido residual
        if lt - lr >= 10:
            lra = lt
            st.metric("LRAeq CORREGIDO", f"{lra} dB", "Diferencia >10dB, no se corrige")
        else:
            lra = 10*math.log10(10**(lt/10) - 10**(lr/10))
            st.metric("LRAeq CORREGIDO", f"{round(lra,1)} dB", f"Corregido -{round(lt-lra,1)}dB")

        # Limites Res 0627
        limites = {"Sector A - Residencial": (55, 50), "Sector B - Comercial": (65, 60), "Sector C - Industrial": (75, 75), "Sector D - Tranquilidad": (45, 45)}
        lim_d, lim_n = limites[sector]
        limite = lim_d if "Diurno" in horario else lim_n

        st.divider()
        if lra <= limite:
            st.balloons()
            st.success(f"✅ CUMPLE - LRA {round(lra,1)} <= Límite {limite} dB")
        else:
            st.error(f"❌ NO CUMPLE - LRA {round(lra,1)} > Límite {limite} dB")
