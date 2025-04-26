// Definición de puertos
uint8_t porta_bits;  // OUTPUT BUS U01-U08 (LSB)
uint8_t portk_bits;  // OUTPUT BUS U09-U16
uint8_t portf_bits;  // OUTPUT BUS U17-U24 (MSB)

// Buffer para recepción (3 bytes big-endian)
uint8_t receivedData[3];
uint8_t dataIndex = 0;
bool newDataAvailable = false;

// Pines de control
const int OUTPACK = 14;  // OUTPUT PACKET (LOGICA NEGADA) OUTPUT BUS
const int INPEN = 15;    // INPUT ENABLE (LOGICA NEGADA) INPUT BUS
const int RESET = 16;    // RESET (LOGICA NEGADA) DISABLE DCL
const int SNW = 17;      // START NEW WORD (LOGICA NEGADA) OUTPUT BUS

// Función para enviar 12 bits en 2 bytes (justificado a derecha)
void send12Bits(uint16_t data) {
  Serial.write((data >> 8) & 0x0F);  // Byte alto: 0000 + bits 12-9
  Serial.write(data & 0xFF);         // Byte bajo: bits 8-1
}

// Función para leer y enviar los 24 bits divididos en 2x12 bits
void send24BitsSplit() {
  // Leer los puertos de salida
  portf_bits = PINF;  // U17-U24
  portk_bits = PINK;  // U09-U16
  porta_bits = PINA;  // U01-U08

  // Construir bloques de 12 bits
  uint16_t high12 = ((uint16_t)portf_bits << 4) | ((portk_bits >> 4) & 0x0F);  // U13-U24
  uint16_t low12 = ((portk_bits & 0x0F) << 8) | porta_bits;                    // U01-U12

  // Enviar primero los 12 bits altos (2 bytes)
  send12Bits(high12);

  // Luego los 12 bits bajos (2 bytes)
  send12Bits(low12);
}

// Procesar datos recibidos (3 bytes big-endian)
void processReceivedData() {
  if (newDataAvailable) {
    // Escribir en los puertos de entrada
    PORTD = receivedData[0];  // I17-I24 (MSB)
    PORTL = receivedData[1];  // I09-I16
    PORTC = receivedData[2];  // I01-I08 (LSB)

    newDataAvailable = false;
    dataIndex = 0;
  }
}

void setup() {
  Serial.begin(500000);

  // Configurar OUTPUT BUS como entradas
  DDRA = 0x00;  // U01-U08
  DDRK = 0x00;  // U09-U16
  DDRF = 0x00;  // U17-U24

  // Configurar INPUT BUS como salidas
  DDRC = 0xFF;  // I01-I08
  DDRL = 0xFF;  // I09-I16
  DDRD = 0xFF;  // I17-I24

  // Inicializar puertos en 0
  PORTC = 0x00;
  PORTL = 0x00;
  PORTD = 0x00;

  // Configurar pines de control
  pinMode(OUTPACK, INPUT);
  pinMode(INPEN, INPUT);
  pinMode(RESET, INPUT);
  pinMode(SNW, OUTPUT);
  digitalWrite(SNW, HIGH);
}

void loop() {
  // Seleccionar el inicio de una nueva palabra de salida
  digitalWrite(SNW, LOW);
  // Leer y enviar OUTPUT BUS cuando OUTPACK está activo
  if (digitalRead(OUTPACK) == LOW) {
    // deshabilitar nuevas palabras de salidas hasta terminar de procesar
    digitalWrite(SNW, HIGH);
    send24BitsSplit();
  }

  // Si INPEN esta activo indica que se tiene que enviar al INPUT BUS el dato de posicion del lightpen (creo que lo hace cada 120ms)
  if (digitalRead(INPEN) == LOW) {
    if (dataIndex >= 3) {
      newDataAvailable = true;
      processReceivedData();
    }
  }

  // Recepción de datos (3 bytes big-endian)
  if (Serial.available() > 0) {
    receivedData[dataIndex++] = Serial.read();
  }
}
