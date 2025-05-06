#include <util/delay.h>

// PB4 OUTPACK (INT4) INPUT
// PB5 INPEN (INT5) INPUT
// PB6 RESET INPUT
// PB7 SNW OUTPUT


// ====================== CONFIGURACIÓN DE REGISTROS ======================
#define SNW_BIT PE5
#define SNW_PORT PORTE
#define SNW_DDR DDRE

// ====================== VARIABLES GLOBALES ======================
volatile uint8_t receivedData[3];
volatile uint8_t dataIndex = 0;
volatile bool packetReady = false;

// ====================== CONFIGURACIÓN INICIAL ======================
void setup() {
  // Inicializar Serial (USB)
  Serial.begin(500000);

  // Configuración de puertos de datos
  // OUTPUT BUS - ENTRADAS
  DDRA = 0x00;
  DDRK = 0x00;
  DDRF = 0x00;
  // Habilito pullups
  PORTA = 0xFF;
  PORTK = 0xFF;
  PORTF = 0xFF;

  PORTE = 0xFF;

  // INPUT BUS - SALIDAS
  DDRB = 0xFF;
  DDRL = 0xFF;
  DDRC = 0xFF;

  //pinMode(LED_BUILTIN, OUTPUT);

  PORTB = 0x00;
  PORTL = 0x00;
  PORTC = 0x00;

  // Configuración de pines de control
  SNW_DDR |= (1 << SNW_BIT);
  SNW_PORT |= (1 << SNW_BIT);

  // Interrupción externa (igual que antes)
  EICRB |= (1 << ISC41);
  EIMSK |= (1 << INT4);

  sei();  // Habilitar interrupciones globales
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

  //digitalWrite(LED_BUILTIN, HIGH);  // LED ON cuando llega algo

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
  send12Bits(high12);
  send12Bits(low12);
}

void test_output_port() {
  PORTB = 0xff;
  PORTL = 0xff;
  PORTC = 0xff;
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

  // Enviar marco de datos con cabecera y checksum
  Serial.write(0x40);  // Cabecera
  Serial.write(porta);
  Serial.write(portk);
  Serial.write(portf);
  delay(1000);
}

// ====================== LOOP PRINCIPAL ======================
void loop() {
  /*
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
 */
  // Manejamos OUTPACK
  SNW_PORT &= ~(1 << SNW_BIT);  // Habilitar SNW (LOW)
                                // Si OUTPACK (PJ1) esta activo, envio los 24 bits
  while (PINE & (1 << PE1)) {   // Mientras PE1 está HIGH (1)
                                // Código cuando OUTPACK está ACTIVO (HIGH)
  }
  if (!(PINE & (1 << PE1))) {
    SNW_PORT |= (1 << SNW_BIT);  // Deshabilitar SNW (HIGH)
    send24BitsSplit();
    //delayMicroseconds(1);
    //delay(1000);
  }
}
