import os, json, time, threading, queue
import pandas as pd
import streamlit as st
from confluent_kafka import Consumer, KafkaException

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC     = os.getenv("KAFKA_TOPIC", "predictions")

st.set_page_config(page_title="Streaming Predictions", layout="wide")
st.title("Predicciones en tiempo real (Kafka → Streamlit)")

# --- Consumer como recurso compartido y cola thread-safe ---
@st.cache_resource
def _consumer_and_queue():
    c = Consumer({
        "bootstrap.servers": BOOTSTRAP,
        "group.id": "streamlit-kafka-consumer",
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
    })
    c.subscribe([TOPIC])
    q = queue.Queue(maxsize=5000)

    def _loop():
        try:
            while True:
                msg = c.poll(0.5)
                if msg is None:
                    continue
                if msg.error():
                    # No tiramos la app, pero podrías imprimir si querés
                    continue
                try:
                    payload = json.loads(msg.value().decode("utf-8"))
                    q.put(payload)
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            c.close()

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    return c, q

_, Q = _consumer_and_queue()

# --- Buffers y UI ---
buf = []
table_ph = st.empty()
chart_ph = st.empty()
stats_ph = st.empty()

# Controles
col1, col2, col3 = st.columns([1,1,1])
with col1:
    max_rows = st.number_input("Filas a mostrar", 50, 5000, 200, step=50)
with col2:
    refresh_ms = st.slider("Refresco (ms)", 200, 2000, 700, step=100)
with col3:
    st.caption(f"Tópico: `{TOPIC}` · Bootstrap: `{BOOTSTRAP}`")

# Loop UI (simple)
last_render = 0
while True:
    try:
        # Drenar cola rápido
        drained = 0
        while not Q.empty() and drained < 2000:
            payload = Q.get_nowait()
            ts = payload.get("ts", time.time())
            pred = payload.get("prediction")
            feats = payload.get("features", {})
            row = {
                "ts": ts,
                "prediction": pred,
                **{f"feat_{k}": v for k, v in feats.items()}
            }
            buf.append(row)
            drained += 1
        # Recortar buffer
        if len(buf) > 10000:
            buf = buf[-5000:]

        now = time.time()
        if now - last_render >= (refresh_ms / 1000.0) and buf:
            df = pd.DataFrame(buf)
            # Ordenar por ts
            df = df.sort_values("ts")
            # Mostrar tabla
            table_ph.dataframe(df.tail(max_rows), use_container_width=True)

            # Gráfico simple
            dd = df.tail(max_rows)[["ts", "prediction"]].copy()
            dd["ts"] = pd.to_datetime(dd["ts"], unit="s")
            chart_ph.line_chart(dd.set_index("ts"))

            # Stats
            stats_ph.write(f"Total puntos: **{len(df)}** · Última pred: **{df.iloc[-1]['prediction']:.4f}**")

            last_render = now

        time.sleep(0.05)
    except KeyboardInterrupt:
        break
    except Exception:
        time.sleep(0.2)
