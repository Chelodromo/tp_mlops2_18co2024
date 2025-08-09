#!/usr/bin/env python3
"""
Script de prueba para el productor Kafka
"""

import time
import json
import random
from kafka import KafkaProducer
from datetime import datetime

def test_kafka_producer():
    """Probar el productor Kafka"""
    
    print("🚀 Iniciando prueba del productor Kafka...")
    print("=" * 50)
    
    try:
        # Configuración del productor Kafka
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9094'],  # Puerto expuesto por Docker
            value_serializer=lambda obj: json.dumps(obj).encode('utf-8')
        )

        topic_name = 'weather_data_input'
        
        print(f"📡 Conectando al tópico: {topic_name}")
        print(f"🌐 Servidor: localhost:9094")
        print("=" * 50)

        # Generar 10 eventos de prueba
        for i in range(10):
            # Generar datos meteorológicos realistas
            sensor_id = random.randint(1, 5)
            temperature = round(random.uniform(15.0, 35.0), 1)
            dew_point = round(random.uniform(-5.0, 25.0), 1)
            wind_speed = round(random.uniform(0.0, 30.0), 1)
            wind_high_speed = round(random.uniform(5.0, 50.0), 1)
            pressure = round(random.uniform(1000.0, 1030.0), 1)
            rain = round(random.uniform(0.0, 10.0), 1)
            et = round(random.uniform(0.0, 8.0), 1)
            wind_direction = round(random.uniform(0.0, 360.0), 1)
            timestamp = time.time()

            # Crear payload
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
                "batch_id": f"test_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }

            # Enviar datos a Kafka
            producer.send(topic_name, value=data)
            print(f"📤 Evento {i+1}/10: Sensor {sensor_id} - Temp: {temperature}°C, Viento: {wind_speed} km/h")
            
            # Pausa entre eventos
            time.sleep(1)

        print("=" * 50)
        print("✅ Prueba completada - 10 eventos enviados")
        
        # Cerrar productor
        producer.close()
        print("🔒 Productor cerrado")
        
        return True

    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        return False

if __name__ == "__main__":
    success = test_kafka_producer()
    if success:
        print("\n🎉 ¡Prueba exitosa! El productor Kafka está funcionando correctamente.")
        print("\n📊 Puedes verificar los mensajes en:")
        print("- Kafka UI: http://localhost:8081")
        print("- Tópico: weather_data_input")
    else:
        print("\n⚠️ La prueba falló. Verifica que Kafka esté ejecutándose.")
        print("Comando para iniciar: docker-compose up -d")
