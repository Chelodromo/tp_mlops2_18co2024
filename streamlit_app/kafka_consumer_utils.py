import json
import time
import requests
from kafka import KafkaConsumer
from datetime import datetime
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
INPUT_TOPIC = "weather_data_input"
FASTAPI_URL = "http://fastapi_app:8000"

class KafkaStreamProcessor:
    def __init__(self):
        self.consumer = None
        self.setup_consumer()
    
    def setup_consumer(self):
        """Configurar consumidor de Kafka"""
        try:
            self.consumer = KafkaConsumer(
                INPUT_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='streamlit_consumer'
            )
            logger.info("✅ Consumidor Kafka configurado correctamente")
        except Exception as e:
            logger.error(f"❌ Error configurando consumidor Kafka: {e}")
            raise
    
    def process_weather_data(self, weather_data):
        """Procesar datos meteorológicos y obtener predicción"""
        try:
            # Preparar payload para FastAPI
            payload = {
                "TempOut": weather_data.get("TempOut", 0),
                "DewPt": weather_data.get("DewPt", weather_data.get("DewPt_", 0)),  # Compatibilidad con ambos nombres
                "WSpeed": weather_data.get("WSpeed", 0),
                "WHSpeed": weather_data.get("WHSpeed", 0),
                "Bar": weather_data.get("Bar", 1013),
                "Rain": weather_data.get("Rain", 0),
                "ET": weather_data.get("ET", 0),
                "WDir_deg": weather_data.get("WDir_deg", 180),
                "Date_num": weather_data.get("Date_num", time.time())
            }
            
            # Hacer predicción
            response = requests.post(f"{FASTAPI_URL}/predict", json=payload, timeout=10)
            
            if response.status_code == 200:
                prediction = response.json()
                
                # Crear mensaje de salida
                output_message = {
                    "timestamp": datetime.now().isoformat(),
                    "sensor_id": weather_data.get("sensor_id", "N/A"),
                    "input_data": weather_data,
                    "prediction": prediction,
                    "probability": prediction.get("probability", [0])[0],
                    "status": "success"
                }
                
                return output_message
            else:
                logger.error(f"Error en predicción: {response.status_code} - {response.text}")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "sensor_id": weather_data.get("sensor_id", "N/A"),
                    "input_data": weather_data,
                    "prediction": None,
                    "probability": 0,
                    "status": "error",
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "sensor_id": weather_data.get("sensor_id", "N/A"),
                "input_data": weather_data,
                "prediction": None,
                "probability": 0,
                "status": "error",
                "error": str(e)
            }
    
    def get_latest_messages(self, max_messages=10):
        """Obtener los últimos mensajes de Kafka"""
        messages = []
        try:
            # Poll para obtener mensajes
            message_batch = self.consumer.poll(timeout=1.0, max_records=max_messages)
            
            for tp, records in message_batch.items():
                for record in records:
                    weather_data = record.value
                    prediction_result = self.process_weather_data(weather_data)
                    messages.append(prediction_result)
            
            return messages
        except Exception as e:
            logger.error(f"Error obteniendo mensajes: {e}")
            return []
    
    def close(self):
        """Cerrar consumidor"""
        if self.consumer:
            self.consumer.close()
            logger.info("🔒 Consumidor Kafka cerrado")

def test_kafka_connection():
    """Probar conexión a Kafka"""
    try:
        consumer = KafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='test_consumer'
        )
        consumer.close()
        return {"status": "success", "message": "Conexión a Kafka exitosa"}
    except Exception as e:
        return {"status": "error", "message": f"Error conectando a Kafka: {e}"}
