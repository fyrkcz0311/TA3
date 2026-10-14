#include <DHT.h>

// Simulacion: Wokwi ofrece DHT22. La placa fisica usa DHT11.
const uint8_t PIN_SENSOR = 2;
const unsigned long INTERVALO_MS = 10000UL;
DHT sensor(PIN_SENSOR, DHT22);
unsigned long ultimaLectura = 0;

void setup() {
  Serial.begin(9600);
  sensor.begin();
}

void loop() {
  const unsigned long ahora = millis();
  if (ahora - ultimaLectura < INTERVALO_MS) return;
  ultimaLectura = ahora;

  const float temperatura = sensor.readTemperature();
  if (isnan(temperatura)) {
    Serial.println("ERR_DHT");
    return;
  }
  Serial.println(temperatura, 2);
}
