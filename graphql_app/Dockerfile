FROM python:3.11-slim

# Herramientas mínimas para curl
RUN apt-get update && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App + scripts
COPY app.py .
COPY entrypoint.sh test_graphql.sh ./
RUN chmod +x /app/entrypoint.sh /app/test_graphql.sh

# Vars útiles
ENV RUN_STARTUP_TESTS=1

EXPOSE 8010

# Arranque: server + pruebas
CMD ["/app/entrypoint.sh"]
