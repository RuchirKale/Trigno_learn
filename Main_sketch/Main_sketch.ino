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
  Serial.begin(9600);   // PC communication
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  servo.attach(SERVO_PIN);
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

  duration = pulseIn(ECHO_PIN, HIGH, 40000); // Timeout ~400cm
  if (duration == 0) {
    // Sensor out of range; optionally could send a default angle
    return;
  }

  distance = duration * 0.034 / 2;
  distance = constrain(distance, 5, 400);

  // --- Update only if pot or distance changed ---
  if (abs(potValue - prevPotValue) > 4 || abs(distance - prevDistance) > 2) {
    prevPotValue = potValue;
    prevDistance = distance;

    // --- Base angle & trig calculations ---
    float baseAngle = map(potValue, 0, 1023, 0, 90);
    float radians = baseAngle * (3.1416 / 180.0);

    float sineVal = sin(radians);
    float cosineVal = cos(radians);

    // --- Map distance + trig to servo angle ---
    int servoAngle = map(distance, 5, 400, 0, 180);
    servoAngle += sineVal * 30 + cosineVal * 20;
    servoAngle = constrain(servoAngle, 0, 180);

    // --- Move servo ---
    servo.write(servoAngle);

    // --- Send only the angle to PC ---
    Serial.print("Angle:");
    Serial.println(servoAngle);
  }

  delay(100); // small delay for stability
}
