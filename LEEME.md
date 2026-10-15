# Arduino Uno + HC-SR04: distancia en MQTT, InfluxDB y Grafana

Esta es una implementación nueva basada en la arquitectura del PDF. El informe usaba un generador en Python; aquí el Arduino lee el sensor y Python actúa como puente USB. Los datos del montaje físico serán mediciones; los del simulador son valores de prueba. La placa prevista es el Uno R3 clasico.

**Recorrido:** HC-SR04 -> Arduino Uno -> USB -> Python en el Mac -> EMQX/MQTT -> Telegraf -> InfluxDB -> Grafana.

La computadora debe permanecer encendida, conectada por USB y ejecutando el puente. No hace falta comprar un módulo Wi-Fi para esta solución. El tópico es `iot/raspberrypi/distancia`; se conserva el prefijo `iot/raspberrypi` del informe, aunque el dispositivo ahora sea un Arduino. Cada lectura es la distancia en centímetros al objeto que tiene delante el sensor.

## 1. Materiales y conexión física

- Arduino Uno y cable USB que permita transmitir datos.
- Sensor ultrasónico HC-SR04 (4 patas).
- Protoboard y cables jumper.

No hacen falta resistencias. Desconecta el USB mientras colocas los cables y sigue las etiquetas impresas en el sensor:

| Pata del HC-SR04 | Arduino Uno |
| --- | --- |
| VCC | 5V |
| Trig | Pin digital 9 (D9) |
| Echo | Pin digital 8 (D8) |
| GND | GND |

El HC-SR04 funciona a 5 V y su pin Echo entrega 5 V, que el Uno acepta directamente. (En placas de 3,3 V haría falta un divisor de tensión en Echo; no es el caso del Uno.)

Coloca el sensor con los dos "ojos" mirando hacia una superficie plana y dura. Mide de 2 a 400 cm en un cono de unos 15°; telas, espuma y superficies muy inclinadas pueden absorber o desviar el eco.

## 2. Cargar el programa en el Uno

1. Instala o abre [Arduino IDE](https://www.arduino.cc/en/software/).
2. Abre `arduino/distancia_hcsr04/distancia_hcsr04.ino`. No necesita bibliotecas adicionales.
3. Conecta el Uno por USB. En Herramientas elige **Arduino Uno** y el puerto de la placa.
4. Sube el programa y abre el Monitor Serie a **9600 baudios**.
5. Debe aparecer un número como `42.37` cada segundo. Acerca y aleja la mano del sensor: el valor debe cambiar.

El programa está configurado para **Trig en D9** y **Echo en D8**. Aparece `ERR_HCSR04` cuando no vuelve eco o la distancia queda fuera de 2 a 400 cm: revisa el cableado o apunta el sensor a una superficie más cercana. Para medir más seguido, cambia `INTERVALO_MS` en el programa.

**Cierra el Monitor Serie antes de ejecutar Python:** el monitor y el puente no deben ocupar el mismo puerto simultaneamente. Tambien cierralo antes de volver a cargar un programa.

## 3. Preparar MQTT, InfluxDB y Grafana en el Mac

Necesitas [Docker Desktop para Mac](https://docs.docker.com/desktop/setup/install/mac-install/) y [Python 3](https://www.python.org/downloads/macos/). Docker debe estar abierto y haber terminado de iniciar. Las imagenes del proyecto usan las versiones del informe, no la etiqueta `latest`.

Descomprime el paquete. Abre Terminal y escribe `cd `, arrastra la carpeta `arduino_iot_mac` a la ventana y pulsa Enter. Así trabajas en la carpeta correcta aunque su ruta tenga espacios.

Ejecuta estas instrucciones, una por una:

```sh
python3 preparar.py
docker compose up -d
docker compose ps
```

La primera instrucción crea `.env` con contraseñas aleatorias y el token de InfluxDB. La segunda descarga e inicia los cuatro servicios. La primera descarga puede tardar varios minutos. Espera hasta que los cuatro aparezcan funcionando; InfluxDB incluye una comprobación de estado.

Las credenciales se consultan abriendo el archivo `.env` local. En Finder puedes mostrar archivos ocultos con **Command + Shift + .**. No compartas ese archivo ni regeneres las credenciales después de inicializar los volumenes: las cuentas ya creadas conservan sus claves.

| Aplicacion | Direccion predeterminada | Acceso |
| --- | --- | --- |
| Grafana | http://127.0.0.1:3000/d/ta3-distancia-arduino | Usuario `admin`; clave `GRAFANA_PASSWORD` de `.env` |
| InfluxDB | http://127.0.0.1:8086 | Usuario `admin`; clave `INFLUX_PASSWORD` de `.env` |
| Panel EMQX | http://127.0.0.1:18083 | Usuario `admin`; clave `EMQX_PASSWORD` de `.env` |

La fuente de datos y el dashboard de Grafana se configuran automáticamente. Verás última lectura, promedio, mínimo, máximo e historial. Mientras no ingresen distancias mostrarán ausencia de datos.

**Si ya habías iniciado Docker con la versión de temperatura:** InfluxDB crea su bucket solo la primera vez, así que el bucket `distancia` no existe todavía. Créalo sin borrar nada:

```sh
docker compose up -d
docker compose exec influxdb influx bucket create --name distancia --org ta3
docker compose restart telegraf
```

Las lecturas antiguas siguen en el bucket `temperatura`. Si prefieres empezar desde cero, `docker compose down -v` borra **todos** los datos guardados y la próxima vez `docker compose up -d` crea el bucket `distancia` automáticamente.

Los puertos quedan publicados solamente en este Mac (`127.0.0.1`). MQTT funciona sin usuario en este laboratorio local. El puente se ejecuta directamente en macOS, donde puede acceder al USB; no se introduce dentro de Docker.

Si un puerto ya esta ocupado, cambia el correspondiente `*_PORT` en `.env` antes del arranque. Si cambias `MQTT_HOST_PORT`, pasa ese mismo número al puente mediante `--mqtt-puerto`.

## 4. Enviar las lecturas reales a MQTT

En la misma carpeta del proyecto:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m serial.tools.list_ports
```

Busca el puerto del Uno. Suele empezar por `/dev/cu.usbmodem` o `/dev/cu.usbserial`; puede tener otro nombre, por ejemplo `/dev/cu.wchusbserial...`, en placas compatibles. Usa el puerto que aparezca realmente en tu Mac.

Con el Monitor Serie cerrado, inicia el puente. **Sustituye el ejemplo de puerto por el tuyo:**

```sh
python puente_mqtt.py --puerto /dev/cu.usbmodem1101
```

Cuando una lectura llegue al broker aparecera un mensaje como:

```text
EMQX confirmo: 42.37 cm -> iot/raspberrypi/distancia
```

El contenido enviado a MQTT es solo `42.37`, sin `cm`, sin texto y sin JSON. Se usa QoS 1. La confirmación acredita recepción por EMQX; comprueba aparte que la lectura este en InfluxDB y Grafana.

Abre Grafana y espera las primeras lecturas. Telegraf escribe por lotes cada 5 segundos y Grafana refresca cada 10 segundos; la lectura puede tardar un poco en aparecer. La marca temporal se asigna al recibir el dato, como en el informe.

### Probar sin Arduino: distancias simuladas

Para comprobar MQTT, InfluxDB y Grafana sin placa, con el entorno Python activado:

```sh
python simulador_distancia.py
```

Publica una distancia cercana a 100 cm cada 10 segundos en el mismo tópico y con el mismo formato que el puente. Opciones útiles: `--intervalo`, `--base`, `--cantidad 6` (para una prueba corta) y `--mqtt-puerto`. Son valores de prueba, no mediciones: no lo ejecutes al mismo tiempo que el puente, porque ambos escriben en el mismo tópico.

### Probar el puente sin Arduino: Uno virtual

`arduino_virtual.py` crea un puerto serial virtual que escribe lo mismo que el firmware (una lectura cada 10 segundos y, cada 6, un `ERR_HCSR04`). Así se prueba `puente_mqtt.py` tal como se usaría con la placa. En una Terminal:

```sh
python arduino_virtual.py
```

Muestra un puerto como `/dev/ttys001`. En otra Terminal, con el entorno activado:

```sh
python puente_mqtt.py --puerto /dev/ttys001
```

Usa el puerto que aparezca en tu pantalla. Detén primero el puente y después el Uno virtual con **Control + C**.

## 5. Simular el circuito

### Prueba sencilla en el navegador

Abre [un nuevo Arduino Uno en Wokwi](https://wokwi.com/projects/new/arduino-uno). Los archivos de la carpeta `simulador` están preparados para esta prueba:

1. Copia `simulador/sketch.ino` al editor `sketch.ino` de Wokwi.
2. Copia `simulador/diagram.json` al editor `diagram.json`.
3. Pulsa el botón verde para iniciar. No hace falta añadir bibliotecas. Tras 10 segundos aparece la primera lectura, `100.00` aproximadamente.
4. Haz clic en el HC-SR04 y mueve el control de distancia. El siguiente número debe reflejar el cambio.

Wokwi incluye el HC-SR04, así que el simulador usa el mismo sensor y el mismo programa que la placa física. La simulación verifica la lectura y la comunicación serial; no reproduce ecos perdidos, superficies blandas ni el ruido de un sensor real.

El Uno del navegador no crea un puerto USB en el Mac. Por tanto, el puente no puede leerlo indicando `/dev/cu...`.

### Simular también el recorrido hasta Grafana

La carpeta `simulador` incluye la configuración para **Wokwi en VS Code**, que permite compartir el puerto serial simulado con Python. Esta opción requiere una licencia de Wokwi compatible; revisa sus [planes vigentes](https://wokwi.com/pricing) y una posible licencia educativa antes de usarla. La prueba en el navegador y el circuito físico no requieren contratar esta opción.

1. Instala VS Code y **Wokwi for VS Code** desde el gestor de extensiones. Activa la licencia de Wokwi siguiendo su [guia oficial](https://docs.wokwi.com/vscode/getting-started).
2. Abre la carpeta `simulador` como proyecto en VS Code.
3. Compila el programa en el navegador Wokwi (prueba sencilla anterior) y, desde su editor, pulsa **F1**, busca **Download Compiled Firmware** y guárdalo como `simulador/firmware.hex`. El paquete no incluye este archivo: el firmware anterior era del sensor de temperatura y se retiró.
4. Ejecuta **Wokwi: Start Simulator**. El archivo `wokwi.toml` habilita el puerto serial simulado en el puerto 4000.
5. En otra Terminal, desde la carpeta principal y con el entorno Python activado, ejecuta:

```sh
python puente_mqtt.py --puerto rfc2217://localhost:4000
```

Si modificas el código, repite el paso 3 para sustituir `simulador/firmware.hex`. También se incluye `platformio.ini` para quien prefiera compilar con PlatformIO; en Macs con Apple Silicon ese compilador puede requerir Rosetta para ejecutar herramientas Intel.

Mantén la pestaña del simulador visible en VS Code; la simulación puede pausarse si queda oculta. Cambia la distancia del HC-SR04 virtual y comprueba que llegue a Grafana. Ejecuta un solo puente a la vez para no mezclar lecturas físicas y simuladas en el mismo tópico.

## 6. Comprobar y detener

Para ver si Telegraf consume y guarda datos:

```sh
docker compose logs --tail 30 telegraf
```

En el explorador de datos de InfluxDB puedes usar esta consulta Flux:

```flux
from(bucket: "distancia")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "distancia")
  |> filter(fn: (r) => r._field == "value")
  |> filter(fn: (r) => r.topic == "iot/raspberrypi/distancia")
  |> sort(columns: ["_time"])
```

Para una evidencia de la exposicion, registra una lectura en el puente, ubica ese valor y su hora en InfluxDB y toma una captura de Grafana. El HC-SR04 tiene una resolución práctica de unos 3 mm; imprimir dos decimales no aumenta su precisión.

Detén el puente con **Control + C**. Para detener los servicios conservando los datos:

```sh
docker compose down
```

Cuando quieras retomarlos usa `docker compose up -d` y vuelve a iniciar el puente. Las lecturas adquiridas mientras el puente esta apagado no se guardan. Este ejemplo no tiene almacenamiento permanente de lecturas pendientes; cortes y reconexiones pueden ocasionar lecturas perdidas o duplicadas.

## Si aparece un error

En la prueba de compilación local de este Mac apareció `Bad CPU type in executable` con una herramienta Intel. Si también ocurre al usar Arduino IDE o PlatformIO, sigue el [procedimiento oficial de Apple para Rosetta](https://support.apple.com/es-es/102527). La simulación web permite avanzar mientras resuelves esa compatibilidad.

| Problema | Acción |
| --- | --- |
| `ERR_HCSR04` | Revisa VCC, GND, Trig en D9 y Echo en D8. Apunta a una superficie dura entre 2 y 400 cm. Desconecta USB antes de cambiar cables. |
| No aparece el puerto | Comprueba el cable USB de datos, adaptador y selección del puerto en Arduino IDE. |
| Puerto ocupado | Cierra Monitor Serie, Serial Plotter y cualquier otro programa que use el Uno. |
| Docker no responde | Abre Docker Desktop y espera a que termine de iniciar. |
| EMQX no responde | Revisa `docker compose ps` y que MQTT use el puerto de `.env`. |
| Grafana muestra `No data` | Comprueba primero el puente, luego Telegraf e InfluxDB; espera las primeras muestras. Si venías de la versión de temperatura, crea el bucket `distancia` (sección 3). |
| La última lectura desaparece | Ese panel solo consulta el ultimo minuto; confirma que sigue entrando información. |

## Fuentes técnicas

- [Arduino Uno R3](https://docs.arduino.cc/hardware/uno-rev3/).
- [`pulseIn()` en Arduino](https://docs.arduino.cc/language-reference/en/functions/advanced-io/pulseIn/) y [HC-SR04 en Wokwi](https://docs.wokwi.com/parts/wokwi-hc-sr04).
- [Hardware de Wokwi](https://docs.wokwi.com/getting-started/supported-hardware) y [puerto serial hacia Python](https://docs.wokwi.com/vscode/project-config).
- [pySerial](https://pyserial.readthedocs.io/en/latest/shortintro.html) y [Paho MQTT](https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html).
- [Telegraf MQTT](https://docs.influxdata.com/telegraf/v1/input-plugins/mqtt_consumer/), [InfluxDB 2 en Docker](https://docs.influxdata.com/influxdb/v2/install/?t=Docker) y [provisión de Grafana](https://grafana.com/docs/grafana/latest/administration/provisioning/).

La configuración de los servicios esta preparada para ejecutarse. Consulta `VALIDACION.md` para distinguir las pruebas realizadas de las verificaciones que requieren el montaje físico o iniciar Docker.
