"""Genera las credenciales locales, sin reemplazar una configuracion existente."""
from pathlib import Path
import secrets

archivo = Path(__file__).resolve().parent / ".env"
if archivo.exists():
    print(".env ya existe. Se conserva su configuracion.")
else:
    contenido = "\n".join([
        "INFLUX_USER=admin",
        f"INFLUX_PASSWORD={secrets.token_hex(12)}",
        f"INFLUX_TOKEN={secrets.token_hex(32)}",
        "GRAFANA_USER=admin",
        f"GRAFANA_PASSWORD={secrets.token_hex(12)}",
        f"EMQX_PASSWORD={secrets.token_hex(12)}",
        "MQTT_HOST_PORT=1883",
        "EMQX_UI_PORT=18083",
        "INFLUX_HOST_PORT=8086",
        "GRAFANA_HOST_PORT=3000",
        "",
    ])
    with archivo.open("x") as stream:
        stream.write(contenido)
    archivo.chmod(0o600)
    print(".env creado. Las contrasenas estan en ese archivo; no lo compartas.")
