"""
Net Monitor App — INY1105 Infraestructura de Aplicaciones I
Duoc UC — Escuela de Informática y Telecomunicaciones

Aplicación de monitoreo de infraestructura de red en tiempo real.
Provista por el docente. NO modificar este archivo.
"""

import os
import time
import socket
import logging
import platform
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import psutil
from flask import Flask, jsonify, render_template

# ── Configuración ────────────────────────────────────────────────
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "netmonitor.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("netmonitor")

app = Flask(__name__)
START_TIME = time.time()


# ── Helpers ──────────────────────────────────────────────────────
def _uptime() -> str:
    """Devuelve el uptime del proceso como string legible."""
    elapsed = int(time.time() - START_TIME)
    return str(timedelta(seconds=elapsed))


def _system_uptime() -> str:
    """Uptime del sistema operativo."""
    try:
        boot = psutil.boot_time()
        elapsed = int(time.time() - boot)
        return str(timedelta(seconds=elapsed))
    except Exception:
        return "N/A"


def _hostname() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


def _ping_host(host: str, count: int = 3) -> dict:
    """
    Ejecuta ping al host y devuelve latencia promedio en ms.
    Funciona en Linux y macOS.
    """
    try:
        flag = "-c" if platform.system() != "Windows" else "-n"
        result = subprocess.run(
            ["ping", flag, str(count), "-W", "2", host],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        # Parsear línea de estadísticas: min/avg/max/mdev
        for line in output.splitlines():
            if "min/avg/max" in line or "Minimum" in line:
                parts = line.split("=")[-1].strip().split("/")
                return {
                    "host": host,
                    "min_ms": float(parts[0].strip()),
                    "avg_ms": float(parts[1].strip()),
                    "max_ms": float(parts[2].strip().split()[0]),
                    "reachable": True,
                }
        # Si no se puede parsear, al menos indica si hubo respuesta
        reachable = result.returncode == 0
        return {"host": host, "min_ms": None, "avg_ms": None, "max_ms": None, "reachable": reachable}
    except Exception as e:
        log.warning("ping %s falló: %s", host, e)
        return {"host": host, "min_ms": None, "avg_ms": None, "max_ms": None, "reachable": False}


def _net_interfaces() -> list:
    """
    Devuelve lista de interfaces de red con IPs, MAC, estado y estadísticas de tráfico.
    """
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    io = psutil.net_io_counters(pernic=True)

    for name, addr_list in addrs.items():
        ipv4 = next(
            (a.address for a in addr_list if a.family == socket.AF_INET), None
        )
        ipv6 = next(
            (a.address for a in addr_list
             if hasattr(socket, "AF_INET6") and a.family == socket.AF_INET6), None
        )
        mac = next(
            (a.address for a in addr_list if a.family == psutil.AF_LINK), None
        )

        st = stats.get(name)
        counters = io.get(name)

        interfaces.append({
            "name": name,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "mac": mac,
            "is_up": st.isup if st else False,
            "speed_mbps": st.speed if st else 0,
            "bytes_sent": counters.bytes_sent if counters else 0,
            "bytes_recv": counters.bytes_recv if counters else 0,
            "packets_sent": counters.packets_sent if counters else 0,
            "packets_recv": counters.packets_recv if counters else 0,
            "errors_out": counters.errout if counters else 0,
            "errors_in": counters.errin if counters else 0,
            "drop_out": counters.dropout if counters else 0,
            "drop_in": counters.dropin if counters else 0,
        })

    return sorted(interfaces, key=lambda x: (not x["is_up"], x["name"]))


def _tcp_connections() -> dict:
    """
    Devuelve resumen de conexiones TCP agrupadas por estado.
    """
    try:
        conns = psutil.net_connections(kind="tcp")
    except psutil.AccessDenied:
        return {"error": "Acceso denegado — ejecutar con privilegios", "summary": {}, "total": 0}

    summary: dict[str, int] = {}
    for c in conns:
        state = c.status if c.status else "UNKNOWN"
        summary[state] = summary.get(state, 0) + 1

    return {
        "total": len(conns),
        "summary": dict(sorted(summary.items(), key=lambda x: -x[1])),
        "error": None,
    }


def _cpu_and_memory() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.3),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "mem_total_mb": round(psutil.virtual_memory().total / 1024 / 1024, 1),
        "mem_used_mb": round(psutil.virtual_memory().used / 1024 / 1024, 1),
        "mem_percent": psutil.virtual_memory().percent,
    }


def _format_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


# ── Rutas ────────────────────────────────────────────────────────
@app.route("/")
def index():
    log.info("GET / — dashboard solicitado")
    return render_template("index.html")


@app.route("/health")
def health():
    """Endpoint de health check para el pipeline CI/CD."""
    return jsonify({
        "status": "ok",
        "hostname": _hostname(),
        "app_uptime": _uptime(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), 200


@app.route("/api/metrics")
def metrics():
    """
    Endpoint principal — devuelve todas las métricas de red en JSON.
    El dashboard consume este endpoint cada 5 segundos vía fetch().
    """
    log.info("GET /api/metrics — recolectando métricas")

    # Latencia a servidores DNS/ICMP conocidos
    dns_targets = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
    ping_results = [_ping_host(h, count=2) for h in dns_targets]

    interfaces = _net_interfaces()
    tcp = _tcp_connections()
    resources = _cpu_and_memory()

    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "hostname": _hostname(),
        "platform": platform.system(),
        "app_uptime": _uptime(),
        "system_uptime": _system_uptime(),
        "interfaces": interfaces,
        "tcp_connections": tcp,
        "ping": ping_results,
        "resources": resources,
        "log_file": str(LOG_DIR / "netmonitor.log"),
    }

    # Log de resumen
    log.info(
        "Métricas: %d interfaces | TCP total=%d | CPU=%.1f%%",
        len(interfaces),
        tcp.get("total", 0),
        resources["cpu_percent"],
    )

    return jsonify(payload)


@app.route("/api/interfaces")
def interfaces_only():
    return jsonify({"interfaces": _net_interfaces()})


@app.route("/api/ping")
def ping_only():
    targets = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
    return jsonify({"ping": [_ping_host(h) for h in targets]})


@app.route("/api/tcp")
def tcp_only():
    return jsonify({"tcp_connections": _tcp_connections()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    log.info("Net Monitor App iniciando en puerto %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
