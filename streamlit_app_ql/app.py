import os
import time
import pandas as pd
import requests
import streamlit as st

# URL interna en Docker; fuera de Docker usar http://localhost:8010/graphql
GRAPHQL_URL = os.getenv("GRAPHQL_URL", "http://graphql_api:8010/graphql")

st.set_page_config(page_title="Predicción de Polvo (GraphQL)", layout="wide")
st.title("🌎 Predicción de Polvo Atmosférico — GraphQL")

def gql(query: str, variables: dict | None = None) -> dict:
    """POST al endpoint GraphQL; lanza error si hay 'errors'."""
    r = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables or {}}, timeout=30)
    r.raise_for_status()
    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]

@st.cache_data(ttl=20.0)
def get_model_info() -> dict:
    q = "query { modelInfo { timestamp isLoaded features } }"
    return gql(q)["modelInfo"]

# Sidebar: estado del modelo
with st.sidebar:
    st.header("🧠 Modelo (GraphQL)")
    st.caption(f"Endpoint: `{GRAPHQL_URL}`")
    try:
        info = get_model_info()
        st.write(f"**timestamp:** {info['timestamp']}")
        st.write(f"**loaded:** {info['isLoaded']}")
        st.code(", ".join(info["features"]) if info.get("features") else "(desconocidas)")
        if st.button("🔁 Reload model"):
            res = gql("mutation { reloadModel { status } }")
            st.success(res["reloadModel"]["status"])
            get_model_info.clear()
    except Exception as e:
        st.error(f"No se pudo obtener modelInfo: {e}")

# UI principal
modo = st.radio("Selecciona el modo:", ["Manual", "Batch (CSV)"], horizontal=True)

if modo == "Manual":
    st.subheader("🚀 Ingresá los datos manualmente")
    c1, c2, c3 = st.columns(3)
    with c1:
        TempOut = st.number_input("Temperatura Exterior (TempOut)", value=20.0)
        DewPt   = st.number_input("Punto de Rocío (DewPt)", value=5.0)
        WSpeed  = st.number_input("Velocidad de Viento Media (WSpeed)", value=10.0)
    with c2:
        WHSpeed = st.number_input("Ráfaga de Viento (WHSpeed)", value=20.0)
        Bar     = st.number_input("Presión Barométrica (Bar)", value=1013.0)
        Rain    = st.number_input("Lluvia (Rain)", value=0.0)
    with c3:
        ET       = st.number_input("Evapotranspiración (ET)", value=0.0)
        WDirDeg  = st.number_input("Dirección del Viento (WDirDeg)", value=180.0)
        DateNum  = st.number_input("Fecha (DateNum, timestamp)", value=float(time.time()))

    if st.button("🔮 Predecir (GraphQL)"):
        q = """
        mutation($x:WeatherData!){
          predict(weatherData:$x){ probability }
        }"""
        vars_ = {"x":{
            "TempOut": TempOut, "DewPt": DewPt, "WSpeed": WSpeed, "WHSpeed": WHSpeed,
            "Bar": Bar, "Rain": Rain, "ET": ET, "WDirDeg": WDirDeg, "DateNum": DateNum
        }}
        try:
            res = gql(q, vars_)
            st.success(f"Probabilidad: {res['predict']['probability']:.4f}")
        except Exception as e:
            st.error(f"Error en predicción: {e}")

else:
    st.subheader("📁 Subí un archivo CSV")
    st.caption("El CSV debe tener columnas: TempOut,DewPt,WSpeed,WHSpeed,Bar,Rain,ET,WDirDeg,DateNum")
    file = st.file_uploader("Elegí el archivo CSV", type="csv")

    if file is not None:
        try:
            df = pd.read_csv(file)
            st.write("Vista previa del archivo:")
            st.dataframe(df.head(), use_container_width=True)

            if st.button("🔮 Predecir en batch (GraphQL)"):
                q = """
                mutation($xs:[WeatherData!]!){
                  predictBatch(weatherDataList:$xs){
                    predictions { date probability }
                  }
                }"""
                xs = df.to_dict(orient="records")
                res = gql(q, {"xs": xs})
                preds = res["predictBatch"]["predictions"]

                out = df.copy()
                out["date"] = [p["date"] for p in preds]
                out["probabi]()
