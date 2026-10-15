# Validación del paquete

Fecha: 14 de octubre de 2026.

El 14 de octubre de 2026 se cambió el sensor de DHT11 (temperatura) a HC-SR04 (distancia). El tópico, el bucket y la medición pasaron de `temperatura` a `distancia`, y la unidad de Grafana de °C a cm. Las comprobaciones se separan según se hayan hecho antes o después del cambio.

## Comprobaciones con HC-SR04

- **Arduino virtual:** `arduino_virtual.py --intervalo 0.3 --error-cada 3` creó un puerto serial virtual que, leído con pySerial, entregó `101.08`, `98.93`, `ERR_HCSR04`, `98.07`, `96.26` y `ERR_HCSR04`.
- **Validación del puente:** `distancia_valida` de `puente_mqtt.py` aceptó `123.45` y `2.00` y descartó `ERR_HCSR04`, `nan`, `inf` y la línea vacía.
- **Sintaxis:** compilaron los tres programas Python y el dashboard de Grafana es JSON válido.

## Comprobaciones anteriores al cambio de sensor

Siguen siendo indicativas para la parte del recorrido que no cambió (lectura serial, MQTT, Telegraf, InfluxDB, Grafana), pero se hicieron con los nombres `temperatura` y deben repetirse con los nuevos.

- **Recorrido EMQX -> Telegraf -> InfluxDB -> Grafana:** con Docker 29.5.3 en Apple Silicon, seis lecturas simuladas publicadas con QoS 1 llegaron a un suscriptor MQTT independiente, a InfluxDB y a las cinco consultas del dashboard (por API).
- **Puente serial -> MQTT -> InfluxDB -> Grafana:** con el Arduino virtual, el puente publicó las ocho lecturas válidas con confirmación de EMQX y descartó el mensaje de error; InfluxDB guardó solo las válidas.
- **Lecturas seriales fragmentadas:** una lectura dividida entre dos fragmentos con una pausa mayor que el timeout se reconstruyó correctamente.
- **Imágenes Docker y credenciales:** las cuatro versiones existen para Intel y ARM64; `preparar.py` crea `.env` con permisos 600 y no lo sobrescribe.

## Verificaciones pendientes

- **Compilación del programa HC-SR04:** no hay compilador AVR en este Mac (PlatformIO falló antes con `Bad CPU type in executable`) y no se probó en Wokwi. Falta compilarlo en Arduino IDE o en Wokwi.
- **Simulación en Wokwi:** `diagram.json` usa el componente `wokwi-hc-sr04`, pero no se ejecutó. Falta confirmar que muestra unos `100.00` y que cambia al mover la distancia.
- **`simulador/firmware.hex`:** se retiró porque era el firmware del DHT22. Para usar Wokwi en VS Code hay que exportarlo de nuevo desde Wokwi.
- **Recorrido completo con los nombres nuevos:** Docker no estaba en ejecución durante el cambio. Falta repetir `docker compose up -d` y confirmar que Telegraf escribe en el bucket `distancia` y que Grafana muestra centímetros. En una instalación previa hay que crear antes el bucket (ver LEEME, sección 3).
- **Montaje físico HC-SR04:** no se ha conectado un sensor real.
- **Vista del dashboard en el navegador:** falta abrirlo y confirmar que los paneles se dibujan.

Los datos de ejemplo no acreditan el funcionamiento del sensor físico.
