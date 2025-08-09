#!/usr/bin/env python3
"""
Script de prueba para el sistema completo de streaming
"""

import json
import time
import requests
from kafka import KafkaProducer, KafkaConsumer
import random
from datetime import datetime

def test_fastapi():
    """Probar FastAPI"""
    print("🔍 Probando FastAPI...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI está funcionando")
            return True
        else:
            print(f"❌ FastAPI respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando a FastAPI: {e}")
        return False

def test_kafka_connection():
    """Probar conexión a Kafka"""
    print("🔍 Probando conexión a Kafka...")
    
    try:
        producer = KafkaProducer(
            bootstrap_servers="localhost:9094",
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        producer.close()
        print("✅ Kafka está accesible")
        return True
    except Exception as e:
        print(f"❌ Error conectando a Kafka: {e}")
        return False

def test_streamlit():
    """Probar Streamlit"""
    print("🔍 Probando Streamlit...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit está funcionando")
            return True
        else:
            print(f"❌ Streamlit respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando a Streamlit: {e}")
        return False

def test_prediction():
    """Probar predicción"""
    print("🔍 Probando predicción...")
    
    payload = {
        "TempOut": 25.0,
        "DewPt_": 15.0,
        "WSpeed": 10.0,
        "WHSpeed": 20.0,
        "Bar": 1013.0,
        "Rain": 0.0,
        "ET": 2.0,
        "WDir_deg": 180.0,
        "Date_num": time.time()
    }
    
    try:
        response = requests.post("http://localhost:8000/predict", json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            probability = result.get('probability', [0])[0]
            print(f"✅ Predicción exitosa: {probability:.2%}")
            return True
        else:
            print(f"❌ Error en predicción: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en predicción: {e}")
        return False

def test_kafka_streaming():
    """Probar streaming completo con Kafka"""
    print("🔍 Probando streaming completo con Kafka...")
    
    try:
        # Productor
        producer = KafkaProducer(
            bootstrap_servers="localhost:9094",
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        # Consumidor
        consumer = KafkaConsumer(
            "weather_data_input",
            bootstrap_servers="localhost:9094",
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='test_streaming_consumer'
        )
        
        # Enviar 5 mensajes de prueba
        print("📤 Enviando mensajes de prueba...")
        for i in range(5):
            test_data = {
                "sensor_id": random.randint(1, 5),
                "TempOut": round(random.uniform(15, 30), 1),
                "DewPt_": round(random.uniform(-5, 20), 1),
                "WSpeed": round(random.uniform(0, 25), 1),
                "WHSpeed": round(random.uniform(5, 40), 1),
                "Bar": round(random.uniform(1000, 1030), 1),
                "Rain": round(random.uniform(0, 5), 1),
                "ET": round(random.uniform(0, 8), 1),
                "WDir_deg": round(random.uniform(0, 360), 1),
                "Date_num": time.time(),
                "timestamp": datetime.now().isoformat(),
                "batch_id": f"test_streaming_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            producer.send("weather_data_input", value=test_data)
            print(f"  📨 Mensaje {i+1}/5 enviado")
            time.sleep(1)
        
        producer.flush()
        print("✅ Mensajes enviados")
        
        # Esperar y leer mensajes
        print("📥 Leyendo mensajes...")
        messages_received = 0
        start_time = time.time()
        
        while messages_received < 5 and (time.time() - start_time) < 30:
            message_batch = consumer.poll(timeout=1.0)
            
            for tp, records in message_batch.items():
                for record in records:
                    data = record.value
                    print(f"  📨 Mensaje recibido: Sensor {data.get('sensor_id')} - Temp: {data.get('TempOut')}°C")
                    messages_received += 1
        
        producer.close()
        consumer.close()
        
        if messages_received >= 5:
            print(f"✅ Streaming exitoso: {messages_received} mensajes procesados")
            return True
        else:
            print(f"❌ Solo se recibieron {messages_received}/5 mensajes")
            return False
            
    except Exception as e:
        print(f"❌ Error en streaming: {e}")
        return False

def test_end_to_end():
    """Prueba end-to-end completa"""
    print("🚀 Iniciando prueba end-to-end del sistema de streaming...")
    print("=" * 60)
    
    tests = [
        ("FastAPI", test_fastapi),
        ("Kafka", test_kafka_connection),
        ("Streamlit", test_streamlit),
        ("Predicción", test_prediction),
        ("Streaming Kafka", test_kafka_streaming)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está funcionando correctamente.")
        print("\n🌊 Para usar el streaming:")
        print("1. Ejecuta el DAG en Airflow: flujo_completo_prediccion_polvo")
        print("2. Ve a Streamlit: http://localhost:8501")
        print("3. Selecciona 'Streaming' y habilita el streaming")
        print("4. ¡Ve las predicciones en tiempo real!")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los logs y la configuración.")
    
    print("\n🌐 URLs de acceso:")
    print("- Streamlit: http://localhost:8501")
    print("- Kafka UI: http://localhost:8081")
    print("- FastAPI: http://localhost:8000")
    print("- Airflow: http://localhost:8080")

if __name__ == "__main__":
    test_end_to_end()
