# Usar imagen base oficial de Python
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para OCR y PDF
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements primero para aprovechar caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación (incluyendo archivos estáticos)
COPY app/ app/

# Variables de entorno para Cloud Run
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Exponer el puerto (Cloud Run usa la variable PORT automáticamente)
EXPOSE 8080

# Comando para ejecutar la aplicación (Cloud Run establece PORT automáticamente)
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info

