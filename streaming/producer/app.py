import os, json, time, math, random
import numpy as np
from confluent_kafka import Producer

bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
topic = os.getenv("KAFKA_TOPIC_IN", "features")
rate = float(os.getenv("EVENT_RATE_PER_SEC", "2"))
seed = os.getenv("SEED")
if seed is not None:
    try:
        seed = int(seed); random.seed(seed); np.random.seed(seed)
    except Exception:
        pass
interval = 1.0 / max(rate, 0.1)
p = Producer({"bootstrap.servers": bootstrap})

def clip(v, lo, hi): return max(lo, min(hi, v))
def rU(a,b): return float(np.random.uniform(a,b))
def rN(m,s): return float(np.random.normal(m,s))

def sample_event():
    base_temp = rN(18,6); TempOut = clip(base_temp, -5, 45)
    DewPt = clip(min(rN(TempOut - rU(0,8), 2.0), TempOut), -10, 30)
    WSpeed = clip(abs(rN(12,6)), 0, 80)
    WHSpeed = clip(max(WSpeed + rU(0,20), WSpeed), 0, 120)
    Bar = clip(rN(1013,12), 970, 1045)
    Rain = clip(abs(rN(1.2,2.0)), 0, 30) if np.random.rand() < 0.15 else 0.0
    t = time.time()
    day_phase = 0.5 + 0.5 * math.sin((t % 86400) / 86400 * 2 * math.pi - math.pi/2)
    ET = clip(0.002 * max(TempOut, 0) * (1 + 0.01 * WSpeed) * day_phase, 0, 8)
    WDir_deg = float(np.random.uniform(0,360)); 
    if WDir_deg == 360: WDir_deg = 0.0
    return {
        "TempOut": round(TempOut,3),
        "DewPt": round(DewPt,3),
        "WSpeed": round(WSpeed,3),
        "WHSpeed": round(WHSpeed,3),
        "Bar": round(Bar,3),
        "Rain": round(Rain,3),
        "ET": round(ET,3),
        "WDir_deg": round(WDir_deg,1),
        "Date_num": t,  # <--- IMPORTANTE
        "ts": t
    }

print(f"[producer] -> {topic} @ ~{rate} ev/s (bootstrap={bootstrap})")
while True:
    payload = sample_event()
    p.produce(topic, json.dumps(payload).encode("utf-8"))
    p.poll(0)
    time.sleep(interval)
