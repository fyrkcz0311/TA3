// Placa fisica: Arduino Uno + HC-SR04. TRIG en D9 y ECHO en D8. No requiere bibliotecas.
const uint8_t PIN_TRIG = 9;
const uint8_t PIN_ECHO = 8;
const unsigned long INTERVALO_MS = 1000UL;
// Eco maximo esperado: unos 4 m de ida y vuelta (~23 ms). Si tarda mas, no hubo eco.
const unsigned long ESPERA_ECO_US = 30000UL;
const float DISTANCIA_MIN_CM = 2.0;
const float DISTANCIA_MAX_CM = 400.0;
unsigned long ultimaLectura = 0;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  digitalWrite(PIN_TRIG, LOW);
}

void loop() {
  const unsigned long ahora = millis();
  if (ahora - ultimaLectura < INTERVALO_MS) return;
  ultimaLectura = ahora;

  // Pulso de disparo de 10 us; el sensor responde con un pulso de duracion proporcional a la distancia.
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  const unsigned long duracion = pulseIn(PIN_ECHO, HIGH, ESPERA_ECO_US);
  // Sonido a ~343 m/s = 0.0343 cm/us; se divide entre 2 por la ida y vuelta.
  const float distancia = duracion * 0.0343 / 2.0;
  if (duracion == 0 || distancia < DISTANCIA_MIN_CM || distancia > DISTANCIA_MAX_CM) {
    Serial.println("ERR_HCSR04");
    return;
  }
  // Solo el numero, en centimetros; Python lo publica en MQTT.
  Serial.println(distancia, 2);
}
