#include <util/delay.h>

// PE5 OUTPACK (INT5) INPUT
// PE4 INPEN (INT4) INPUT
// PH3 RESET INPUT
// PH4 SNW OUTPUT


// ====================== CONFIGURACIÓN DE REGISTROS ======================
#define SNW_BIT PH4
#define SNW_PORT PORTH
#define SNW_DDR DDRH

// ====================== VARIABLES GLOBALES ======================
volatile uint8_t receivedData[3];
volatile uint8_t dataIndex = 0;
volatile bool packetReady = false;

// ====================== CONFIGURACIÓN INICIAL ======================
void setup() {
  // Inicializar Serial (USB)
  Serial.begin(500000);

  // Configuración de puertos de datos
  // OUTPUT BUS - ENTRADAS 24 bits para leer lo que envía la SMR-MU
  // PORTF - parte baja
  // U01 -- 004
  // U02 -- 006
  // U03 -- 031
  // U04 -- 034
  // U05 -- 009
  // U06 -- 007
  // U07 -- 051
  // U08 -- 081
  // PORTK - parte media
  // U09 -- 064
  // U10 -- 049
  // U11 -- 043
  // U12 -- 039
  // U13 -- 028
  // U14 -- 029
  // U15 -- 033
  // U16 -- 032
  // PORTA - parte alta
  // U17 -- 050
  // U18 -- 024
  // U19 -- 053
  // U20 -- 083
  // U21 -- 063
  // U22 -- 088
  // U23 -- 061
  // U24 -- 041

  DDRA = 0x00;
  DDRK = 0x00;
  DDRF = 0x00;
  // Habilito pullups
  PORTA = 0xFF; // U17-U24 entras testeadas ok 26-08-25
  PORTK = 0xFF; // U09-U16
  PORTF = 0xFF; // U01-U08
  // INPUT BUS - SALIDAS 19 bits que envío con los datos de posición del LOC a la SMR-MU (vía DCL-SOCO)
  DDRB = 0xFF;
  DDRL = 0xFF;
  DDRC = 0xFF;
  // pongo las salidas en cero
  PORTB = 0x00;
  PORTL = 0x00;
  PORTC = 0x00;
  // Configuración de pines de control
  DDRE = 0x00;
  DDRH = 0x00;
  // Habilito pullups en PORTE y PORTH, donde están OUTPACK, INPEN y RESET
  PORTE = 0xFF;
  PORTH = 0xFF;
  // Configuri la salida "START NEW WORD"
  SNW_DDR |= (1 << SNW_BIT);
  SNW_PORT |= (1 << SNW_BIT);
  // Interrupción externa (igual que antes)
  //EICRB |= (1 << ISC41);
  //EIMSK |= (1 << INT4);
  //sei();  // Habilitar interrupciones globales
  /*
  // Blink inicial
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(300);
    digitalWrite(LED_BUILTIN, LOW);
    delay(300);
  }*/
}

// ====================== INTERRUPCIÓN PARA INPEN ======================
ISR(INT4_vect) {
  if (packetReady) {
    PORTB = receivedData[0];
    PORTL = receivedData[1];
    PORTC = receivedData[2];

    packetReady = false;
  }
}

// ====================== FUNCIONES DE TRANSMISIÓN ======================
/* 
 * Función para enviar un valor de 12 bits a través del puerto serial
 * Dividido en 4 bits altos + 8 bits bajos para eficiencia
 * 
 * @param data Valor de 16 bits (usaremos solo los 12 bits menos significativos)
 */
void send12Bits(uint16_t data) {
  // Envía los 4 bits más significativos del valor de 12 bits
  // 1. data >> 8: Desplaza 8 bits a la derecha para obtener el byte alto
  // 2. & 0x0F: Aplica máscara para quedarnos solo con los 4 bits menos significativos del byte alto
  Serial.write((data >> 8) & 0x0F);

  // Envía los 8 bits menos significativos del valor
  // data & 0xFF: Aplica máscara para obtener solo el byte bajo
  Serial.write(data & 0xFF);
}

/*
 * Función principal que lee los puertos y envía los 24 bits combinados
 * Divididos en dos valores de 12 bits (high12 y low12)
 */
void send24BitsSplit() {
  // 1. Construcción de los 12 bits altos (high12):
  // Combinamos los 8 bits de PORTA con los 4 bits altos de PORTK
  uint16_t high12 = ((uint16_t)PINA << 4) | ((PINK >> 4) & 0x0F);
  // - (uint16_t)PINA << 4: Convertimos PINA a 16 bits y desplazamos 4 posiciones a la izquierda
  // - (PINK >> 4) & 0x0F: Tomamos PORTK, desplazamos 4 bits derecha y aplicamos máscara para 4 bits

  // 2. Construcción de los 12 bits bajos (low12):
  // Combinamos los 4 bits bajos de PORTK con los 8 bits de PORTF
  uint16_t low12 = ((PINK & 0x0F) << 8) | PINF;
  // - (PINK & 0x0F) << 8: Tomamos los 4 bits bajos de PORTK y desplazamos 8 posiciones a la izquierda
  // - | PINF: Hacemos OR con el valor completo de PORTF

  // Enviamos ambas mitades de 12 bits usando nuestra función de envío


  // revisar que usa la misma funcion para enviar los 12 bits y esos 12 bits se componen distinto, de parte baja y alta del PORTK
  send12Bits(high12);
  send12Bits(low12);
}

void send24BitsFlat() {
  // Combinar los 24 bits planos
  uint32_t value24 = ((uint32_t)PINA << 16) | ((uint32_t)PINK << 8) | PINF;

  // Partir en 2 bloques de 12 bits
  uint16_t high12 = (value24 >> 12) & 0x0FFF;
  uint16_t low12  = value24 & 0x0FFF;

  send12Bits(high12);
  send12Bits(low12);
}


void test_output_port() {
  PORTB = 0x00; // parte baja
  PORTL = 0x80;
  PORTC = 0x80; // parte alta
  SNW_PORT |= (1 << SNW_BIT);
  delay(1000);
  PORTB = 0x00;
  PORTL = 0x00;
  PORTC = 0x00;
  SNW_PORT &= ~(1 << SNW_BIT);
  delay(1000);
}

void test_input_port() {
  // Leer puertos simultáneamente
  uint8_t porta = PINA;
  uint8_t portk = PINK;
  uint8_t portf = PINF;
  uint8_t porte = PINE;
  uint8_t porth = PINH;

  // Enviar marco de datos con cabecera
  Serial.write(0x40);  // Cabecera
  Serial.write(porta);
  Serial.write(portk);
  Serial.write(portf);
  Serial.write(porte);
  Serial.write(porth);
  delay(1000);
}

// ====================== LOOP PRINCIPAL ======================
void loop() {
  //Serial.write(0x52);
  //delay(1000);

  // Mientras no esté en RESET, o sea cuando RESET esté en 1 (pin 3 MEGA)
  //while (PINE & (1 << PE5)) {
    //Serial.write(0x40);
    //delay(1000);
    /*
  // Manejamos llegada de datos por USB (se envían en la interrupoción de INPEN)
  while (Serial.available()) {
    receivedData[dataIndex++] = Serial.read();

    if (dataIndex >= 3) {
      dataIndex = 0;
      packetReady = true;
      }
  }
 */
    // Manejamos OUTPACK
    SNW_PORT &= ~(1 << SNW_BIT);    // Habilitar SNW (LOW)
                                    // Si OUTPACK (PJ1) esta activo, envio los 24 bits
    while (PINH & (1 << PH3)) {     // OUTPACK em 1
    }
    if (!(PINH & (1 << PH3))) {     // si OUTPACK es 0
      SNW_PORT |= (1 << SNW_BIT);   // Deshabilitar SNW (HIGH)
      send24BitsSplit();            // leo los 24 bit y los envío
      //Serial.flush();
      //send24BitsFlat();
    }
 // }
}
