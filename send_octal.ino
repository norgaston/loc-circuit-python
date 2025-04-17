/*
STX: 000000000010 (0x002)
VT:  000000001011 (0x00B)
RN:  000001xxxxxx (bits: [00000][1][32][16][8][4][2][1])
HT:  000000001001 (0x009)
CN:  000001xxxxxx (bits: [00000][1][32][16][8][4][2][1])
CHAR: 12 bits (BF1-BF2 + bordes + ASCII)
ETX: 000000000011 (0x003)
*/

const char* octalData[] = {
  "00000002", 
  "00130100", 
  "00110140", 
  "00400124",
  "01230040", 
  "00640060", 
  "00400040", 
  "00400123",
  "00130101", 
  "00110140", 
  "00400124", 
  "01230040",
  "00670066", 
  "00400040", 
  "00400123",
  "00130102", 
  "00110140", 
  "00400040", 
  "00400040",
  "00400003"
};

const int numItems = sizeof(octalData) / sizeof(octalData[0]);
int currentIndex = 0;

// Constantes de control de 12 bits
const uint16_t STX = 0x002;
const uint16_t VT = 0x00B;
const uint16_t HT = 0x009;
const uint16_t ETX = 0x003;

void send12Bits(uint16_t data) {
  // Asegurar que solo usamos 12 bits en parte BAJA
  data &= 0x0FFF;
  // Enviar en BIG-ENDIAN (MSB primero)
  Serial.write((data >> 8) & 0xFF);  // Bits 11-8
  Serial.write(data & 0xFF);         // Bits 7-0
}

uint16_t encodePosition(uint8_t pos) {
  return 0x0040 | (pos - 1);  // Codificación RN/CN (000001xxxxxx)
}

void setup() {
  Serial.begin(500000);
}

void loop() {
  const char* currentOctal = octalData[currentIndex];
  
  // Convertir dato octal a 32 bits
  uint32_t fullValue = strtoul(currentOctal, NULL, 8);
  
  // Extraer dos palabras de 12 bits (24 bits útiles)
  uint16_t word1 = (fullValue >> 12) & 0x0FFF; // Primeros 12 bits
  uint16_t word2 = fullValue & 0x0FFF;         // Últimos 12 bits
  
  // Enviar ambas palabras
  send12Bits(word1);
  send12Bits(word2);

  currentIndex = (currentIndex + 1) % numItems;
  delay(10); // Ajustar según necesidad
}