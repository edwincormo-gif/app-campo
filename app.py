import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Ruido Campo", page_icon="🔊")
st.title("🔊 Ruido Campo - vExcel")

sector = st.selectbox("Sector", ["Sector A - Residencial", "Sector B - Comercial", "Sector C - Industrial", "Sector D - Tranquilidad"])
horario = st.selectbox("Horario", ["Diurno", "Nocturno"])

f1 = st.file_uploader("Archivo TOTAL (prendida) - Excel o CSV", type=["csv","txt","xlsx","xls"])
f2 = st.file_uploader("Archivo RESIDUAL (apagada) - Excel o CSV", type=["csv","txt","xlsx","xls"])

def leer(f):
    if not f: return None
    try:
        f.seek(0)
        if f.name.endswith(".xlsx") or f.name.endswith(".xls"):
            df = pd.read_excel(f)
        else:
            try:
                df = pd.read_csv(f, sep=';', decimal=',', encoding='latin1', on_bad_lines='skip')
                if df.shape[1] < 2: raise Exception("x")
            except:
                f.seek(0)
                df = pd.read_csv(f, sep=',', encoding='latin1', on_bad_lines='skip')

        # busca LAeq
        col = None
        for c in df.columns:
            if 'LAEQ' in str(c).upper() and 'L90' not in str(c).upper():
                col = c
                break
        if not col:
            for c in df.columns:
                if str(c).upper().strip() in ['LAF','LA','LEQ']:
                    col = c
                    break
        if not col: col = df.columns[1]

        vals = pd.to_numeric(df[col].astype(str).str.replace(',','.'), errors='coerce').dropna()
        vals = vals[(vals>20)&(vals<140)]
        laeq = 10*math.log10(sum(10**(v/10) for v in vals)/len(vals))
        return round(laeq,1), col
    except Exception as e:
        st.error(f"Error: {e}"); return None

if f1:
    r=leer(f1)
    if r: st.success(f"TOTAL: {r[0]} dB - col: {r[1]}"); lt=r[0]
    else: lt=None
else: lt=None

if f2:
    r=leer(f2)
    if r: st.info(f"RESIDUAL: {r[0]} dB - col: {r[1]}"); lr=r[0]
    else: lr=None
else: lr=None

if f1 and f2 and lt and lr:
    if lr >= lt:
        st.warning(f"Residual {lr} >= Total {lt} - Fondo muy alto, no se puede corregir")
        lra=lt
    else:
        if lt - lr >= 10: lra=lt
        else: lra=round(10*math.log10(10**(lt/10)-10**(lr/10)),1)
    st.metric("LRAeq FINAL", f"{lra} dB")
    lim = {"Sector A - Residencial": (55,50), "Sector B - Comercial": (65,60), "Sector C - Industrial": (75,75), "Sector D - Tranquilidad": (45,45)}[sector]
    limite = lim[0] if horario=="Diurno" else lim[1]
    if lra <= limite: st.success(f"✅ CUMPLE <= {limite} dB")
    else: st.error(f"❌ NO CUMPLE > {limite} dB")
