# 🌊 Sistema Completo de Streaming con Kafka - Predicción de Polvo Atmosférico

## 📋 Descripción

Este sistema implementa un pipeline completo de streaming en tiempo real para la predicción de polvo atmosférico utilizando Apache Kafka. El flujo incluye:

1. **DAG de Airflow** que produce datos meteorológicos
2. **Streamlit** que consume y visualiza predicciones en tiempo real
3. **FastAPI** que procesa las predicciones del modelo ML

## 🏗️ Arquitectura Completa

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Airflow DAG   │───▶│     Kafka    │───▶│   Streamlit     │───▶│   FastAPI     │
│   (Productor)   │    │              │    │   (Consumidor)  │    │   (Modelo)    │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
   Genera datos           Tópico: weather_        Visualiza en        Predicciones
   meteorológicos         data_input             tiempo real          del modelo
```

## 🚀 Componentes del Sistema

### 1. **DAG de Airflow** (`dags/ml_dust_pred_dag.py`)
- **Productor Kafka**: Genera 50 eventos de datos meteorológicos
- **Flujo**: `recargar_modelo_api` → `test_kafka_connection` → `kafka_producer_task` → `predict_actual`
- **Tópico**: `weather_data_input`

### 2. **Streamlit** (`streamlit_app/app.py`)
- **Consumidor Kafka**: Lee datos del tópico `weather_data_input`
- **Procesamiento**: Envía datos a FastAPI para predicciones
- **Visualización**: Muestra predicciones en tiempo real
- **Modos**: Manual, Batch (CSV), Streaming

### 3. **FastAPI** (`fastapi_app/app.py`)
- **Modelo ML**: Procesa predicciones de polvo atmosférico
- **Endpoints**: `/predict` y `/predict_batch`
- **Integración**: Conecta con el modelo entrenado

### 4. **Kafka** (Docker Compose)
- **Zookeeper**: Coordinación del cluster
- **Kafka Broker**: Procesamiento de mensajes
- **Kafka UI**: Monitoreo (puerto 8081)

## 📊 Flujo de Datos

### 1. **Generación de Datos** (Airflow DAG)
```python
# El DAG genera datos como:
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

### 2. **Procesamiento** (Streamlit + FastAPI)
```python
# Streamlit consume y procesa:
1. Lee datos de Kafka
2. Envía a FastAPI para predicción
3. Recibe probabilidad de polvo
4. Visualiza en tiempo real
```

### 3. **Visualización** (Streamlit)
- Tabla de predicciones en tiempo real
- Gráfico de probabilidades
- Estadísticas (promedio, máximo, mínimo)
- Detalles de cada predicción

## 🛠️ Instalación y Configuración

### 1. **Crear archivo `.env`**
```bash
# Airflow Configuration
AIRFLOW_UID=50000

# Airflow Web UI credentials
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=airflow

# Additional PIP requirements for ML libraries
_PIP_ADDITIONAL_REQUIREMENTS=pandas pytest scikit-learn seaborn optuna lightgbm mlflow
```

### 2. **Ejecutar el sistema**
```bash
docker-compose up -d
```

### 3. **Verificar servicios**
```bash
docker-compose ps
```

## 🌐 URLs de Acceso

| Servicio | URL | Credenciales | Descripción |
|----------|-----|--------------|-------------|
| **Streamlit** | http://localhost:8501 | - | Interfaz de streaming |
| **Kafka UI** | http://localhost:8081 | - | Monitoreo de Kafka |
| **FastAPI** | http://localhost:8000 | - | API de predicción |
| **Airflow** | http://localhost:8080 | airflow/airflow | Orquestación |

## 📡 Uso del Sistema de Streaming

### 1. **Ejecutar el DAG Productor**
1. Ve a Airflow: http://localhost:8080
2. Busca: `flujo_completo_prediccion_polvo`
3. Haz clic en "Trigger DAG"
4. Espera a que se ejecute el productor Kafka

### 2. **Configurar Streamlit**
1. Ve a Streamlit: http://localhost:8501
2. Selecciona "Streaming"
3. Verifica conexión a Kafka
4. Habilita streaming

### 3. **Ver Predicciones en Tiempo Real**
- Los datos aparecen automáticamente
- Ve probabilidades en tiempo real
- Analiza gráficos y estadísticas
- Revisa detalles de cada predicción

## 🔧 Configuración del Streaming

### Parámetros Configurables:
- **Auto-refresh**: Actualización automática
- **Intervalo**: Frecuencia de refresh (1-10 segundos)
- **Máximo mensajes**: Límite en memoria (5-50)
- **Streaming activo**: Control manual

### Controles:
- **🚀 Iniciar Streaming**: Comienza a procesar datos
- **⏹️ Detener Streaming**: Pausa el procesamiento
- **🗑️ Limpiar Mensajes**: Borra datos en memoria

## 📈 Visualizaciones Disponibles

### 1. **Tabla de Predicciones**
- Timestamp de cada predicción
- ID del sensor
- Temperatura y velocidad del viento
- Probabilidad de polvo
- Estado de la predicción

### 2. **Gráfico de Probabilidades**
- Línea de tiempo de probabilidades
- Tendencias en tiempo real
- Identificación de picos

### 3. **Estadísticas en Tiempo Real**
- Total de mensajes procesados
- Promedio de probabilidades
- Valores máximo y mínimo

### 4. **Detalles de Predicciones**
- Datos de entrada completos
- Resultado de la predicción
- Barras de progreso
- Alertas según probabilidad

## 🧪 Pruebas del Sistema

### 1. **Script de Prueba Completo**
```bash
python test_streaming_system.py
```

### 2. **Prueba del Productor**
```bash
python test_kafka_producer.py
```

### 3. **Verificación Manual**
1. Ejecutar DAG en Airflow
2. Verificar mensajes en Kafka UI
3. Probar streaming en Streamlit
4. Confirmar predicciones

## 🔄 Flujo Completo de Ejecución

```
1. Airflow DAG → Entrena modelos y selecciona el mejor
2. DAG Productor → Genera 50 eventos meteorológicos
3. Kafka → Almacena datos en tópico weather_data_input
4. Streamlit → Consume datos de Kafka
5. FastAPI → Procesa predicciones del modelo
6. Streamlit → Visualiza resultados en tiempo real
```

## 📊 Métricas y Monitoreo

### Kafka UI (http://localhost:8081)
- **Tópicos**: Ver `weather_data_input`
- **Mensajes**: Monitorear throughput
- **Consumidores**: Ver grupos activos
- **Configuración**: Revisar cluster

### Logs de Docker
```bash
# Logs del productor (DAG)
docker-compose logs airflow-scheduler | grep kafka

# Logs de Streamlit
docker-compose logs streamlit_app

# Logs de Kafka
docker-compose logs kafka
```

## 🐛 Troubleshooting

### Problemas Comunes:

1. **No hay mensajes en Streamlit**
   - Verificar que el DAG se ejecutó correctamente
   - Revisar logs de Airflow
   - Confirmar conexión a Kafka

2. **Error de conexión a Kafka**
   ```bash
   docker-compose restart kafka zookeeper
   ```

3. **Streamlit no muestra datos**
   - Verificar que el streaming esté habilitado
   - Revisar logs de conexión
   - Confirmar que FastAPI esté funcionando

4. **DAG falla en tarea Kafka**
   - Verificar que Kafka esté ejecutándose
   - Revisar logs de Airflow
   - Confirmar dependencias instaladas

### Verificar Estado:
```bash
# Estado de todos los servicios
docker-compose ps

# Logs en tiempo real
docker-compose logs -f

# Verificar tópicos de Kafka
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```

## 📝 Ejemplo de Uso Completo

### 1. **Iniciar el sistema**
```bash
docker-compose up -d
```

### 2. **Ejecutar DAG productor**
- Airflow → `flujo_completo_prediccion_polvo` → Trigger DAG
- Esperar ejecución completa (~5-10 minutos)

### 3. **Configurar streaming**
- Streamlit → Seleccionar "Streaming"
- Habilitar streaming
- Configurar parámetros

### 4. **Ver predicciones**
- Los datos aparecen automáticamente
- Analizar gráficos y estadísticas
- Revisar detalles de predicciones

### 5. **Monitorear**
- Kafka UI → Ver tópicos y mensajes
- Logs → Verificar funcionamiento
- Métricas → Analizar rendimiento

## 🎯 Características Destacadas

- **⚡ Tiempo Real**: Predicciones instantáneas
- **📊 Visualización**: Gráficos y estadísticas en vivo
- **🔧 Configurable**: Parámetros ajustables
- **📈 Monitoreo**: Métricas y logs completos
- **🔄 Auto-refresh**: Actualización automática
- **🎨 Interfaz**: UI moderna y intuitiva

---

**🎯 Sistema de Predicción de Polvo Atmosférico - MLOps II**
*Sistema Completo de Streaming con Kafka*
