"""Imita al Uno con DHT11: crea un puerto serial virtual y escribe lo mismo que el firmware.

Sirve para probar puente_mqtt.py sin placa. Usa un pseudo-terminal de macOS/Linux;
el puente lo abre igual que /dev/cu.usbmodem...
"""
import argparse
import os
import random
import time
import tty


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intervalo", type=float, default=10.0, help="segundos entre lecturas")
    parser.add_argument("--base", type=float, default=23.0, help="temperatura media en C")
    parser.add_argument("--error-cada", type=int, default=6,
                        help="emite ERR_DHT cada N lecturas; 0 = nunca")
    args = parser.parse_args()
    if args.intervalo <= 0:
        parser.error("--intervalo debe ser mayor que 0")

    maestro, esclavo = os.openpty()
    tty.setraw(esclavo)
    # El extremo esclavo queda abierto para que el puerto exista aunque el puente se reconecte.
    print(f"Puerto serial virtual: {os.ttyname(esclavo)}", flush=True)
    print("Usalo con: python puente_mqtt.py --puerto " + os.ttyname(esclavo), flush=True)

    valor = args.base
    lecturas = 0
    try:
        while True:
            time.sleep(args.intervalo)
            lecturas += 1
            if args.error_cada and lecturas % args.error_cada == 0:
                linea = "ERR_DHT"
            else:
                valor += random.uniform(-0.3, 0.3) + (args.base - valor) * 0.1
                # El DHT11 entrega pasos de 0.1 C; el firmware imprime dos decimales.
                linea = f"{round(valor, 1):.2f}"
            os.write(maestro, (linea + "\r\n").encode("ascii"))
            print(f"{time.strftime('%H:%M:%S')} Serial -> {linea}", flush=True)
    except KeyboardInterrupt:
        print("Arduino virtual detenido.")
    finally:
        os.close(maestro)
        os.close(esclavo)


if __name__ == "__main__":
    main()
