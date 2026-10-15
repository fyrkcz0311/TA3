"""Lee distancias del Uno por USB, o de Wokwi por RFC2217, y publica en MQTT."""
import argparse
import math
import re
import sys
import threading
import time

import paho.mqtt.client as mqtt
import serial


DISTANCIA_MIN_CM = 2.0
DISTANCIA_MAX_CM = 400.0
# Acepta "42.37" y tambien "Distancia: 42.37 cm".
LINEA = re.compile(r"(?:Distancia:\s*)?(-?\d+(?:\.\d+)?)(?:\s*cm)?", re.IGNORECASE)


def distancia_valida(linea):
    encontrado = LINEA.fullmatch(linea)
    if not encontrado:
        return None
    valor = float(encontrado.group(1))
    # Sin eco, pulseIn devuelve 0 y el sketch imprime 0.00: no es una medicion.
    if not math.isfinite(valor) or not DISTANCIA_MIN_CM <= valor <= DISTANCIA_MAX_CM:
        return None
    return valor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--puerto", required=True,
                        help="/dev/cu.usbmodem... o rfc2217://localhost:4000")
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--mqtt-puerto", type=int, default=1883)
    parser.add_argument("--topico", default="iot/raspberrypi/distancia")
    args = parser.parse_args()

    conectado = threading.Event()
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                          client_id="ta3-arduino-usb", protocol=mqtt.MQTTv311)
    cliente.reconnect_delay_set(min_delay=1, max_delay=15)
    cliente.max_queued_messages_set(100)

    def al_conectar(client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            print(f"Conexion MQTT rechazada: {reason_code}", flush=True)
        else:
            conectado.set()
            print("MQTT conectado.", flush=True)

    def al_desconectar(client, userdata, flags, reason_code, properties):
        conectado.clear()
        print("MQTT desconectado.", flush=True)

    cliente.on_connect = al_conectar
    cliente.on_disconnect = al_desconectar
    cliente.connect_async(args.broker, args.mqtt_puerto, keepalive=60)
    cliente.loop_start()
    try:
        if not conectado.wait(20):
            raise RuntimeError("EMQX no responde. Abre Docker Desktop y revisa docker compose ps.")
        with serial.serial_for_url(args.puerto, baudrate=9600, timeout=1) as puerto:
            # Abrir el USB puede reiniciar el Uno. Esperamos y limpiamos bytes incompletos.
            time.sleep(2)
            puerto.reset_input_buffer()
            print(f"Leyendo {args.puerto}; espera hasta 10 segundos para la primera muestra.", flush=True)
            pendiente = bytearray()
            descartando = False
            while True:
                fragmento = puerto.read_until(b"\n", size=128)
                if not fragmento:
                    continue
                if descartando:
                    if fragmento.endswith(b"\n"):
                        descartando = False
                    continue
                pendiente.extend(fragmento)
                if len(pendiente) > 128:
                    descartando = not pendiente.endswith(b"\n")
                    pendiente.clear()
                    print("Linea serial demasiado larga; descartada.", flush=True)
                    continue
                if not pendiente.endswith(b"\n"):
                    continue
                linea = pendiente.decode("ascii", errors="replace").strip()
                pendiente.clear()
                valor = distancia_valida(linea)
                if valor is None:
                    print(f"Lectura ignorada: {linea!r}. Revisa sensor y cableado.", flush=True)
                    continue
                if not conectado.is_set():
                    # No acumulamos lecturas indefinidamente ni inventamos fechas de adquisicion.
                    print(f"Sin MQTT; lectura {valor:.2f} no enviada.", flush=True)
                    continue
                mensaje = cliente.publish(args.topico, f"{valor:.2f}", qos=1, retain=False)
                try:
                    mensaje.wait_for_publish(timeout=5)
                    if mensaje.is_published():
                        print(f"EMQX confirmo: {valor:.2f} cm -> {args.topico}", flush=True)
                    else:
                        print("Sin confirmacion aun; MQTT puede reenviar al reconectar.", flush=True)
                except (RuntimeError, ValueError) as error:
                    print(f"Publicacion pendiente o fallida: {error}", flush=True)
    finally:
        cliente.disconnect()
        cliente.loop_stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Puente detenido.")
    except (serial.SerialException, OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
