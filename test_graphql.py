#!/usr/bin/env python3
"""
Script de testing para la API GraphQL de predicción de polvo
"""

import requests
import json
import time
from datetime import datetime
import sys

# Configuración
GRAPHQL_URL = "http://localhost:8001/graphql"
HEALTH_URL = "http://localhost:8001/health"

class GraphQLTester:
    def __init__(self, graphql_url=GRAPHQL_URL, health_url=HEALTH_URL):
        self.graphql_url = graphql_url
        self.health_url = health_url
        self.session = requests.Session()
    
    def execute_query(self, query, variables=None):
        """Ejecuta una consulta GraphQL"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        try:
            response = self.session.post(self.graphql_url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en la consulta: {e}")
            return None
    
    def check_health(self):
        """Verifica que la API esté disponible"""
        try:
            response = self.session.get(self.health_url, timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print("✅ API GraphQL disponible")
                print(f"   - Modelo cargado: {health_data.get('model_loaded', 'N/A')}")
                print(f"   - Timestamp: {health_data.get('model_timestamp', 'N/A')}")
                return True
            else:
                print(f"❌ API no disponible (status: {response.status_code})")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ No se puede conectar a la API: {e}")
            return False
    
    def test_model_info(self):
        """Prueba obtener información del modelo"""
        print("\n🔍 Probando modelInfo...")
        
        query = """
        query {
            modelInfo {
                timestamp
                features
                isLoaded
            }
        }
        """
        
        result = self.execute_query(query)
        if result and 'data' in result:
            model_info = result['data']['modelInfo']
            print("✅ Información del modelo obtenida:")
            print(f"   - Timestamp: {model_info['timestamp']}")
            print(f"   - Cargado: {model_info['isLoaded']}")
            print(f"   - Features: {len(model_info['features'])} features")
            return model_info
        else:
            print("❌ Error obteniendo información del modelo")
            if result and 'errors' in result:
                print(f"   Errores: {result['errors']}")
            return None
    
    def test_reload_model(self):
        """Prueba recargar el modelo"""
        print("\n🔄 Probando reloadModel...")
        
        query = """
        mutation {
            reloadModel {
                status
            }
        }
        """
        
        result = self.execute_query(query)
        if result and 'data' in result:
            reload_result = result['data']['reloadModel']
            print(f"✅ Resultado de recarga: {reload_result['status']}")
            return reload_result
        else:
            print("❌ Error recargando modelo")
            if result and 'errors' in result:
                print(f"   Errores: {result['errors']}")
            return None
    
    def test_single_prediction(self):
        """Prueba predicción individual"""
        print("\n🎯 Probando predicción individual...")
        
        # Datos de ejemplo
        weather_data = {
            "TempOut": 25.5,
            "DewPt": 18.2,
            "WSpeed": 12.3,
            "WHSpeed": 15.7,
            "Bar": 1013.2,
            "Rain": 0.0,
            "ET": 3.2,
            "WDir_deg": 180.0,
            "Date_num": time.time()
        }
        
        query = """
        mutation Predict($weatherData: WeatherData!) {
            predict(weatherData: $weatherData) {
                probability
            }
        }
        """
        
        result = self.execute_query(query, {"weatherData": weather_data})
        if result and 'data' in result:
            prediction = result['data']['predict']
            print(f"✅ Predicción exitosa: {prediction['probability']}")
            return prediction
        else:
            print("❌ Error en predicción individual")
            if result and 'errors' in result:
                print(f"   Errores: {result['errors']}")
            return None
    
    def test_batch_prediction(self):
        """Prueba predicciones en lote"""
        print("\n📊 Probando predicciones en lote...")
        
        # Datos de ejemplo para múltiples días
        weather_data_list = [
            {
                "TempOut": 25.5,
                "DewPt": 18.2,
                "WSpeed": 12.3,
                "WHSpeed": 15.7,
                "Bar": 1013.2,
                "Rain": 0.0,
                "ET": 3.2,
                "WDir_deg": 180.0,
                "Date_num": time.time()
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
                "Date_num": time.time() + 86400  # Un día después
            },
            {
                "TempOut": 22.3,
                "DewPt": 15.8,
                "WSpeed": 18.5,
                "WHSpeed": 22.0,
                "Bar": 1015.6,
                "Rain": 0.0,
                "ET": 2.8,
                "WDir_deg": 270.0,
                "Date_num": time.time() + 172800  # Dos días después
            }
        ]
        
        query = """
        mutation PredictBatch($weatherDataList: [WeatherData!]!) {
            predictBatch(weatherDataList: $weatherDataList) {
                predictions {
                    date
                    probability
                }
            }
        }
        """
        
        result = self.execute_query(query, {"weatherDataList": weather_data_list})
        if result and 'data' in result:
            batch_result = result['data']['predictBatch']
            predictions = batch_result['predictions']
            print(f"✅ Predicciones en lote exitosas: {len(predictions)} predicciones")
            for i, pred in enumerate(predictions):
                print(f"   {i+1}. {pred['date']}: {pred['probability']}")
            return batch_result
        else:
            print("❌ Error en predicciones en lote")
            if result and 'errors' in result:
                print(f"   Errores: {result['errors']}")
            return None
    
    def test_error_handling(self):
        """Prueba el manejo de errores"""
        print("\n⚠️ Probando manejo de errores...")
        
        # Consulta con datos inválidos
        query = """
        mutation {
            predict(weatherData: {
                TempOut: "invalid"
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
        """
        
        result = self.execute_query(query)
        if result and 'errors' in result:
            print("✅ Error capturado correctamente:")
            for error in result['errors']:
                print(f"   - {error.get('message', 'Error desconocido')}")
            return True
        else:
            print("❌ Error no capturado correctamente")
            return False
    
    def test_complex_query(self):
        """Prueba una consulta compleja con múltiples operaciones"""
        print("\n🔗 Probando consulta compleja...")
        
        query = """
        query GetModelInfo {
            modelInfo {
                timestamp
                isLoaded
                features
            }
        }
        
        mutation PredictDust {
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
        """
        
        # Ejecutar queries por separado
        model_query = """
        query {
            modelInfo {
                timestamp
                isLoaded
            }
        }
        """
        
        predict_query = """
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
        """
        
        model_result = self.execute_query(model_query)
        predict_result = self.execute_query(predict_query)
        
        if model_result and predict_result:
            print("✅ Consulta compleja exitosa")
            print(f"   - Modelo cargado: {model_result['data']['modelInfo']['isLoaded']}")
            print(f"   - Predicción: {predict_result['data']['predict']['probability']}")
            return True
        else:
            print("❌ Error en consulta compleja")
            return False
    
    def run_all_tests(self):
        """Ejecuta todas las pruebas"""
        print("🚀 Iniciando pruebas de la API GraphQL")
        print("=" * 60)
        
        # Verificar salud de la API
        if not self.check_health():
            print("\n❌ La API no está disponible. Asegúrate de que esté ejecutándose.")
            return False
        
        # Ejecutar pruebas
        tests = [
            ("Información del modelo", self.test_model_info),
            ("Recarga del modelo", self.test_reload_model),
            ("Predicción individual", self.test_single_prediction),
            ("Predicciones en lote", self.test_batch_prediction),
            ("Manejo de errores", self.test_error_handling),
            ("Consulta compleja", self.test_complex_query)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result is not None:
                    passed += 1
                    print(f"✅ {test_name}: PASÓ")
                else:
                    print(f"❌ {test_name}: FALLÓ")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Resumen: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        else:
            print("⚠️ Algunas pruebas fallaron")
        
        print(f"\n💡 Visita {self.graphql_url} para usar el playground interactivo")
        return passed == total

def main():
    """Función principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
Uso: python test_graphql.py [opciones]

Opciones:
  --help     Muestra esta ayuda
  --url URL  URL de la API GraphQL (default: http://localhost:8000/graphql)

Ejemplos:
  python test_graphql.py
  python test_graphql.py --url http://localhost:8000/graphql
        """)
        return
    
    # Configurar URL si se proporciona
    graphql_url = GRAPHQL_URL
    if len(sys.argv) > 2 and sys.argv[1] == "--url":
        graphql_url = sys.argv[2]
    
    # Crear tester y ejecutar pruebas
    tester = GraphQLTester(graphql_url=graphql_url)
    success = tester.run_all_tests()
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
