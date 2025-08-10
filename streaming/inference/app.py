import os, json, time, tempfile, pickle
from typing import List
import pandas as pd
import boto3

from confluent_kafka import Consumer, Producer, KafkaException
# ----- ENV
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP","kafka:9092")
TOPIC_IN  = os.getenv("KAFKA_TOPIC_IN","features")
GROUP_ID  = os.getenv("GROUP_ID","model-inference")
MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT","minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY","minio_admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY","minio_admin")
BUCKET_NAME      = os.getenv("BUCKET_NAME","respaldo2")
PREFIX           = os.getenv("PREFIX","best_model/")
MODEL_CHECK_INTERVAL_SEC = int(os.getenv("MODEL_CHECK_INTERVAL_SEC","30"))

FEATURE_ORDER: List[str] = ["TempOut","DewPt","WSpeed","WHSpeed","Bar","Rain","ET","WDir_deg","Date_num"]

# ----- Kafka
producer = Producer({"bootstrap.servers": BOOTSTRAP})
consumer = Consumer({
    "bootstrap.servers": BOOTSTRAP,
    "group.id": GROUP_ID,
    "auto.offset.reset": "earliest",
})

# ----- MinIO
s3 = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
)

_last_key = None
_last_load = 0.0
_model = None

def load_latest_model_from_minio():
    resp = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
    files = [obj["Key"] for obj in resp.get("Contents", []) if obj["Key"].endswith(".pkl")]
    if not files:
        raise RuntimeError(f"No hay .pkl en s3://{BUCKET_NAME}/{PREFIX}")
    latest = sorted(files)[-1]
    with tempfile.TemporaryDirectory() as tmp:
        local = os.path.join(tmp, os.path.basename(latest))
        s3.download_file(BUCKET_NAME, latest, local)
        with open(local,"rb") as f:
            m = pickle.load(f)
    return m, latest

def ensure_model():
    global _model, _last_key, _last_load
    now = time.time()
    if _model is not None and now - _last_load < MODEL_CHECK_INTERVAL_SEC:
        return
    try:
        m, key = load_latest_model_from_minio()
        if key != _last_key:
            print(f"[inference] Modelo cargado: {key}")
            _model, _last_key = m, key
        _last_load = now
    except Exception as e:
        print(f"[inference] Aviso: no se pudo cargar modelo ({e})")

def to_df(payload: dict) -> pd.DataFrame:
    row = {c: payload.get(c, 0.0) for c in FEATURE_ORDER}
    df = pd.DataFrame([row], columns=FEATURE_ORDER)
    return df.apply(pd.to_numeric, errors="coerce").fillna(0.0)

def predict_one(features: dict):
    ensure_model()
    if _model is None: return None
    df = to_df(features)
    if hasattr(_model,"predict_proba"):
        return float(_model.predict_proba(df)[:,1][0])
    return float(_model.predict(df)[0])

def main():
    consumer.subscribe([TOPIC_IN])
    print(f"[inference] escuchando {TOPIC_IN}")
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None: 
                continue
            if msg.error(): 
                raise KafkaException(msg.error())
            payload = json.loads(msg.value().decode("utf-8"))
            features = {k:v for k,v in payload.items() if k!="ts"}
            ts = payload.get("ts", time.time())
            y = predict_one(features)
            if y is None:
                continue
            # por ahora SOLO logueamos
            print(f"[inference] ts={ts} y={y:.6f} feats={{"
                  f"TempOut={features.get('TempOut')}, DewPt={features.get('DewPt')}, "
                  f"WSpeed={features.get('WSpeed')}, WHSpeed={features.get('WHSpeed')}, "
                  f"Bar={features.get('Bar')}, Rain={features.get('Rain')}, "
                  f"ET={features.get('ET')}, WDir_deg={features.get('WDir_deg')}, "
                  f"Date_num={features.get('Date_num')}}}")
            out = {"ts": ts, "features": features, "prediction": y}
            producer.produce(os.getenv("KAFKA_TOPIC_OUT", "predictions"),
                 json.dumps(out).encode("utf-8"))
            producer.poll(0)   # drena callbacks
            print(f"[inference] -> predictions  ts={ts} y={y:.6f}")
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
