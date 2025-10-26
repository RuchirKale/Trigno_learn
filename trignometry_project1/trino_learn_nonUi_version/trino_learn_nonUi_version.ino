#include <Servo.h>
#include <math.h>

#define TRIG_PIN 9
#define ECHO_PIN 10
#define POT_PIN A0
#define SERVO_PIN 6

Servo servo;

int prevPotValue = -1;
int prevDistance = -1;

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  servo.attach(SERVO_PIN);

  Serial.println("=== TRIGONOMETRIC SCANNER v6 ===");
  Serial.println("System Status: ONLINE");
  Serial.println("--------------------------------");
}

void loop() {
  // --- Read potentiometer ---
  int potValue = analogRead(POT_PIN);
  
  // --- Read ultrasonic distance ---
  long duration;
  int distance;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  duration = pulseIn(ECHO_PIN, HIGH, 40000); // timeout ~400cm
  if (duration == 0) {
    Serial.println("⚠️ 404: Ultrasonic Sensor Not Found or Out of Range");
    delay(500);
    return;
  }

  distance = duration * 0.034 / 2;
  distance = constrain(distance, 5, 400);

  // --- Update only if pot or distance changed significantly ---
  if (abs(potValue - prevPotValue) > 4 || abs(distance - prevDistance) > 2) {
    prevPotValue = potValue;
    prevDistance = distance;

    // --- Base angle & trig calculations ---
    float baseAngle = map(potValue, 0, 1023, 0, 90);
    float radians = baseAngle * (3.1416 / 180.0);

    float sineVal = sin(radians);
    float cosineVal = cos(radians);
    float tangentVal = tan(radians);

    // --- Map distance + trig to servo angle ---
    int servoAngle = map(distance, 5, 400, 0, 180);
    servoAngle += sineVal * 30 + cosineVal * 20;
    servoAngle = constrain(servoAngle, 0, 180);

    // --- Move servo ---
    servo.write(servoAngle);

   // --- Console Output with spacing ---
Serial.print("Distance: ");
Serial.print(distance);
Serial.print(" cm\t| Base Angle: ");
Serial.print(baseAngle);
Serial.print("°\t| sin: ");
Serial.print(sineVal, 2);
Serial.print("\t| cos: ");
Serial.print(cosineVal, 2);
Serial.print("\t| tan: ");
Serial.print(tangentVal, 2);
Serial.print("\t| Servo: ");
Serial.print(servoAngle);
Serial.println("°\n");  // extra line for vertical spacing
  }
  delay(100); // small delay for stability
}
