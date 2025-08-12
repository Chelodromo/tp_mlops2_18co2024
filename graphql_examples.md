# Ejemplos de Consultas GraphQL

## 🚀 Cómo Usar

1. **Inicia la aplicación GraphQL:**
   ```bash
   cd fastapi_app
   uvicorn graphql_app:app --reload
   ```

2. **Accede al playground:**
   - URL: http://localhost:8000/graphql
   - El playground incluye autocompletado y documentación automática

3. **Ejecuta las consultas de ejemplo:**

## 📊 Queries (Consultas)

### 1. Obtener información del modelo
```graphql
query {
  modelInfo {
    timestamp
    features
    isLoaded
  }
}
```

**Respuesta esperada:**
```json
{
  "data": {
    "modelInfo": {
      "timestamp": "20241201_143022",
      "features": ["TempOut", "DewPt", "WSpeed", "WHSpeed", "Bar", "Rain", "ET", "WDir_deg", "Date_num"],
      "isLoaded": true
    }
  }
}
```

## 🔄 Mutations (Modificaciones)

### 2. Recargar el modelo
```graphql
mutation {
  reloadModel {
    status
  }
}
```

**Respuesta esperada:**
```json
{
  "data": {
    "reloadModel": {
      "status": "🔁 Modelo recargado exitosamente"
    }
  }
}
```

### 3. Predicción individual
```graphql
mutation {
  predict(weatherData: {
    TempOut: 25.5
    DewPt: 18.2
    WSpeed: 12.3
    WHSpeed: 15.7
    Bar: 1013.2
    Rain: 0.0
    ET: 3.2
    WDirDeg: 180.0
    DateNum: 1640995200.0
  }) {
    probability
  }
}
```

**Respuesta esperada:**
```json
{
  "data": {
    "predict": {
      "probability": 0.2345
    }
  }
}
```

### 4. Predicciones en lote
```graphql
mutation {
  predictBatch(weatherDataList: [
    {
      TempOut: 25.5
      DewPt: 18.2
      WSpeed: 12.3
      WHSpeed: 15.7
      Bar: 1013.2
      Rain: 0.0
      ET: 3.2
      WDirDeg: 180.0
      DateNum: 1640995200.0
    },
    {
      TempOut: 28.1
      DewPt: 20.5
      WSpeed: 8.9
      WHSpeed: 12.1
      Bar: 1010.8
      Rain: 0.0
      ET: 4.1
      WDirDeg: 225.0
      DateNum: 1641081600.0
    }
  ]) {
    predictions {
      date
      probability
    }
  }
}
```

**Respuesta esperada:**
```json
{
  "data": {
    "predictBatch": {
      "predictions": [
        {
          "date": "01-01-2022",
          "probability": 0.2345
        },
        {
          "date": "02-01-2022",
          "probability": 0.3456
        }
      ]
    }
  }
}
```

## 🔧 Consultas con Variables

### 5. Predicción con variables
```graphql
mutation PredictDust($weatherData: WeatherData!) {
  predict(weatherData: $weatherData) {
    probability
  }
}
```

**Variables:**
```json
{
  "weatherData": {
    "TempOut": 25.5,
    "DewPt": 18.2,
    "WSpeed": 12.3,
    "WHSpeed": 15.7,
    "Bar": 1013.2,
    "Rain": 0.0,
    "ET": 3.2,
    "WDir_deg": 180.0,
    "Date_num": 1640995200.0
  }
}
```

### 6. Predicciones en lote con variables
```graphql
mutation PredictBatch($weatherDataList: [WeatherData!]!) {
  predictBatch(weatherDataList: $weatherDataList) {
    predictions {
      date
      probability
    }
  }
}
```

**Variables:**
```json
{
  "weatherDataList": [
    {
      "TempOut": 25.5,
      "DewPt": 18.2,
      "WSpeed": 12.3,
      "WHSpeed": 15.7,
      "Bar": 1013.2,
      "Rain": 0.0,
      "ET": 3.2,
      "WDir_deg": 180.0,
      "Date_num": 1640995200.0
    },
    {
      "TempOut": 28.1,
      "DewPt": 20.5,
      "WSpeed": 8.9,
      "WHSpeed": 12.1,
      "Bar": 1010.8,
      "Rain": 0.0,
      "ET": 4.1,
      "WDir_deg": 225.0,
      "Date_num": 1641081600.0
    }
  ]
}
```

## 🎯 Casos de Uso Avanzados

### 7. Consulta selectiva (solo probabilidad)
```graphql
mutation {
  predict(weatherData: {
    TempOut: 25.5
    DewPt: 18.2
    WSpeed: 12.3
    WHSpeed: 15.7
    Bar: 1013.2
    Rain: 0.0
    ET: 3.2
    WDir_deg: 180.0
    Date_num: 1640995200.0
  }) {
    probability
    # date  # Comentado si no lo necesitas
  }
}
```

### 8. Múltiples operaciones en una sesión
```graphql
# Primero obtener información del modelo
query {
  modelInfo {
    timestamp
    isLoaded
  }
}

# Luego hacer una predicción
mutation {
  predict(weatherData: {
    TempOut: 25.5
    DewPt: 18.2
    WSpeed: 12.3
    WHSpeed: 15.7
    Bar: 1013.2
    Rain: 0.0
    ET: 3.2
    WDir_deg: 180.0
    Date_num: 1640995200.0
  }) {
    probability
  }
}
```

## 🚨 Manejo de Errores

### 9. Error con datos inválidos
```graphql
mutation {
  predict(weatherData: {
    TempOut: "invalid"  # Error: debe ser float
    DewPt: 18.2
    WSpeed: 12.3
    WHSpeed: 15.7
    Bar: 1013.2
    Rain: 0.0
    ET: 3.2
    WDir_deg: 180.0
    Date_num: 1640995200.0
  }) {
    probability
  }
}
```

**Respuesta esperada (error):**
```json
{
  "errors": [
    {
      "message": "Variable \"$weatherData\" got invalid value \"invalid\" at \"weatherData.TempOut\"; Float cannot represent non numeric value: \"invalid\"",
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ]
    }
  ]
}
```

## 🧪 Testing con cURL

### 10. Predicción individual con cURL
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "mutation { predict(weatherData: { TempOut: 25.5, DewPt: 18.2, WSpeed: 12.3, WHSpeed: 15.7, Bar: 1013.2, Rain: 0.0, ET: 3.2, WDir_deg: 180.0, Date_num: 1640995200.0 }) { probability } }"
  }'
```

### 11. Información del modelo con cURL
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { modelInfo { timestamp features isLoaded } }"
  }'
```

## 📈 Ventajas de GraphQL vs REST

### Comparación con tu API REST actual:

**REST API:**
```bash
POST /predict
{
  "TempOut": 25.5,
  "DewPt": 18.2,
  "WSpeed": 12.3,
  "WHSpeed": 15.7,
  "Bar": 1013.2,
  "Rain": 0.0,
  "ET": 3.2,
  "WDir_deg": 180.0,
  "Date_num": 1640995200.0
}
```

**GraphQL:**
```graphql
mutation {
  predict(weatherData: {
    TempOut: 25.5,
    DewPt: 18.2
    # Solo los campos que necesitas
  }) {
    probability  # Solo obtienes la probabilidad
    # date       # Comentado si no lo necesitas
  }
}
```

### ✅ Ventajas de GraphQL:
- **Over-fetching eliminado**: Solo obtienes los datos que necesitas
- **Under-fetching eliminado**: Una sola consulta puede obtener múltiples recursos
- **Schema autodocumentado**: Documentación automática y actualizada
- **Validación automática**: Errores detectados en tiempo de compilación
- **Flexibilidad**: Los clientes controlan exactamente qué datos reciben

## 🔍 Monitoreo

### 12. Health Check
```bash
curl http://localhost:8000/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "graphql_endpoint": "/graphql",
  "model_loaded": true,
  "model_timestamp": "20241201_143022"
}
```

---

**¡Usa estos ejemplos para probar tu API GraphQL! 🚀**
