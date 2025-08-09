import time
import json
import random
from kafka import KafkaProducer
from datetime import datetime

def serialize_json(obj):
    """Serializar objeto a JSON"""
    return json.dumps(obj).encode('utf-8')

def kafka_producer_sensor_data():
    """
    Productor de Kafka que genera y envía datos de sensores meteorológicos
    para predicción de polvo atmosférico
    """
    
    # Configuración del productor Kafka
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],  # URL interna de Kafka en Docker
        value_serializer=serialize_json
    )

    topic_name = 'weather_data_input'
    
    print(f"🌊 Iniciando productor Kafka - Enviando datos al tópico: {topic_name}")
    print("=" * 60)

    try:
        # Generar 50 eventos de datos meteorológicos
        for i in range(50):
            # Generar datos meteorológicos realistas
            sensor_id = random.randint(1, 5)
            temperature = round(random.uniform(15.0, 35.0), 1)  # TempOut
            dew_point = round(random.uniform(-5.0, 25.0), 1)    # DewPt_
            wind_speed = round(random.uniform(0.0, 30.0), 1)    # WSpeed
            wind_high_speed = round(random.uniform(5.0, 50.0), 1)  # WHSpeed
            pressure = round(random.uniform(1000.0, 1030.0), 1)  # Bar
            rain = round(random.uniform(0.0, 10.0), 1)          # Rain
            et = round(random.uniform(0.0, 8.0), 1)             # ET
            wind_direction = round(random.uniform(0.0, 360.0), 1)  # WDir_deg
            timestamp = time.time()  # Date_num

            # Crear payload con el formato esperado por el modelo
            data = {
                "sensor_id": sensor_id,
                "TempOut": temperature,
                "DewPt_": dew_point,
                "WSpeed": wind_speed,
                "WHSpeed": wind_high_speed,
                "Bar": pressure,
                "Rain": rain,
                "ET": et,
                "WDir_deg": wind_direction,
                "Date_num": timestamp,
                "timestamp": datetime.now().isoformat(),
                "batch_id": f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }

            # Enviar datos a Kafka
            producer.send(topic_name, value=data)
            print(f"📤 Evento {i+1}/50 enviado: Sensor {sensor_id} - Temp: {temperature}°C, Viento: {wind_speed} km/h")
            
            # Pausa entre eventos
            time.sleep(2)  # Enviar un evento cada 2 segundos

        print("=" * 60)
        print(f"✅ Productor completado - {50} eventos enviados al tópico {topic_name}")

    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo productor...")
    except Exception as e:
        print(f"❌ Error en el productor: {e}")
    finally:
        producer.close()
        print("🔒 Productor cerrado.")
        
    return {"status": "success", "events_sent": 50, "topic": topic_name}

def kafka_producer_test_connection():
    """
    Función de prueba para verificar la conexión a Kafka
    """
    try:
        producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=serialize_json
        )
        
        # Enviar mensaje de prueba
        test_data = {
            "test": True,
            "message": "Conexión de prueba exitosa",
            "timestamp": datetime.now().isoformat()
        }
        
        producer.send('weather_data_input', value=test_data)
        producer.flush()
        producer.close()
        
        print("✅ Conexión a Kafka exitosa")
        return {"status": "success", "message": "Conexión verificada"}
        
    except Exception as e:
        print(f"❌ Error conectando a Kafka: {e}")
        return {"status": "error", "message": str(e)}
