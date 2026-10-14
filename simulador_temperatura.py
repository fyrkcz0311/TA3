"""Publica temperaturas simuladas en MQTT, sin Arduino, para probar el recorrido completo."""
import argparse
import random
import sys
import threading
import time

import paho.mqtt.client as mqtt


def siguiente_temperatura(actual, base, variacion):
    # Paseo aleatorio que tiende a volver a la base, con limites razonables para un interior.
    paso = random.uniform(-variacion, variacion) + (base - actual) * 0.1
    return min(max(actual + paso, 10.0), 40.0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="127.0.0.1")
    parser.add_argument("--mqtt-puerto", type=int, default=1883)
    parser.add_argument("--topico", default="iot/raspberrypi/temperatura")
    parser.add_argument("--intervalo", type=float, default=10.0, help="segundos entre lecturas")
    parser.add_argument("--base", type=float, default=24.0, help="temperatura media en C")
    parser.add_argument("--variacion", type=float, default=0.5, help="cambio maximo por lectura")
    parser.add_argument("--cantidad", type=int, default=0, help="lecturas a enviar; 0 = sin fin")
    args = parser.parse_args()
    if args.intervalo <= 0:
        parser.error("--intervalo debe ser mayor que 0")

    conectado = threading.Event()
    cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                          client_id="ta3-simulador-python", protocol=mqtt.MQTTv311)
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
        print(f"Simulando una temperatura cada {args.intervalo:g} s en {args.topico}. "
              "Detener con Control + C.", flush=True)
        valor = args.base
        enviadas = 0
        proxima = time.monotonic()
        while args.cantidad == 0 or enviadas < args.cantidad:
            valor = siguiente_temperatura(valor, args.base, args.variacion)
            if not conectado.is_set():
                print(f"Sin MQTT; lectura simulada {valor:.2f} no enviada.", flush=True)
            else:
                mensaje = cliente.publish(args.topico, f"{valor:.2f}", qos=1, retain=False)
                try:
                    mensaje.wait_for_publish(timeout=5)
                    if mensaje.is_published():
                        hora = time.strftime("%H:%M:%S")
                        print(f"{hora} EMQX confirmo: {valor:.2f} C (simulada) -> {args.topico}",
                              flush=True)
                    else:
                        print("Sin confirmacion aun; MQTT puede reenviar al reconectar.", flush=True)
                except (RuntimeError, ValueError) as error:
                    print(f"Publicacion pendiente o fallida: {error}", flush=True)
            enviadas += 1
            if args.cantidad and enviadas >= args.cantidad:
                break
            # Intervalo fijo respecto al reloj, sin acumular el tiempo de cada publicacion.
            proxima += args.intervalo
            time.sleep(max(0.0, proxima - time.monotonic()))
    finally:
        cliente.disconnect()
        cliente.loop_stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Simulador detenido.")
    except (OSError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
