# fastapi_app/graphql_app.py

import strawberry
from strawberry.fastapi import GraphQLRouter
from fastapi import FastAPI
import pandas as pd
import boto3
import tempfile
import os
import pickle
from typing import List, Optional
from datetime import datetime
from sklearn.base import BaseEstimator

# ============================================================================
# CONFIGURACIÓN (igual que tu app.py original)
# ============================================================================

# Configuración de MinIO
MINIO_ENDPOINT   = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minio_admin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minio_admin')
BUCKET_NAME      = "respaldo2"
PREFIX           = "modelos/"

# Variables globales
model: Optional[BaseEstimator] = None
model_timestamp: Optional[str] = None
expected_features: List[str] = []

# ============================================================================
# TIPOS DE DATOS GRAPHQL
# ============================================================================

@strawberry.input
class WeatherData:
    """Datos meteorológicos para predicción"""
    TempOut: float = strawberry.field(description="Temperatura exterior")
    DewPt: float = strawberry.field(description="Punto de rocío")
    WSpeed: float = strawberry.field(description="Velocidad del viento")
    WHSpeed: float = strawberry.field(description="Velocidad máxima del viento")
    Bar: float = strawberry.field(description="Presión barométrica")
    Rain: float = strawberry.field(description="Lluvia")
    ET: float = strawberry.field(description="Evapotranspiración")
    WDir_deg: float = strawberry.field(description="Dirección del viento en grados")
    Date_num: float = strawberry.field(description="Fecha en formato numérico")

@strawberry.type
class PredictionResult:
    """Resultado de una predicción individual"""
    probability: float = strawberry.field(description="Probabilidad de polvo")

@strawberry.type
class BatchPredictionItem:
    """Elemento de predicción en lote"""
    date: str = strawberry.field(description="Fecha formateada")
    probability: float = strawberry.field(description="Probabilidad de polvo")

@strawberry.type
class BatchPredictionResult:
    """Resultado de predicciones en lote"""
    predictions: List[BatchPredictionItem] = strawberry.field(description="Lista de predicciones")

@strawberry.type
class ModelInfo:
    """Información del modelo cargado"""
    timestamp: str = strawberry.field(description="Timestamp del modelo")
    features: List[str] = strawberry.field(description="Features esperadas por el modelo")
    is_loaded: bool = strawberry.field(description="Si el modelo está cargado")

@strawberry.type
class ReloadResult:
    """Resultado de recargar el modelo"""
    status: str = strawberry.field(description="Estado de la operación")

# ============================================================================
# FUNCIONES DE UTILIDAD (adaptadas de tu app.py original)
# ============================================================================

def load_latest_model():
    """Carga el modelo más reciente desde MinIO"""
    global model, model_timestamp, expected_features

    s3 = boto3.client(
        's3',
        endpoint_url=f'http://{MINIO_ENDPOINT}',
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY
    )
    
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PREFIX)
        files = [o['Key'] for o in resp.get('Contents', []) if o['Key'].endswith('.pkl')]
        
        if not files:
            print("⚠️ No se encontraron modelos en MinIO.")
            return False

        latest = sorted(files)[-1]
        latest_ts = latest.split("/")[-1].split(".")[0]
        
        if latest_ts == model_timestamp:
            return True  # Ya tenemos cargado el más reciente

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = os.path.join(tmpdir, os.path.basename(latest))
            s3.download_file(BUCKET_NAME, latest, tmp_path)
            with open(tmp_path, 'rb') as f:
                model = pickle.load(f)
                model_timestamp = latest_ts

        # Capturamos las features
        if hasattr(model, 'feature_names_in_'):
            expected_features = list(model.feature_names_in_)

        print(f"✅ Modelo cargado: {latest}")
        print(f"🔧 Features esperadas: {expected_features}")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return False

def lazy_load_model_if_needed():
    """Carga el modelo si no está cargado"""
    if model is None:
        load_latest_model()

def align_and_order(df: pd.DataFrame) -> pd.DataFrame:
    """Alinea y ordena las columnas según las features esperadas"""
    df2 = df.copy()
    for feat in expected_features:
        if feat not in df2.columns:
            for col in df2.columns:
                if col.rstrip('.') == feat.rstrip('.'):
                    df2.rename(columns={col: feat}, inplace=True)
                    break
    return df2[expected_features]

def predict_proba_model(m: BaseEstimator, df: pd.DataFrame) -> pd.Series:
    """Realiza predicciones de probabilidad"""
    probs = m.predict_proba(df)
    return pd.Series(probs[:, 1], index=df.index)

def weather_data_to_dict(weather: WeatherData) -> dict:
    """Convierte WeatherData a diccionario"""
    return {
        'TempOut': weather.TempOut,
        'DewPt': weather.DewPt,
        'WSpeed': weather.WSpeed,
        'WHSpeed': weather.WHSpeed,
        'Bar': weather.Bar,
        'Rain': weather.Rain,
        'ET': weather.ET,
        'WDir_deg': weather.WDir_deg,
        'Date_num': weather.Date_num
    }

# ============================================================================
# RESOLVERS GRAPHQL
# ============================================================================

@strawberry.type
class Query:
    """Queries GraphQL"""
    
    @strawberry.field(description="Obtiene información del modelo actual")
    def model_info(self) -> ModelInfo:
        lazy_load_model_if_needed()
        return ModelInfo(
            timestamp=model_timestamp or "No cargado",
            features=expected_features,
            is_loaded=model is not None
        )

@strawberry.type
class Mutation:
    """Mutations GraphQL"""
    
    @strawberry.mutation(description="Recarga el modelo desde MinIO")
    def reload_model(self) -> ReloadResult:
        success = load_latest_model()
        status = "🔁 Modelo recargado exitosamente" if success else "❌ Error recargando modelo"
        return ReloadResult(status=status)
    
    @strawberry.mutation(description="Realiza una predicción individual")
    def predict(self, weather_data: WeatherData) -> PredictionResult:
        lazy_load_model_if_needed()
        
        if model is None:
            raise Exception("No hay modelo cargado")
        
        df = pd.DataFrame([weather_data_to_dict(weather_data)])
        df_aligned = align_and_order(df)
        proba = predict_proba_model(model, df_aligned)
        
        return PredictionResult(
            probability=round(float(proba.iloc[0]), 4)
        )
    
    @strawberry.mutation(description="Realiza predicciones en lote")
    def predict_batch(self, weather_data_list: List[WeatherData]) -> BatchPredictionResult:
        lazy_load_model_if_needed()
        
        if model is None:
            raise Exception("No hay modelo cargado")
        
        df = pd.DataFrame([weather_data_to_dict(w) for w in weather_data_list])
        df_aligned = align_and_order(df)
        proba = predict_proba_model(model, df_aligned)
        
        # Formatear fechas como en tu código original
        dates = df_aligned["Date_num"].apply(lambda ts: datetime.fromtimestamp(ts).strftime("%d-%m-%Y"))
        
        predictions = []
        for date, prob in zip(dates, proba):
            predictions.append(BatchPredictionItem(
                date=date,
                probability=round(float(prob), 4)
            ))
        
        return BatchPredictionResult(predictions=predictions)

# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================================

# Crear el schema GraphQL
schema = strawberry.Schema(query=Query, mutation=Mutation)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Weather Dust Prediction GraphQL API", 
    version="1.0.0",
    description="API GraphQL para predicción de polvo basada en datos meteorológicos"
)

# Agregar el router de GraphQL
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Endpoint de salud
@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "graphql_endpoint": "/graphql",
        "model_loaded": model is not None,
        "model_timestamp": model_timestamp
    }

# Endpoint para documentación GraphQL
@app.get("/")
def root():
    return {
        "message": "Weather Dust Prediction GraphQL API",
        "graphql_playground": "/graphql",
        "health_check": "/health",
        "model_status": {
            "loaded": model is not None,
            "timestamp": model_timestamp
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
