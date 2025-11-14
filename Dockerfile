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

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación (incluyendo archivos estáticos)
COPY app/ app/

# Exponer el puerto (Cloud Run usa la variable PORT automáticamente)
EXPOSE 8080

# Variable de entorno para el puerto (Cloud Run la establece automáticamente)
ENV PORT=8080

# Comando para ejecutar la aplicación
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info

