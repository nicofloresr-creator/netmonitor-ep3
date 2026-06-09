# ──────────────────────────────────────────────────────────────────
# Net Monitor App — Dockerfile
# INY1105 Infraestructura de Aplicaciones I — Duoc UC
#
# INSTRUCCIÓN PARA EL ESTUDIANTE:
#   Este archivo lo debes crear tú, siguiendo los requisitos del Encargo 3.
#   La imagen base, la exposición de puerto y el CMD están definidos.
#   Completa los pasos intermedios (WORKDIR, COPY, RUN).
#
# Requisitos:
#   - Imagen base : python:3.11-slim
#   - Puerto      : 5000
#   - CMD         : python app.py
# ──────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# Metadatos de la imagen
LABEL maintainer="docente-iny1105@duoc.cl"
LABEL description="Net Monitor App — monitoreo de infraestructura de red"
LABEL version="1.0"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar dependencias del sistema necesarias para psutil
RUN apt-get update && apt-get install -y --no-install-recommends \
        iputils-ping \
        net-tools \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python primero (capa cacheada)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY app/ .

# Crear directorio de logs (Bind Mount del Encargo 7 lo mapeará aquí)
RUN mkdir -p /app/logs

# Exponer el puerto de la aplicación
EXPOSE 5000

# Comando de inicio
CMD ["python", "app.py"]
