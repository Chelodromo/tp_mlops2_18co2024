import os
import tempfile
import pickle
import json
import time
from typing import List
import boto3
import pandas as pd
from confluent_kafka import Consumer, TopicPartition

# ======== MinIO (igual que Airflow) ========
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minio_admin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minio_admin')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'respaldo2')
PREFIX = os.getenv('PREFIX', 'best_model/')

# ======== Kafka ========
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC_IN = os.getenv("KAFKA_TOPIC_IN", "features")
READ_LAST_N = int(os.getenv("READ_LAST_N", "10"))

# 9 features exactas del modelo
FEATURE_ORDER: List[str] = [
    "TempOut","DewPt","WSpeed","WHSpeed","Bar","Rain","ET","WDir_deg","Date_num"
]

def load_latest_model_from_minio():
    """Carga el último modelo almacenado en MinIO (misma lógica que Airflow)."""
    s3 = boto3.client(
        's3',
        endpoint_url=f'http://{MINIO_ENDPOINT}',
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
    files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.pkl')]
    if not files:
        raise Exception("No se encontraron modelos en MinIO.")
    latest_file = sorted(files)[-1]
    print(f"📦 Último modelo encontrado: {latest_file}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = os.path.join(tmpdir, os.path.basename(latest_file))
        s3.download_file(BUCKET_NAME, latest_file, tmp_path)
        with open(tmp_path, 'rb') as f:
            model = pickle.load(f)
    return model

def tail_last_n_messages(topic: str, n: int):
    """
    Lee las últimas n entradas del tópico (asumiendo 1 partición: 0).
    Si tu topic tiene >1 partición, lo extendemos luego para agregarlas.
    """
    c = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": "model-test-tail",
        "enable.auto.commit": False,
        "auto.offset.reset": "latest",
    })
    try:
        # Partición 0
        tp0 = TopicPartition(topic, 0)
        # Necesitamos saber low y high para calcular el inicio
        lo, hi = c.get_watermark_offsets(tp0, timeout=5.0)
        if hi == lo:
            print("⚠️  Topic vacío.")
            return []

        start = max(lo, hi - n)
        # Asignamos consumo directo desde ese offset
        tp0.offset = start
        c.assign([tp0])

        msgs = []
        deadline = time.time() + 5.0  # hasta 5s para reunir mensajes
        while len(msgs) < n and time.time() < deadline:
            msg = c.poll(0.5)
            if msg is None:
                continue
            if msg.error():
                print(f"Kafka error: {msg.error()}")
                continue
            try:
                payload = json.loads(msg.value().decode("utf-8"))
                msgs.append(payload)
            except Exception as e:
                print(f"Mensaje inválido: {e}")
        return msgs
    finally:
        c.close()

def build_dataframe(samples: List[dict]) -> pd.DataFrame:
    """
    Arma un DataFrame con exclusivamente las 9 features (ignora 'ts').
    Rellena faltantes con 0.0 y castea a numérico.
    Devuelve el DF y también la lista de ts para referencia.
    """
    rows = []
    ts_list = []
    for s in samples:
        ts_list.append(s.get("ts"))
        feats = {k: s.get(k, 0.0) for k in FEATURE_ORDER}
        rows.append(feats)
    df = pd.DataFrame(rows, columns=FEATURE_ORDER)
    df = df.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    return df, ts_list

if __name__ == "__main__":
    # 1) Cargar modelo
    model = load_latest_model_from_minio()

    # 2) Leer últimas N muestras del tópico
    samples = tail_last_n_messages(KAFKA_TOPIC_IN, READ_LAST_N)
    if not samples:
        print("⚠️  No se pudieron leer mensajes recientes del tópico. ¿Está el data-producer enviando?")
        raise SystemExit(0)

    # 3) Armar DF de 9 features (y guardar ts por separado)
    df, ts_list = build_dataframe(samples)
    print(f"🧪 Tomadas {len(df)} muestras del tópico '{KAFKA_TOPIC_IN}'.")
    # 4) Predicción
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(df)[:, 1]
        for i, p in enumerate(proba):
            print(f"  #{i:02d} ts={ts_list[i]}  proba_pos={p:.6f}")
    else:
        pred = model.predict(df)
        for i, y in enumerate(pred):
            print(f"  #{i:02d} ts={ts_list[i]}  pred={float(y)}")
    print("✅ Test Kafka+MinIO OK.")
