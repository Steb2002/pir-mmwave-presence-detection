#include <Arduino.h>
#include <ld2410.h>

#define RADAR_RX_PIN 17
#define RADAR_TX_PIN 16
#define PIR_PIN 23
#define LED_PIN 2


HardwareSerial RadarSerial(2);
ld2410 radar;

unsigned long lastPrint = 0;
const unsigned long samplePeriodMs = 1000;

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(PIR_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  RadarSerial.begin(256000, SERIAL_8N1, RADAR_RX_PIN, RADAR_TX_PIN);

  if (radar.begin(RadarSerial)) {
    Serial.println("timestamp_ms,radar_presence,moving_target,stationary_target,moving_distance_cm,stationary_distance_cm,moving_energy,stationary_energy,pir_presence");
  } else {
    Serial.println("ERROR: radar not detected");
  }

}

void loop() {
  radar.read();

  unsigned long now = millis();

  if (now - lastPrint >= samplePeriodMs) {
    lastPrint = now;

    digitalWrite(LED_PIN, HIGH);

    int pirPresence = digitalRead(PIR_PIN);

    if (radar.movingTargetDetected()) {
      digitalWrite(LED_PIN, HIGH);
    } else {
      digitalWrite(LED_PIN, LOW);
    }


    Serial.print(now);
    Serial.print(",");

    Serial.print(radar.presenceDetected() ? 1 : 0);
    Serial.print(",");

    Serial.print(radar.movingTargetDetected() ? 1 : 0);
    Serial.print(",");

    Serial.print(radar.stationaryTargetDetected() ? 1 : 0);
    Serial.print(",");

    Serial.print(radar.movingTargetDistance());
    Serial.print(",");

    Serial.print(radar.stationaryTargetDistance());
    Serial.print(",");

    Serial.print(radar.movingTargetEnergy());
    Serial.print(",");

    Serial.print(radar.stationaryTargetEnergy());
    Serial.print(",");

    Serial.println(pirPresence);

  }
}