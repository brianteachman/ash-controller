/*
 * Arduino Room Controller
 * 
 * Arduino controller for driving an LED and PTC heating element 
 * using a photoresistor, PIR sensor, and DHT22 temperature sensor 
 * for feedback. Also uses a 12V DC fan and a servo to open/close
 * exhause vent.
 * 
 * Author:  Brian Teachman
 * Date:    12/8/2016
 */

#define SYS_MESSAGE 0
#define SYS_LIGHT 1
#define SYS_HEAT 2

const unsigned int DEVICE_ID = 0;   // main room
//const unsigned int DEVICE_ID = 1; // dining room

const unsigned int HOME_CONTROLLER = 99; // HC reference

//-----------------------------------------------------------

unsigned long previous_time = 0; // used for calculating run time

//-----------------------------------------------------------

const unsigned int ledPin = 9;
unsigned int ledBrightness = 0;
bool isLightOn = false;

//-----------------------------------------------------------

const unsigned int pirPin = 7; // Input for HC-S501
bool isMotion = false; // store PIR Value

//-----------------------------------------------------------

const unsigned int photocellPin = 0; // the cell and 10K pulldown are connected to a0
unsigned int photocellReading; // the analog reading from the sensor divider
double photocellVoltage;

//-----------------------------------------------------------

#include "DHT.h"
#define DHT_PIN 8     // what digital pin we're connected to
#define DHT_TYPE DHT22   // DHT 22  (AM2302), AM2321
DHT dht(DHT_PIN, DHT_TYPE);

//-----------------------------------------------------------

#include <Servo.h>
Servo fanServo;
const unsigned int fanPin = 5;
const unsigned int VENT_CLOSED = 30;
const unsigned int VENT_OPEN = 90;

//-----------------------------------------------------------

const unsigned int heaterPin = 13;
bool isHeatingOn = true;
bool isHeaterRunning = false; 
unsigned int heatSetpoint = 71; // default
float f; // current temp

//-----------------------------------------------------------

bool onState = false;

int subSystem; // 0=Messaging, 1=Lighting, 2=Heating

//-----------------------------------------------------------

void setup() {
  pinMode(fanPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(heaterPin, OUTPUT);
  pinMode(pirPin, INPUT);
  pinMode(photocellPin, INPUT);
  dht.begin();
  Serial.begin(115200);

  delay(2000);
  onState = true; // defaults to on
}

void loop() {
  
  // setup timer
  unsigned long this_time = millis();
  unsigned long running_time = this_time - previous_time;

  //--------------------------------------------------------

  isMotion = digitalRead(pirPin);
  if (isMotion) onState = true;

  //--------------------------------------------------------
  
  if ( onState )
  {
    if ( Serial.available() )
    {
      // check device ID
      if ( Serial.parseInt() == DEVICE_ID ) {  // 1 or 2
        
        // 2nd element, subSystem: 0=Messaging, 1=Lighting, 2=Heating
        subSystem = Serial.parseInt();

        // check system being called
        if ( subSystem == SYS_LIGHT )
        {
          // the set point, a value between 0 to 255
          ledBrightness = Serial.parseInt();

          // respond to Home Controller
          Serial.println( packCSV(HOME_CONTROLLER, SYS_LIGHT, ledBrightness) );
        }
        else if ( subSystem == SYS_HEAT )
        {
          // the set point, a value between ~70degF and 100degF
          heatSetpoint = Serial.parseInt();

          if ( heatSetpoint == 0 ) { turnOffHeatingSystem(); }

          // respond to Home Controller
          Serial.println( packCSV(HOME_CONTROLLER, SYS_HEAT, heatSetpoint) );
        }
        else if ( subSystem == SYS_MESSAGE )
        {
          int message_code = Serial.parseInt();
          
          switch ( message_code ) {
            // message codes will be converted to {'device': 1,'system': 0,'state': 75}
            
            case 0: // what is the temperature?
              Serial.println( packCSV(HOME_CONTROLLER, SYS_HEAT, (int) getCurrentTemp()) );
              break;

            case 1: // are any heaters running?
              if ( isHeaterRunning ) {
                Serial.println( packCSV(HOME_CONTROLLER, SYS_HEAT, 1) );
              }
              else {
                Serial.println( packCSV(HOME_CONTROLLER, SYS_HEAT, 0) );
              }
              break;

            case 2: // what is the temperature set to?
              Serial.println( packCSV(HOME_CONTROLLER, SYS_HEAT, (int) heatSetpoint) );
              break;

            case 3: // what is the light on?
              if ( isLightOn ) {
                Serial.println( packCSV(HOME_CONTROLLER, SYS_LIGHT, 1 ) );
              }
              else {
                Serial.println( packCSV(HOME_CONTROLLER, SYS_LIGHT, 0 ) );
              }
              break;

            case 4: // is anyone in the room?
              Serial.println( packCSV(HOME_CONTROLLER, SYS_MESSAGE, (int) isMotion ) );
              break;
            
            default:
              // not found error code
              Serial.println( packCSV(HOME_CONTROLLER, SYS_MESSAGE, 400) );
              break;
          }
        }
      }
    }
  }

  runLightController(ledBrightness);
  runTempController(heatSetpoint);
  
  delay(10); // Small delay for stability
}


//- Lighting API ----------------------------------------------------------


int runLightController(int light_level) {

  if ( light_level == 0 ) {
    isLightOn = false;
  }
  else {
    isLightOn = true;
  }
  
  // set the brightness of the LED:
  analogWrite(ledPin, light_level);
  return light_level;
}

int getLightLevel() {
  return ledBrightness;
}

// Returns a light level from photocell (range: 0 - 255)
int ambientLightLevel() {
  photocellReading = analogRead(photocellPin);
  photocellVoltage = photocellReading / 204.6;
  
  // LED gets brighter the darker it is at the sensor
  // so, invert reading from 0-1023 back to 1023-0
  photocellReading = 1023 - photocellReading;

  photocellReading /= 2;
  
  // map 0-1023 (8 bits) to 0-255 since thats the range analogWrite uses
  return map(photocellReading, 0, 1023, 0, 255);
}


//- Heating API ----------------------------------------------------------


void runTempController(int set_point) {

//  int upper_threshold = set_point + ( set_point * 0.03)
//  int lower_threshold = set_point - ( set_point * 0.03)

  f = readCurrentTemp();
  if ( isnan(f) || f < 30.0 ) {  // if no DHT reading
    Serial.println( packCSV(HOME_CONTROLLER, SYS_HEAT, 500) ); // error 400: could not read sensor
    return;
  }
  if ( isHeatingOn ) { 
    if ( (int) f < set_point ) {
      setVentilation(false);          // close vents, kill fan
      digitalWrite(heaterPin, HIGH);  // turn on heater
      if ( ! isHeaterRunning ) isHeaterRunning = true;
    }
    else if( (int) f >= set_point ) {
      setVentilation(true);           // open vents, run fan
      digitalWrite(heaterPin, LOW);   // turn off heater
      if ( isHeaterRunning ) isHeaterRunning = false;
    }
  }
}

float readCurrentTemp() {
  return dht.readTemperature(true); // read DHT sensor
}

void setVentilation(bool on) {
  if ( on ) {
    fanServo.write(VENT_OPEN);    // Turn servo motor to 90 Degrees from Center (Range from 0 - 180 represents 0 -170 degrees)
    delay(500);                   // Wait half a second for servo to close all the way
    analogWrite(fanPin, 255);     // Turn Fan on PWM pin 6 all the way on. (Duty cycle ranges from 0-255, 0 percent duty cycle to 100 percent duty cycle, respectively)
  }
  else {
    fanServo.write(VENT_CLOSED); // Turn servo motor to 0 Degrees from Center (Range from 0 - 180 represents 0 -170 degrees)
    delay(500);                  // Wait half a second for servo to open all the way
    analogWrite(fanPin, 0);      // Turn Fan on PWM pin 6 all the way off. (Duty cycle ranges from 0-255, 0 percent duty cycle to 100 percent duty cycle, respectively)
  }
}

void turnOffHeatingSystem() {
  digitalWrite(heaterPin, LOW);
  analogWrite(fanPin, 0);
  isHeaterRunning = false;
  isHeatingOn = false;
}

float getCurrentTemp() { return f; }

float getTempSetPoint() { return heatSetpoint; }


//-----------------------------------------------------------------------

// Read and return UART data as string upto newline chatacter
String fetchSerialString() {
  String str = "\0";
  if(Serial.available() > 0)
  {
      str = Serial.readStringUntil('\n');
  }
  return str;
}

String packCSV(int device, int sub_system, int state) {
  return String(device) + "," + String(sub_system) + "," + String(state);
}

Serial.println( packCSV(DEVICE_ID, SYS_HEAT, current_temp) );

void printLoading(int load_time) {
  // give the sensor some time to calibrate
  Serial.print(" Setting things up ");
  for (int i = 0; i < load_time; i++) {
    Serial.print(".");
    delay(1000);    // BEWARE: blocking delay
  }
  Serial.println(" complete.");
  Serial.println("SENSOR ACTIVE");
}
