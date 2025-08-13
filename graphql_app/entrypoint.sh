#!/usr/bin/env bash
set -euo pipefail

UVICORN_CMD="uvicorn app:app --host 0.0.0.0 --port 8010"

# Arranco Uvicorn en background
$UVICORN_CMD &
PID=$!

# Espero a que /health responda
echo "[entrypoint] esperando a que /health esté listo..."
for i in {1..60}; do
  if curl -sf http://127.0.0.1:8010/health >/dev/null; then
    echo "[entrypoint] server arriba ✅"
    break
  fi
  sleep 0.5
done

# Si no levantó, corto
if ! curl -sf http://127.0.0.1:8010/health >/dev/null; then
  echo "[entrypoint] ❌ no levantó /health"
  kill -SIGTERM "$PID" || true
  wait "$PID" || true
  exit 1
fi

# Ejecutar pruebas de inicio (se puede desactivar con RUN_STARTUP_TESTS=0)
if [ "${RUN_STARTUP_TESTS:-1}" = "1" ]; then
  echo "[entrypoint] corriendo pruebas de inicio..."
  /app/test_graphql.sh || { 
    echo "[entrypoint] ❌ pruebas fallaron"; 
    kill -SIGTERM "$PID" || true; 
    wait "$PID" || true; 
    exit 1; 
  }
  echo "[entrypoint] pruebas OK ✅"
fi

# Quedarme con el proceso de Uvicorn
wait "$PID"
