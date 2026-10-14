# Validación del paquete

Fecha: 14 de octubre de 2026.

## Comprobaciones realizadas

- **Simulación web:** Arduino Uno y DHT22 en Wokwi. El programa compiló, mostró `24.00` y cambió a `28.00` después de ajustar la temperatura virtual. Se observaron lecturas cada 10 segundos de tiempo simulado. Se exportó el firmware compilado y se comprobaron las sumas de los registros Intel HEX.
- **Puente USB a MQTT:** se ejecutó el programa Python con un puerto serial virtual y un receptor MQTT local de prueba. Se recibieron exactamente `24.25`, `26.50` y `27.75` en `iot/raspberrypi/temperatura`, con QoS 1 y confirmaciones. El receptor de esta prueba fue una implementación mínima para comprobar el protocolo; no fue EMQX.
- **Lecturas inválidas:** se descartaron `ERR_DHT`, `nan`, `inf` y texto. Una lectura dividida entre dos fragmentos seriales con una pausa mayor que el timeout se reconstruyó como `24.25`.
- **Configuración:** Docker Compose aceptó el archivo con credenciales de prueba. Se comprobó la sintaxis de Python, JSON y TOML y la coherencia de los cinco paneles de Grafana.
- **Imágenes Docker:** se verificó que las cuatro versiones indicadas existen y publican variantes Linux para Intel y ARM64.
- **Credenciales locales:** `preparar.py` generó `.env` con permisos de lectura/escritura para su propietario y conservó el contenido al ejecutarlo nuevamente. El paquete entregado no contiene credenciales generadas.

- **Recorrido EMQX -> Telegraf -> InfluxDB -> Grafana con temperaturas simuladas:** se iniciaron los cuatro servicios con `docker compose up -d` (Docker 29.5.3, Apple Silicon). `simulador_temperatura.py` publicó 6 lecturas, una cada 10 segundos, en `iot/raspberrypi/temperatura` con QoS 1: `24.09`, `24.16`, `24.20`, `24.64`, `24.71` y `24.60`. Un suscriptor MQTT independiente recibió los seis valores; la consulta Flux en InfluxDB devolvió los seis con las mismas horas, y las cinco consultas del dashboard de Grafana, ejecutadas mediante su API, devolvieron última lectura `24.60`, promedio `24.40`, mínimo `24.09`, máximo `24.71` y la serie completa. La fuente de datos de Grafana respondió `datasource is working`. No se revisó el dashboard visualmente en el navegador.
- **Puente serial -> MQTT -> InfluxDB -> Grafana con Arduino virtual:** `arduino_virtual.py` creó `/dev/ttys001` y escribió `23.00`, `23.20`, `22.90`, `22.60`, `22.50`, `ERR_DHT`, `22.40`, `22.70` y `22.90`, uno cada 10 segundos. `puente_mqtt.py --puerto /dev/ttys001` publicó las ocho lecturas válidas con confirmación de EMQX y descartó `ERR_DHT`. InfluxDB guardó las ocho y no guardó el error. Las consultas de Grafana devolvieron última lectura `22.90`, promedio `22.77`, mínimo `22.40` y máximo `23.20`.

## Verificaciones pendientes

- **Montaje físico DHT11:** no se ha conectado un sensor real ni se ha identificado si el del usuario lleva tres o cuatro patas. Se proporcionan instrucciones para ambas presentaciones.
- **Puente USB con Uno físico o Wokwi:** `puente_mqtt.py` se probó de punta a punta con `arduino_virtual.py`, un puerto serial virtual (pty) que escribe lo mismo que el firmware. Aún no se probó con un Uno conectado por USB ni con Wokwi para VS Code.
- **Vista del dashboard en el navegador:** los datos del dashboard se verificaron por API; falta abrirlo, iniciar sesión y confirmar que los paneles se dibujan.
- **Simulación con VS Code y RFC2217:** la configuración sigue la documentación oficial de Wokwi, pero no se ejecutó esa modalidad ni se activó una licencia. El archivo `firmware.hex` permite iniciar la prueba sin compilar localmente.
- **Compilación local PlatformIO:** la descarga de herramientas y bibliotecas terminó, pero el compilador Intel no pudo ejecutarse en este Mac (`Bad CPU type in executable`). La simulación web sí compiló correctamente. La guía indica la alternativa con firmware preparado y el procedimiento oficial de Apple si se requiere Rosetta.

La prueba con datos de ejemplo no acredita el funcionamiento del sensor físico ni sustituye las comprobaciones en InfluxDB y Grafana. La guía explica cómo hacerlas al iniciar el sistema.
