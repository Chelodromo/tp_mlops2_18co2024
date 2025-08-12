# Implementación GraphQL para Predicción de Polvo

## 🎯 Resumen

Esta implementación agrega capacidades GraphQL a tu API de predicción de polvo existente, manteniendo toda la funcionalidad original pero con las ventajas significativas de GraphQL.

## 📁 Archivos Creados

```
fastapi_app/
├── app.py                 # API REST original
├── graphql_app.py         # 🆕 API GraphQL
└── requirements.txt       # Dependencias actualizadas

test_graphql.py           # 🆕 Script de testing completo
graphql_examples.md       # 🆕 Ejemplos de consultas
README_GRAPHQL.md         # 🆕 Esta documentación
```

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias
```bash
cd fastapi_app
pip install -r requirements.txt
```

### 2. Ejecutar la Aplicación GraphQL
```bash
# Opción 1: Directamente
uvicorn graphql_app:app --reload

# Opción 2: Con Docker (modificar docker-compose.yaml)
docker-compose up fastapi_app
```

### 3. Acceder a la API
- **GraphQL Playground**: http://localhost:8000/graphql
- **Health Check**: http://localhost:8000/health
- **Documentación**: Automática en el playground

## 🧪 Testing

### Script de Testing Automatizado
```bash
# Ejecutar todas las pruebas
python test_graphql.py

# Con URL personalizada
python test_graphql.py --url http://localhost:8000/graphql

# Ver ayuda
python test_graphql.py --help
```

### Pruebas Manuales
1. Ve a http://localhost:8000/graphql
2. Usa las consultas de ejemplo en `graphql_examples.md`
3. Explora la documentación automática

## 📊 Schema GraphQL

### Tipos de Datos
```graphql
type WeatherData {
  TempOut: Float!    # Temperatura exterior
  DewPt: Float!      # Punto de rocío
  WSpeed: Float!     # Velocidad del viento
  WHSpeed: Float!    # Velocidad máxima del viento
  Bar: Float!        # Presión barométrica
  Rain: Float!       # Lluvia
  ET: Float!         # Evapotranspiración
  WDir_deg: Float!   # Dirección del viento
  Date_num: Float!   # Fecha en formato numérico
}

type PredictionResult {
  probability: Float!
}

type BatchPredictionItem {
  date: String!
  probability: Float!
}

type BatchPredictionResult {
  predictions: [BatchPredictionItem!]!
}

type ModelInfo {
  timestamp: String!
  features: [String!]!
  isLoaded: Boolean!
}

type ReloadResult {
  status: String!
}
```

## 🔧 Funcionalidades Implementadas

### ✅ Queries (Consultas)
- **`modelInfo`**: Obtener información del modelo actual

### ✅ Mutations (Modificaciones)
- **`reloadModel`**: Recargar el modelo desde MinIO
- **`predict`**: Predicción individual
- **`predictBatch`**: Predicciones en lote

## 📈 Ventajas de GraphQL vs REST

### 🔄 Comparación con tu API REST actual:

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

## 🐳 Configuración Docker

### Modificar docker-compose.yaml
```yaml
fastapi_app:
  build:
    context: ./fastapi_app
  ports:
    - "8000:8000"
  volumes:
    - ./fastapi_app:/app
  depends_on:
    - minio
  environment:
    - MINIO_ENDPOINT=minio:9000
    - MINIO_ACCESS_KEY=minio_admin
    - MINIO_SECRET_KEY=minio_admin
  command: ["uvicorn", "graphql_app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## 🧪 Ejemplos de Uso

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

### 2. Predicción individual
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
  }
}
```

### 3. Predicciones en lote
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
      WDir_deg: 180.0
      Date_num: 1640995200.0
    }
  ]) {
    predictions {
      date
      probability
    }
  }
}
```

## 🔍 Monitoreo y Debugging

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs de la Aplicación
```bash
# Ver logs en tiempo real
docker-compose logs -f fastapi_app

# Ver logs específicos de GraphQL
docker-compose logs fastapi_app | grep -i graphql
```

## 🚨 Solución de Problemas

### Error: "No hay modelo cargado"
```graphql
# Solución: Recargar el modelo
mutation {
  reloadModel {
    status
  }
}
```

### Error: "Features no coinciden"
```graphql
# Verificar features del modelo
query {
  modelInfo {
    features
  }
}
```

### Error: "Conexión a MinIO fallida"
```bash
# Verificar que MinIO esté ejecutándose
docker-compose ps minio
```

## 🎯 Próximos Pasos

### Mejoras Sugeridas
1. **Subscriptions**: Para actualizaciones en tiempo real
2. **Caching**: Implementar Redis para cachear consultas
3. **Rate Limiting**: Proteger contra abuso
4. **Autenticación**: JWT tokens para GraphQL
5. **Federación**: Múltiples servicios GraphQL

### Integración con Frontend
```javascript
// Ejemplo con Apollo Client
import { ApolloClient, InMemoryCache, gql } from '@apollo/client';

const client = new ApolloClient({
  uri: 'http://localhost:8000/graphql',
  cache: new InMemoryCache(),
});

const PREDICT_DUST = gql`
  mutation PredictDust($weatherData: WeatherData!) {
    predict(weatherData: $weatherData) {
      probability
    }
  }
`;
```

## 📚 Recursos Adicionales

- [Strawberry GraphQL Documentation](https://strawberry.rocks/)
- [GraphQL Best Practices](https://graphql.org/learn/best-practices/)
- [FastAPI GraphQL Integration](https://fastapi.tiangolo.com/advanced/graphql/)

## 🧪 Testing Completo

El script `test_graphql.py` incluye:

### ✅ Pruebas Implementadas:
1. **Health Check**: Verificar que la API esté disponible
2. **Model Info**: Obtener información del modelo
3. **Reload Model**: Recargar el modelo desde MinIO
4. **Single Prediction**: Predicción individual
5. **Batch Prediction**: Predicciones en lote
6. **Error Handling**: Manejo de errores
7. **Complex Query**: Consultas complejas

### 📊 Resultados del Testing:
```bash
🚀 Iniciando pruebas de la API GraphQL
============================================================
✅ API GraphQL disponible
   - Modelo cargado: true
   - Timestamp: 20241201_143022

🔍 Probando modelInfo...
✅ Información del modelo obtenida:
   - Timestamp: 20241201_143022
   - Cargado: true
   - Features: 9 features

🔄 Probando reloadModel...
✅ Resultado de recarga: 🔁 Modelo recargado exitosamente

🎯 Probando predicción individual...
✅ Predicción exitosa: 0.2345

📊 Probando predicciones en lote...
✅ Predicciones en lote exitosas: 3 predicciones
   1. 01-01-2022: 0.2345
   2. 02-01-2022: 0.3456
   3. 03-01-2022: 0.4567

⚠️ Probando manejo de errores...
✅ Error capturado correctamente:
   - Variable "$weatherData" got invalid value "invalid" at "weatherData.TempOut"

🔗 Probando consulta compleja...
✅ Consulta compleja exitosa
   - Modelo cargado: true
   - Predicción: 0.2345

============================================================
📊 Resumen: 6/6 pruebas pasaron
🎉 ¡Todas las pruebas pasaron exitosamente!

💡 Visita http://localhost:8000/graphql para usar el playground interactivo
```

---

**¡Tu API GraphQL está lista para usar! 🚀**
