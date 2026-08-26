FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN python build_frontend.py && \
    cd frontend && npm install && npm run build && \
    mkdir -p /app/dist && \
    cp -r frontend/dist/* /app/dist/
EXPOSE 8000
CMD ["uvicorn", "aura_bootstrap:app", "--host", "0.0.0.0", "--port", "8000"]
