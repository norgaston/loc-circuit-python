#include <util/delay.h>

// ====================== CONFIGURACIÓN DE REGISTROS ======================
#define SNW_BIT PB0  // SNW en PB0 (pin 17)
#define SNW_PORT PORTB
#define SNW_DDR DDRB

// ====================== VARIABLES GLOBALES ======================
volatile uint8_t receivedData[3];
volatile uint8_t dataIndex = 0;
volatile bool packetReady = false;

// ====================== CONFIGURACIÓN INICIAL ======================
void setup() {
  // Inicializar Serial (USB)
  Serial.begin(500000);

  // Configuración de puertos de datos
  DDRA = 0x00;
  DDRK = 0x00;
  DDRF = 0x00;

  DDRC = 0xFF;
  DDRL = 0xFF;
  DDRD = 0xFF;

  pinMode(LED_BUILTIN, OUTPUT);

  PORTC = 0x00;
  PORTL = 0x00;
  PORTD = 0x00;

  // Configuración de pines de control
  SNW_DDR |= (1 << SNW_BIT);
  SNW_PORT |= (1 << SNW_BIT);

  // Interrupción externa (igual que antes)
  EICRB |= (1 << ISC51);
  EIMSK |= (1 << INT5);

  sei();  // Habilitar interrupciones globales

  // Blink inicial
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(300);
    digitalWrite(LED_BUILTIN, LOW);
    delay(300);
  }
}

// ====================== INTERRUPCIÓN PARA INPEN ======================
ISR(INT5_vect) {
  if (packetReady) {
    PORTD = receivedData[0];
    PORTL = receivedData[1];
    PORTC = receivedData[2];

    packetReady = false;
  }
}

// ====================== FUNCIONES DE TRANSMISIÓN ======================
void send12Bits(uint16_t data) {
  Serial.write((data >> 8) & 0x0F);
  Serial.write(data & 0xFF);
}

void send24BitsSplit() {
  uint16_t high12 = ((uint16_t)PINF << 4) | ((PINK >> 4) & 0x0F);
  uint16_t low12 = ((PINK & 0x0F) << 8) | PINA;

  send12Bits(high12);
  send12Bits(low12);
}

// ====================== LOOP PRINCIPAL ======================
void loop() {
  // Manejamos llegada de datos por USB
  while (Serial.available()) {
    receivedData[dataIndex++] = Serial.read();

    if (dataIndex >= 3) {
      dataIndex = 0;
      packetReady = true;
      if (receivedData[0] == '0' && receivedData[1] == '1' && receivedData[2] == '2') {
        digitalWrite(LED_BUILTIN, HIGH);  // LED ON cuando llega algo
        delay(100);
        digitalWrite(LED_BUILTIN, LOW);  // LED ON cuando llega algo
      }
    }
  }

  // Manejamos OUTPACK
  SNW_PORT &= ~(1 << SNW_BIT);  // Habilitar SNW (LOW)
  // Si OUTPACK (PJ1) esta activo, envio los 24 bits
  if (!(PINJ & (1 << PJ1))) {
    SNW_PORT |= (1 << SNW_BIT);  // Deshabilitar SNW (LOW)
    send24BitsSplit();
  }
}
