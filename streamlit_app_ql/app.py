import os
import time
import pandas as pd
import requests
import streamlit as st

# URL interna en Docker; fuera de Docker usar http://localhost:8010/graphql
GRAPHQL_URL = os.getenv("GRAPHQL_URL", "http://graphql_api:8010/graphql")

st.set_page_config(page_title="Predicción de Polvo (GraphQL)", layout="wide")
st.title("🌎 Predicción de Polvo Atmosférico — GraphQL")

# ---------------------------
# Helpers GraphQL
# ---------------------------
def gql(query: str, variables: dict | None = None) -> dict:
    """
    Ejecuta una query/mutation GraphQL.
    Lanza RuntimeError si el server responde con 'errors'.
    """
    try:
        r = requests.post(
            GRAPHQL_URL,
            json={"query": query, "variables": variables or {}},
            timeout=30,
        )
        r.raise_for_status()
        payload = r.json()
        if "errors" in payload:
            # Propagamos los errores de GraphQL de forma legible
            raise RuntimeError(payload["errors"])
        return payload["data"]
    except Exception as e:
        # Re-lanzamos con más contexto para que la UI muestre el error
        raise RuntimeError(f"Fallo GraphQL: {e}") from e


@st.cache_data(ttl=20.0)
def get_model_info() -> dict:
    q = "query { modelInfo { timestamp isLoaded features } }"
    return gql(q)["modelInfo"]


def validate_columns(df: pd.DataFrame) -> list:
    """
    Valida que el CSV tenga las columnas esperadas por el schema (camelCase de Strawberry).
    """
    required = [
        "TempOut", "DewPt", "WSpeed", "WHSpeed",
        "Bar", "Rain", "ET", "WDirDeg", "DateNum",
    ]
    missing = [c for c in required if c not in df.columns]
    return missing


# ---------------------------
# Sidebar: estado del modelo
# ---------------------------
with st.sidebar:
    st.header("🧠 Modelo (GraphQL)")
    st.caption(f"Endpoint: `{GRAPHQL_URL}`")
    try:
        info = get_model_info()
        st.write(f"**timestamp:** {info.get('timestamp', 'N/A')}")
        st.write(f"**loaded:** {info.get('isLoaded', False)}")
        feats = info.get("features") or []
        st.code(", ".join(map(str, feats)) if feats else "(desconocidas)")
        if st.button("🔁 Reload model"):
            res = gql("mutation { reloadModel { status } }")
            st.success(res["reloadModel"]["status"])
            get_model_info.clear()
    except Exception as e:
        st.error(f"No se pudo obtener modelInfo: {e}")

# ---------------------------
# UI: Manual / Batch
# ---------------------------
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

    if st.button("🔮 Predecir (GraphQL)", key="predict_manual_btn"):
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
            prob = res["predict"]["probability"]
            st.success(f"Probabilidad: {prob:.4f}")
        except Exception as e:
            st.error(f"Error en predicción: {e}")

else:
    st.subheader("📁 Subí un archivo CSV")
    st.caption("El CSV debe tener columnas: TempOut,DewPt,WSpeed,WHSpeed,Bar,Rain,ET,WDirDeg,DateNum")

    file = st.file_uploader("Elegí el archivo CSV", type="csv", key="csv_uploader")

    df = None
    if file is not None:
        try:
            df = pd.read_csv(file)
            st.write("Vista previa del archivo:")
            st.dataframe(df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Error leyendo CSV: {e}")
            df = None

    # El botón SIEMPRE visible (con key único)
    do_predict = st.button("🔮 Predecir en batch (GraphQL)", key="predict_batch_btn")

    if do_predict:
        if df is None:
            st.warning("Primero subí un CSV válido con las columnas requeridas.")
        else:
            missing = validate_columns(df)
            if missing:
                st.error(f"Faltan columnas en el CSV: {missing}")
            else:
                try:
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
                    out["probability"] = [p["probability"] for p in preds]

                    st.success(f"Predicciones: {len(out)} filas")
                    st.dataframe(out, use_container_width=True)

                    # Gráfico temporal si tenemos DateNum
                    if "DateNum" in out.columns:
                        dd = out.copy()
                        dd["date_dt"] = pd.to_datetime(dd["DateNum"], unit="s", errors="coerce")
                        dd = dd.dropna(subset=["date_dt"])
                        if not dd.empty:
                            st.line_chart(dd.set_index("date_dt")["probability"])
                except Exception as e:
                    st.error(f"Error en predicción batch: {e}")
