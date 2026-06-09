# Net Monitor App — INY1105

**Infraestructura de Aplicaciones I — Duoc UC**  
Escuela de Informática y Telecomunicaciones — Sede Viña del Mar

---

## ¿Qué es esta aplicación?

Net Monitor App es una herramienta de monitoreo de infraestructura de red en tiempo real.  
Muestra métricas del servidor donde se ejecuta:

- Interfaces de red activas con IPs, MAC y estado
- Estadísticas de tráfico (bytes/paquetes enviados y recibidos por interfaz)
- Conexiones TCP activas agrupadas por estado
- Latencia a servidores DNS externos (8.8.8.8, 1.1.1.1, 208.67.222.222)
- CPU, memoria RAM y uptime del sistema
- Log de actividad en tiempo real en el dashboard

---

## Estructura del repositorio

```
netmonitor/
├── app/
│   ├── app.py              ← Aplicación Flask (NO modificar)
│   ├── requirements.txt    ← Dependencias Python (NO modificar)
│   └── templates/
│       └── index.html      ← Dashboard web (NO modificar)
├── nginx/
│   ├── nginx.conf          ← Configuración NGINX (puedes ajustar timeouts)
│   └── Dockerfile          ← Dockerfile NGINX — TÚ debes completarlo (Encargo 4)
├── .github/
│   └── workflows/
│       └── ci-cd.yml       ← Pipeline CI/CD — TÚ debes configurar secrets (Encargo 5)
├── Dockerfile              ← Dockerfile app — TÚ debes completarlo (Encargo 3)
└── README.md
```

---

## Lo que debes crear tú (no está completo en el repositorio)

| Archivo | Encargo | Estado |
|---|---|---|
| `Dockerfile` (raíz) | Encargo 3 | Plantilla provista — completar pasos intermedios |
| `nginx/Dockerfile` | Encargo 4 | Plantilla provista — completar pasos intermedios |
| `.github/workflows/ci-cd.yml` | Encargo 5 | Plantilla provista — configurar secrets |

---

## Endpoints disponibles

| Endpoint | Método | Descripción |
|---|---|---|
| `/` | GET | Dashboard web con todas las métricas |
| `/health` | GET | Health check (HTTP 200 si la app está activa) |
| `/api/metrics` | GET | Todas las métricas en JSON |
| `/api/interfaces` | GET | Solo interfaces de red |
| `/api/ping` | GET | Solo latencia a DNS externos |
| `/api/tcp` | GET | Solo conexiones TCP |

---

## Secrets requeridos en GitHub

Configura estos secrets en `Settings → Secrets and variables → Actions`:

| Secret | Descripción |
|---|---|
| `DOCKERHUB_USERNAME` | Tu usuario de Docker Hub |
| `DOCKERHUB_TOKEN` | Access Token de Docker Hub (no tu contraseña) |
| `AWS_ACCESS_KEY_ID` | Clave de acceso IAM |
| `AWS_SECRET_ACCESS_KEY` | Secreto IAM |
| `AWS_REGION` | Región AWS (ej: `us-east-1`) |
| `ECS_CLUSTER` | Nombre del cluster ECS (ej: `netmonitor`) |
| `ECS_SERVICE_APP` | Nombre del ECS service de la app |
| `ECS_SERVICE_NGINX` | Nombre del ECS service de NGINX |
| `EC2_PUBLIC_IP` | IP pública de la instancia EC2 |

---

## Pruebas de infraestructura en el pipeline

El pipeline incluye 3 pruebas de infraestructura obligatorias:

1. **Health Check HTTP** — verifica que `/health` retorna HTTP 200
2. **Latencia de red** — mide tiempo de respuesta con desglose (DNS, TCP, transferencia)
3. **Validación de puerto** — confirma que el puerto 80 está abierto y `/api/metrics` responde

Las pruebas se ejecutan en el Job `infra-tests`, **después** del build y **antes** del deploy a ECS.

---

## Bind Mount para persistencia de logs (Encargo 7)

La aplicación escribe logs en `/app/logs/netmonitor.log` dentro del contenedor.  
Configura el Bind Mount en la Task Definition de ECS apuntando a `/home/ec2-user/netmonitor-logs` en el host.

Para verificar:

```bash
docker inspect <container_id>
# Buscar sección "Mounts" en la salida
```

---

*Aplicación provista por el docente — No modificar `app/app.py` ni `app/templates/index.html`*
