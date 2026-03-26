#include "DHT.h"
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

// --- SENSOR SETUP ---
#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// --- LCD SETUP ---
// Most I2C screens use 0x27. If it's completely blank after adjusting the blue dial, try 0x3F.
LiquidCrystal_I2C lcd(0x27, 16, 2); 

// --- TIMING VARIABLES ---
unsigned long previousMillis = 0;
const long interval = 2000; // 2 seconds (The absolute minimum for a DHT22)

void setup() {
  Serial.begin(9600);
  
  // Start the sensor
  dht.begin();
  
  // Start the LCD
  lcd.init();       // Note: If your specific library gives an error here, change to lcd.begin()
  lcd.backlight();
  
  // Quick startup message to verify the screen works
  lcd.setCursor(0, 0);
  lcd.print("System Booting..");
  Serial.println("System Booting..");
  delay(2000); 
  lcd.clear();
}

void loop() {
  // Check the current time
  unsigned long currentMillis = millis();

  // Non-blocking timer: only read the sensor if 2 seconds have passed
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis; // Reset the timer

    // Read data
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();

    // Safety check: Did the sensor disconnect?
    if (isnan(temp) || isnan(hum)) {
      Serial.println("Error: Failed to read from DHT sensor!");
      lcd.setCursor(0, 0);
      lcd.print("Sensor Error!   ");
      return;
    }

    // Print to Serial Monitor as JSON
    Serial.print("{\"temperature\": ");
    Serial.print(temp);
    Serial.print(", \"humidity\": ");
    Serial.print(hum);
    Serial.println("}");

    // Print to LCD - Top Row
    lcd.setCursor(0, 0); 
    lcd.print("Temp: ");
    lcd.print(temp, 1);   // Show only 1 decimal place
    lcd.print((char)223); // Degree symbol
    lcd.print("C  ");     // Extra spaces to clear any leftover characters

    // Print to LCD - Bottom Row
    lcd.setCursor(0, 1); 
    lcd.print("Hum:  ");
    lcd.print(hum, 1);
    lcd.print("%   ");
  }
  
  // You can add other code down here later, and it will run instantly!
}