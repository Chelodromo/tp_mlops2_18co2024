import os, json, time
from confluent_kafka import Consumer, Producer, KafkaException

bootstrap = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
topic_in = os.getenv("KAFKA_TOPIC_IN", "features")
topic_out = os.getenv("KAFKA_TOPIC_OUT", "predictions")
group_id = os.getenv("GROUP_ID", "smoke-consumer")

c = Consumer({
    "bootstrap.servers": bootstrap,
    "group.id": group_id,
    "auto.offset.reset": "earliest",
})
p = Producer({"bootstrap.servers": bootstrap})
c.subscribe([topic_in])

print(f"[smoke] consuming {topic_in} -> producing {topic_out}")
try:
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())
        payload = json.loads(msg.value().decode("utf-8"))
        # “predicción” dummy (ej: combinación simple)
        pred = 0.1*payload.get("TempOut",0) + 0.05*payload.get("WSpeed",0) - 0.02*payload.get("Rain",0)
        out = {"ts": payload.get("ts", time.time()), "features": payload, "prediction": float(pred)}
        p.produce(topic_out, json.dumps(out).encode("utf-8"))
        p.poll(0)
except KeyboardInterrupt:
    pass
finally:
    c.close()
