# 🌊 DAG con Productor Kafka - Predicción de Polvo Atmosférico

## 📋 Descripción

Se ha agregado un nuevo DAG que incluye un productor de Kafka entre las tareas "recargar_modelo_api" y "predict_actual". Este productor genera datos meteorológicos simulados y los envía a Kafka para procesamiento en tiempo real.

## 🏗️ Arquitectura del DAG

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Seleccionar     │───▶│ Recargar        │───▶│ Test Kafka      │───▶│ Productor       │
│ Mejor Modelo    │    │ Modelo API      │    │ Connection      │    │ Kafka           │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Predict Datos   │◀───│                 │    │                 │    │ Tópico:         │
│ Actuales        │    │                 │    │                 │    │ weather_data_   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    │ input           │
                                                                      └─────────────────┘
```

## 🚀 Nuevas Tareas Agregadas

### 1. **test_kafka_connection**
- **Función**: `kafka_producer_test_connection()`
- **Propósito**: Verificar la conexión a Kafka antes de enviar datos
- **Ubicación**: Entre `recargar_modelo_api` y `kafka_producer_task`

### 2. **kafka_producer_sensor_data**
- **Función**: `kafka_producer_sensor_data()`
- **Propósito**: Generar y enviar 50 eventos de datos meteorológicos a Kafka
- **Ubicación**: Entre `test_kafka_connection` y `predict_actual`

## 📊 Datos Generados

El productor genera datos meteorológicos con el siguiente formato:

```json
{
    "sensor_id": 1-5,
    "TempOut": 15.0-35.0,
    "DewPt_": -5.0-25.0,
    "WSpeed": 0.0-30.0,
    "WHSpeed": 5.0-50.0,
    "Bar": 1000.0-1030.0,
    "Rain": 0.0-10.0,
    "ET": 0.0-8.0,
    "WDir_deg": 0.0-360.0,
    "Date_num": timestamp,
    "timestamp": "2024-01-01T12:00:00",
    "batch_id": "batch_20240101_120000"
}
```

## 🛠️ Configuración

### 1. **Servicios Kafka Agregados**
- **Zookeeper**: Puerto 2181
- **Kafka**: Puertos 9092 (interno) y 9094 (externo)
- **Kafka UI**: Puerto 8081

### 2. **Dependencias Agregadas**
```bash
kafka-python
confluent-kafka
```

### 3. **Tópico de Kafka**
- **Nombre**: `weather_data_input`
- **Configuración**: Auto-creación habilitado
- **Replicación**: Factor 1 (desarrollo)

## 🚀 Instalación y Uso

### 1. **Ejecutar el sistema completo**
```bash
docker-compose up -d
```

### 2. **Verificar servicios**
```bash
docker-compose ps
```

### 3. **Acceder a Airflow**
- URL: http://localhost:8080
- Usuario: airflow
- Contraseña: airflow

### 4. **Ejecutar el DAG**
- Buscar: `flujo_completo_prediccion_polvo`
- Hacer clic en "Trigger DAG"

## 📈 Monitoreo

### 1. **Kafka UI**
- URL: http://localhost:8081
- Ver tópicos y mensajes en tiempo real
- Monitorear throughput

### 2. **Logs de Airflow**
```bash
# Ver logs de la tarea Kafka
docker-compose logs airflow-webserver | grep kafka

# Ver logs específicos
docker-compose logs airflow-scheduler
```

### 3. **Verificar Mensajes**
En Kafka UI, buscar el tópico `weather_data_input` para ver los mensajes enviados.

## 🧪 Pruebas

### 1. **Script de Prueba**
```bash
python test_kafka_producer.py
```

### 2. **Verificación Manual**
1. Ejecutar el DAG en Airflow
2. Verificar logs de las tareas Kafka
3. Revisar mensajes en Kafka UI
4. Confirmar que `predict_actual` se ejecuta correctamente

## 🔄 Flujo Completo

1. **Entrenamiento**: Se entrenan múltiples modelos
2. **Selección**: Se selecciona el mejor modelo
3. **Recarga**: Se recarga el modelo en la API
4. **Test Kafka**: Se verifica la conexión a Kafka
5. **Productor**: Se envían 50 eventos meteorológicos
6. **Predicción**: Se procesan los datos actuales
7. **Test Endpoints**: Se prueban los endpoints de la API

## 📊 Métricas del Productor

- **Eventos por ejecución**: 50
- **Intervalo entre eventos**: 2 segundos
- **Duración total**: ~100 segundos
- **Sensores simulados**: 5
- **Variables meteorológicas**: 9

## 🐛 Troubleshooting

### Problemas Comunes:

1. **Kafka no conecta**
   ```bash
   docker-compose restart kafka zookeeper
   ```

2. **Tópico no existe**
   - Kafka auto-crea tópicos
   - Verificar en Kafka UI: http://localhost:8081

3. **DAG falla en tarea Kafka**
   - Verificar logs de Airflow
   - Confirmar que Kafka esté ejecutándose

### Verificar Estado:
```bash
# Estado de Kafka
docker-compose ps | grep kafka

# Logs de Kafka
docker-compose logs kafka

# Logs de Zookeeper
docker-compose logs zookeeper
```

## 📝 Ejemplo de Logs

### Tarea test_kafka_connection:
```
✅ Conexión a Kafka exitosa
```

### Tarea kafka_producer_sensor_data:
```
🌊 Iniciando productor Kafka - Enviando datos al tópico: weather_data_input
============================================================
📤 Evento 1/50 enviado: Sensor 3 - Temp: 25.3°C, Viento: 12.7 km/h
📤 Evento 2/50 enviado: Sensor 1 - Temp: 18.9°C, Viento: 8.2 km/h
...
============================================================
✅ Productor completado - 50 eventos enviados al tópico weather_data_input
🔒 Productor cerrado.
```

## 🌐 URLs de Acceso

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Airflow** | http://localhost:8080 | Orquestación de workflows |
| **Kafka UI** | http://localhost:8081 | Monitoreo de Kafka |
| **FastAPI** | http://localhost:8000 | API de predicción |
| **Streamlit** | http://localhost:8501 | Interfaz de usuario |

---

**🎯 Sistema de Predicción de Polvo Atmosférico - MLOps II**
*DAG con Productor Kafka Integrado*
