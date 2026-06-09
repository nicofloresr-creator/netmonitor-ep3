# ──────────────────────────────────────────────────────────────────
# NGINX Reverse Proxy — Dockerfile
# INY1105 Infraestructura de Aplicaciones I — Duoc UC
#
# INSTRUCCIÓN PARA EL ESTUDIANTE:
#   Este archivo lo debes crear tú en nginx/Dockerfile (Encargo 4).
#   La imagen base es nginx:alpine. Copia nginx.conf al contenedor
#   y expone el puerto 80.
# ──────────────────────────────────────────────────────────────────

FROM nginx:alpine

LABEL maintainer="docente-iny1105@duoc.cl"
LABEL description="NGINX Reverse Proxy para Net Monitor App"

# Eliminar la configuración por defecto de NGINX
RUN rm /etc/nginx/conf.d/default.conf

# Copiar la configuración personalizada
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto HTTP
EXPOSE 80

# NGINX se inicia en foreground (requerido en Docker)
CMD ["nginx", "-g", "daemon off;"]
