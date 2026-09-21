import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Ruido Campo", page_icon="🔊")
st.title("🔊 Ruido - Lectura a.csv")

sector = st.selectbox("Sector", ["Sector A - Residencial", "Sector B - Comercial", "Sector C - Industrial", "Sector D - Tranquilidad"])
horario = st.selectbox("Horario", ["Diurno", "Nocturno"])

f1 = st.file_uploader("TOTAL (prendida) - sube el a.csv", type=["csv"])
f2 = st.file_uploader("RESIDUAL (apagada) - sube el otro a.csv", type=["csv"])

def leer(f):
    if not f: return None
    f.seek(0)
    # Tu CSV tiene una fila basura arriba, la saltamos
    try:
        df = pd.read_csv(f, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip')
    except:
        f.seek(0)
        df = pd.read_csv(f, sep=';', decimal=',', encoding='latin1', skiprows=1, on_bad_lines='skip', engine='python')

    # df ahora si tiene columna LAeq
    col = 'LAeq'
    if col not in df.columns:
        for c in df.columns:
            if 'LAEQ' in str(c).upper():
                col = c
                break

    vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
    vals = vals[(vals>20)&(vals<140)]
    laeq = 10*math.log10(sum(10**(v/10) for v in vals)/len(vals))
    return round(laeq,1), len(vals)

if f1:
    lt, n = leer(f1)
    st.success(f"TOTAL: {lt} dB - {n} datos")

if f2:
    lr, n = leer(f2)
    st.info(f"RESIDUAL: {lr} dB - {n} datos")

if f1 and f2:
    lt = leer(f1)[0]
    lr = leer(f2)[0]
    if lr >= lt:
        st.warning(f"⚠️ Residual {lr} >= Total {lt} - fondo más alto")
        lra = lt
    else:
        lra = round(10*math.log10(10**(lt/10)-10**(lr/10)),1) if lt-lr <10 else lt
    st.metric("LRAeq CORREGIDO", f"{lra} dB")
