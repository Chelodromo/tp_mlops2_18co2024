import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from kafka_consumer_utils import KafkaStreamProcessor, test_kafka_connection

FASTAPI_URL = "http://fastapi_app:8000"  # URL interna para Docker

st.title("🌎 Predicción de Polvo Atmosférico")

# --- Selección de modo
modo = st.radio("Selecciona el modo:", ["Manual", "Batch (CSV)", "Streaming"])

if modo == "Manual":
    st.subheader("🚀 Ingresá los datos manualmente")

    col1, col2 = st.columns(2)
    
    with col1:
        TempOut = st.number_input("Temperatura Exterior (TempOut)", value=20.0)
        DewPt = st.number_input("Punto de Rocío (DewPt)", value=5.0)
        WSpeed = st.number_input("Velocidad de Viento Media (WSpeed)", value=10.0)
        WHSpeed = st.number_input("Ráfaga de Viento (WHSpeed)", value=20.0)
    
    with col2:
        Bar = st.number_input("Presión Barométrica (Bar)", value=1013.0)
        Rain = st.number_input("Lluvia (Rain)", value=0.0)
        ET = st.number_input("Evapotranspiración (ET)", value=0.0)
        WDir_deg = st.number_input("Dirección del Viento (WDir_deg)", value=180.0)
    
    Date_num = st.number_input("Fecha (Date_num, timestamp)", value=1743465600.0)

    if st.button("🔮 Predecir"):
        payload = {
            "TempOut": TempOut,
            "DewPt": DewPt,
            "WSpeed": WSpeed,
            "WHSpeed": WHSpeed,
            "Bar": Bar,
            "Rain": Rain,
            "ET": ET,
            "WDir_deg": WDir_deg,
            "Date_num": Date_num
        }
        
        with st.spinner("Procesando predicción..."):
            response = requests.post(f"{FASTAPI_URL}/predict", json=payload)

        if response.status_code == 200:
            result = response.json()
            probability = result.get('probability', [0])[0]
            
            st.success(f"✅ Predicción completada!")
            st.metric("Probabilidad de Polvo", f"{probability:.2%}")
            
            # Mostrar barra de progreso
            st.progress(probability)
            
            if probability > 0.5:
                st.warning("⚠️ Alta probabilidad de polvo atmosférico")
            elif probability > 0.3:
                st.info("ℹ️ Probabilidad moderada de polvo atmosférico")
            else:
                st.success("✅ Baja probabilidad de polvo atmosférico")
        else:
            st.error(f"❌ Error en predicción: {response.text}")

elif modo == "Batch (CSV)":
    st.subheader("📁 Subí un archivo CSV")

    uploaded_file = st.file_uploader("Elegí el archivo CSV", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Vista previa del archivo:")
        st.dataframe(df.head())

        if st.button("🔮 Predecir en batch"):
            payload = df.to_dict(orient="records")
            
            with st.spinner("Procesando predicciones en batch..."):
                response = requests.post(f"{FASTAPI_URL}/predict_batch", json=payload)

            if response.status_code == 200:
                preds = response.json()
                st.write("📈 Predicciones:")
                
                # Crear DataFrame con las predicciones
                predictions_df = pd.DataFrame(preds['predictions'])
                st.dataframe(predictions_df)
                
                # Gráfico de probabilidades
                if not predictions_df.empty:
                    st.line_chart(predictions_df.set_index('date')['probability'])
                
                # Estadísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Promedio", f"{predictions_df['probability'].mean():.2%}")
                with col2:
                    st.metric("Máximo", f"{predictions_df['probability'].max():.2%}")
                with col3:
                    st.metric("Mínimo", f"{predictions_df['probability'].min():.2%}")
            else:
                st.error(f"❌ Error en predicción batch: {response.text}")

else:  # Streaming
    st.subheader("🌊 Streaming en Tiempo Real con Kafka")
    
    # Verificar conexión a Kafka
    kafka_status = test_kafka_connection()
    
    if kafka_status["status"] == "error":
        st.error(f"❌ {kafka_status['message']}")
        st.info("💡 Asegúrate de que el DAG de Airflow haya ejecutado el productor Kafka")
        st.stop()
    
    st.success("✅ Conexión a Kafka establecida")
    
    # Configuración del streaming
    st.write("**⚙️ Configuración del Streaming:**")
    col1, col2 = st.columns(2)
    
    with col1:
        streaming_enabled = st.checkbox("🔄 Habilitar Streaming", value=False)
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
    
    with col2:
        refresh_interval = st.slider("⏱️ Intervalo de refresh (segundos)", 1, 10, 3)
        max_messages = st.number_input("📊 Máximo de mensajes", 5, 50, 20)
    
    # Inicializar procesador de Kafka
    if 'kafka_processor' not in st.session_state:
        try:
            st.session_state.kafka_processor = KafkaStreamProcessor()
            st.session_state.messages = []
        except Exception as e:
            st.error(f"❌ Error inicializando procesador Kafka: {e}")
            st.stop()
    
    # Controles de streaming
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 Iniciar Streaming"):
            st.session_state.streaming_active = True
            st.success("Streaming iniciado!")
    
    with col2:
        if st.button("⏹️ Detener Streaming"):
            st.session_state.streaming_active = False
            st.warning("Streaming detenido!")
    
    with col3:
        if st.button("🗑️ Limpiar Mensajes"):
            st.session_state.messages = []
            st.success("Mensajes limpiados!")
    
    with col4:
        if st.button("🧪 Generar Datos de Prueba"):
            # Generar datos de prueba para demostración
            import random
            import time
            
            test_data = {
                "sensor_id": random.randint(1, 5),
                "TempOut": round(random.uniform(15, 30), 1),
                "DewPt": round(random.uniform(-5, 20), 1),
                "WSpeed": round(random.uniform(0, 25), 1),
                "WHSpeed": round(random.uniform(5, 40), 1),
                "Bar": round(random.uniform(1000, 1030), 1),
                "Rain": round(random.uniform(0, 5), 1),
                "ET": round(random.uniform(0, 8), 1),
                "WDir_deg": round(random.uniform(0, 360), 1),
                "Date_num": time.time(),
                "timestamp": datetime.now().isoformat(),
                "batch_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
            # Procesar datos de prueba
            try:
                prediction_result = st.session_state.kafka_processor.process_weather_data(test_data)
                st.session_state.messages.append(prediction_result)
                st.success("✅ Datos de prueba generados y procesados!")
            except Exception as e:
                st.error(f"❌ Error generando datos de prueba: {e}")
    
    # Procesar streaming
    if streaming_enabled and st.session_state.get('streaming_active', False):
        try:
            # Obtener mensajes de Kafka
            new_messages = st.session_state.kafka_processor.get_latest_messages(max_messages)
            
            if new_messages:
                st.session_state.messages.extend(new_messages)
                
                # Mantener solo los últimos mensajes
                if len(st.session_state.messages) > max_messages:
                    st.session_state.messages = st.session_state.messages[-max_messages:]
                
                st.success(f"📨 {len(new_messages)} nuevos mensajes recibidos")
            else:
                # Si no hay mensajes nuevos, mostrar información
                st.info("⏳ Esperando mensajes de Kafka... Ejecuta el DAG de Airflow para generar datos")
        except Exception as e:
            st.error(f"❌ Error en streaming: {e}")
            st.info("💡 Verifica que Kafka esté funcionando y el DAG se haya ejecutado")
    
    # Mostrar mensajes en tiempo real
    st.write("**📡 Predicciones en Tiempo Real:**")
    
    if st.session_state.messages:
        # Crear DataFrame para visualización
        messages_df = pd.DataFrame([
            {
                'Timestamp': msg['timestamp'],
                'Sensor ID': msg['sensor_id'],
                'Temperatura': msg['input_data'].get('TempOut', 0),
                'Viento': msg['input_data'].get('WSpeed', 0),
                'Probabilidad': msg['probability'],
                'Estado': msg['status']
            }
            for msg in st.session_state.messages
        ])
        
        # Mostrar tabla de predicciones
        st.dataframe(messages_df, use_container_width=True)
        
        # Gráfico de probabilidades en tiempo real
        if len(messages_df) > 1:
            st.write("**📈 Gráfico de Probabilidades:**")
            chart_data = messages_df.set_index('Timestamp')['Probabilidad']
            st.line_chart(chart_data)
        
        # Estadísticas en tiempo real
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Mensajes", len(st.session_state.messages))
        with col2:
            st.metric("Promedio", f"{messages_df['Probabilidad'].mean():.2%}")
        with col3:
            st.metric("Máximo", f"{messages_df['Probabilidad'].max():.2%}")
        with col4:
            st.metric("Mínimo", f"{messages_df['Probabilidad'].min():.2%}")
        
        # Mostrar últimos mensajes detallados
        st.write("**🔍 Últimos Mensajes Detallados:**")
        for msg in reversed(st.session_state.messages[-5:]):  # Mostrar últimos 5
            with st.expander(f"📨 {msg['timestamp']} - Sensor {msg['sensor_id']} - Prob: {msg['probability']:.2%}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Datos de Entrada:**")
                    input_data = msg['input_data']
                    st.json({
                        "TempOut": input_data.get('TempOut', 0),
                        "DewPt_": input_data.get('DewPt_', 0),
                        "WSpeed": input_data.get('WSpeed', 0),
                        "WHSpeed": input_data.get('WHSpeed', 0),
                        "Bar": input_data.get('Bar', 0),
                        "Rain": input_data.get('Rain', 0),
                        "ET": input_data.get('ET', 0),
                        "WDir_deg": input_data.get('WDir_deg', 0)
                    })
                
                with col2:
                    st.write("**Predicción:**")
                    if msg['status'] == 'success':
                        st.success(f"Probabilidad: {msg['probability']:.2%}")
                        st.progress(msg['probability'])
                        
                        if msg['probability'] > 0.5:
                            st.warning("⚠️ Alta probabilidad de polvo")
                        elif msg['probability'] > 0.3:
                            st.info("ℹ️ Probabilidad moderada")
                        else:
                            st.success("✅ Baja probabilidad")
                    else:
                        st.error(f"Error: {msg.get('error', 'Desconocido')}")
    
    else:
        st.info("📭 No hay mensajes aún. Ejecuta el DAG de Airflow para generar datos o inicia el streaming.")
    
    # Auto-refresh
    if auto_refresh and streaming_enabled and st.session_state.get('streaming_active', False):
        time.sleep(refresh_interval)
        st.rerun()

# Footer
st.markdown("---")
st.markdown("*Sistema de Predicción de Polvo Atmosférico - MLOps II*")
