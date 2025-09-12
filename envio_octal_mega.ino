#include "vram.h"

// Pines de control
#define PIN_OUTPACK  6   // salida
#define PIN_SNW      7   // entrada
#define PIN_RESET    3   // salida
#define PIN_INPEN    2   // salida

void setup() {
  // Configurar puertos como salida
  DDRA = 0xFF;  // PORTA salida (parte alta)
  DDRK = 0xFF;  // PORTK salida (parte media)
  DDRF = 0xFF;  // PORTF salida (parte baja)

  pinMode(LED_BUILTIN, OUTPUT);

  // Pines de control
  pinMode(PIN_OUTPACK, OUTPUT);
  pinMode(PIN_RESET, OUTPUT);
  pinMode(PIN_INPEN, OUTPUT);
  pinMode(PIN_SNW, INPUT);

  digitalWrite(PIN_OUTPACK, HIGH); // OUTPACK inactivo (lógica negada)
  digitalWrite(PIN_RESET, HIGH); // RESET inactivo (lógica negada)

  Serial.begin(500000);
}

void loop() {
  for (int i = 0; i < cantidad_valores; i++) {
    // Los valores ya son interpretados como octales por el compilador.
    uint32_t value = valores[i];

    // Separar en 3 bytes
    uint8_t low  = value & 0xFF;          // bits 0..7
    uint8_t mid  = (value >> 8) & 0xFF;   // bits 8..15
    uint8_t high = (value >> 16) & 0xFF;  // bits 16..23

    // Cargar datos en los puertos
    PORTF = low;
    PORTK = mid;
    PORTA = high;

    // Feedback tx
    digitalWrite(LED_BUILTIN, HIGH);
    // Espero a que SNW baje (activo bajo)
    while (digitalRead(PIN_SNW) != LOW);  
    // Cuando SNW baja, pongo OUTPACK bajo (activo bajo)
    digitalWrite(PIN_OUTPACK, LOW); 
    // Espero a que SNW suba (inactivo)  
    while (digitalRead(PIN_SNW) != HIGH);
    // Con SNW inactivo , hago OUTPACK alto (inactivo)
    digitalWrite(PIN_OUTPACK, HIGH);
    // Feedback tx
    digitalWrite(LED_BUILTIN, LOW);
  }
  delay(5000);
}