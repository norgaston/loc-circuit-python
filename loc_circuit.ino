uint8_t portd_bits;  // PD2-PD7 (6 bits)
uint8_t portb_bits;  // PB0-PB5 (6 bits)
uint16_t data;       // Para combinar en un valor de 12 bits
// Buffer para almacenar los 24 bits (3 bytes)
uint8_t receivedData[3];
bool newDataAvailable = false;


int OUTPACK = 14;
int INPEN = 15;
int SNW = 16;
int MUX = 17;
int DATA595 = 18;
int CLOCK595 = 19;
int LATCH595 = 20;

void send12Bits(uint16_t data) {
  // Asegurar que solo usamos 12 bits en parte BAJA
  data &= 0x0FFF;
  // Enviar en BIG-ENDIAN (MSB primero)
  Serial.write((data >> 8) & 0xFF);  // Bits 11-8
  Serial.write(data & 0xFF);         // Bits 7-0
}

void sendDataMu(byte receivedData[3]) {
  // Enviar los datos
  digitalWrite(LATCH595, LOW);  // Preparar el registro

  // Enviar del último al primero
  for (int i = 2; i >= 0; i--) {
    shiftOut(DATA595, CLOCK595, MSBFIRST, receivedData[i]);
  }

  digitalWrite(LATCH595, HIGH);  // Cargar los datos al registro de salida
}

void setup() {
  Serial.begin(500000);
  // Configurar PORTD PD2 a PD7 como entradas, TX la dejo como salida
  DDRD = B00000001;
  //PORTD = B11111111; // Habilito las pull-ups

  // Configurar PORTB PB0 a PB5 como entradas
  DDRB = B00000000;
  //PORTB = B11111111; // Habilito las pull-ups

  // Configurar los pines de control como entradas y salida

  pinMode(OUTPACK, INPUT);
  pinMode(INPEN, INPUT);
  pinMode(SNW, OUTPUT);
  pinMode(MUX, OUTPUT);
  pinMode(DATA595, OUTPUT);
  pinMode(CLOCK595, OUTPUT);
  pinMode(LATCH595, OUTPUT);
}

void loop() {
  if (OUTPACK) {
    digitalWrite(SNW, 0);
    digitalWrite(MUX, 0);
    // Leer los 12 bits (6 de PORTD + 6 de PORTB)
    portd_bits = (PIND & 0xFC) >> 2;  // PD2-PD7 (6 bits)
    portb_bits = PINB & 0x3F;         // PB0-PB5 (6 bits)

    // Combinar en un valor de 12 bits
    data = (portd_bits << 6) | portb_bits;

    // Enviar los dos bytes
    Serial.write((uint8_t)(data >> 8));    // Byte alto (4 bits relevantes)
    Serial.write((uint8_t)(data & 0xFF));  // Byte bajo (8 bits)

    digitalWrite(MUX, 1);

    portd_bits = (PIND & 0xFC) >> 2;  // PD2-PD7 (6 bits)
    portb_bits = PINB & 0x3F;         // PB0-PB5 (6 bits)

    // Combinar en un valor de 12 bits
    data = (portd_bits << 6) | portb_bits;

    // Enviar los dos bytes
    Serial.write((uint8_t)(data >> 8));    // Byte alto (4 bits relevantes)
    Serial.write((uint8_t)(data & 0xFF));  // Byte bajo (8 bits)

    digitalWrite(SNW, 1);
  }
  // Si tengo nuevos datos los envío a la SMR-MU
  if (INPEN) {
    if (newDataAvailable) {
      sendDataMu(receivedData[3]);
      newDataAvailable = false;
    }
  }
  // Recibir datos por serial
  if (Serial.available() >= 3) {
    for (int i = 0; i < 3; i++) {
      receivedData[i] = Serial.read();
    }
    newDataAvailable = true;
  }
}
