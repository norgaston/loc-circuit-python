import numpy as np
import cv2
import serial
import threading
from font import *

# Función para decodificar caracteres
def decode_char(value):
    char_code = value & 0x7F       # Bits 6-0: ASCII
    borders = (value >> 7) & 0x7   # Bits 9-7: bordes
    color = (value >> 10) & 0x3    # Bits 11-10: color
    return char_code, borders, color
 
def draw_char(img, col, row, char_code, borders, color):
    start_x, start_y = col * CHAR_WIDTH, row * CHAR_HEIGHT
    
    # Dibujar fondo
    img[start_y:start_y+CHAR_HEIGHT, start_x:start_x+CHAR_WIDTH] = COLOR_MAP[color]
    
    # Dibujar bordes
    if borders & 0b100: img[start_y+CHAR_HEIGHT-1, start_x:start_x+CHAR_WIDTH] = (128, 128, 128) # abajo
    if borders & 0b010: img[start_y:start_y+CHAR_HEIGHT, start_x] = (128, 128, 128) # izquierda
    if borders & 0b001: img[start_y, start_x:start_x+CHAR_WIDTH] = (128, 128, 128) # arriba
    
    # Versión compatible con strings y números
    char = chr(char_code)
    if char in font_7x10:
        glyph = font_7x10[char]
        for y in range(min(len(glyph), CHAR_HEIGHT-2)):
            row_data = glyph[y]
            # Manejar tanto strings como números
            if isinstance(row_data, str):
                for x in range(min(len(row_data), CHAR_WIDTH-2)):
                    if row_data[x] == '1':
                        img[start_y+2+y, start_x+2+x] = (128, 128, 128)
            else:  # Suponer que es numérico
                for x in range(min(8, CHAR_WIDTH-2)):
                    if row_data & (1 << (7 - x)):
                        img[start_y+1+y, start_x+1+x] = (128, 128, 128)

def serial_receiver():
    buffer = bytearray()
    state = "WAIT_STX"
    current_row = 1  # Default (1-based)
    current_col = 1  # Default (1-based)
    packet_active = False
    
    # Constantes de control (12 bits)
    STX = 0x002
    VT = 0x00B
    HT = 0x009
    ETX = 0x003
    
    def get_word(data):
        """Combina 2 bytes en una palabra de 16 bits y aplica máscara de 12 bits"""
        return (data[0] << 8 | data[1]) & 0x0FFF
    
    def decode_position(word):
        """Decodifica RN/CN (000001xxxxxx) a posición 1-based"""
        return (word & 0x3F) + 1
    
    while True:
        # Leer datos del serial
        data = ser.read(ser.in_waiting or 1)
        if data:
            buffer.extend(data)
        
        # Procesar buffer mientras tengamos al menos 2 bytes
        while len(buffer) >= 2:
            word = get_word(buffer[:2])
            buffer = buffer[2:]  # Consumir los bytes procesados
            
            if state == "WAIT_STX":
                if word == STX:
                    packet_active = True
                    state = "IN_PACKET"
                    #print("\nInicio de paquete detectado")
            
            elif state == "IN_PACKET":
                if word == ETX:
                    packet_active = False
                    state = "WAIT_STX"
                    #print("Fin de paquete detectado\n")
                
                elif word == VT:
                    state = "READ_ROW"
                
                elif word == HT:
                    state = "READ_COL"
                
                elif packet_active:
                    # Procesar como carácter
                    char_data = word
                    with vram_lock:
                        if 1 <= current_row <= ROWS and 1 <= current_col <= COLS:
                            vram[current_row-1, current_col-1] = char_data
                            #print(f"Carácter 0x{char_data:03X} en ({current_row}, {current_col})")
                            current_col += 1
                            if current_col > COLS:
                                current_col = 1
                                current_row += 1
                                if current_row > ROWS:
                                    current_row = 1
            
            elif state == "READ_ROW":
                current_row = decode_position(word)
                #print(f"Nueva fila: {current_row}")
                state = "IN_PACKET"
            
            elif state == "READ_COL":
                current_col = decode_position(word)
                #print(f"Nueva columna: {current_col}")
                state = "IN_PACKET"

# Callback para clics del mouse
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        #print(f"\nClick en coordenadas: x={x}, y={y}")

        col, row = x // CHAR_WIDTH, y // CHAR_HEIGHT
        if 0 <= col < COLS and 0 <= row < ROWS:
            with vram_lock:
                value = vram[row][col]  # Asegurate que vram sea lista de listas o np.array

            char_code, borders, color = decode_char(value)

            print(f"\nFila {row+1}, Columna {col+1}")
            print(f"Point: {(x%10)+1} Line: {(y%14)+1}")
            #print(f"Carácter: {char_code} ('{chr(char_code) if 32 <= char_code < 127 else ' '}')")            
            #print(f"Bordes: Superior={bool(borders & 0b100)}, Izquierdo={bool(borders & 0b010)}, Inferior={bool(borders & 0b001)}")
            #print(f"Color: {['Negro', 'Gris', 'Blanco', 'Negro'][color]}")

            data = pack_data(
                            valid=True,
                            lightpen_active=True,
                            column=col,     # 6 bits (0-63)
                            points=6,       # 3 bits (0-7)
                            row=row,        # 6 bits (0-63)
                            lines=8         # 3 bits (0-7)
                            )
            send_24bits(data)

def send_24bits(data):    
    ser.write(data)
    print(f"Enviados: {data.hex()}")

def pack_data(valid, lightpen_active, column, points, row, lines):
    # Validar rangos de los parámetros
    if not isinstance(valid, bool) or not isinstance(lightpen_active, bool):
        raise ValueError("valid y lightpen_active deben ser booleanos")
    if column < 0 or column > 63:
        raise ValueError("Columna debe estar entre 0 y 63")
    if points < 0 or points > 14 or points % 2 != 0:
        raise ValueError("Points debe ser par entre 0 y 14")
    if row < 0 or row > 63:
        raise ValueError("Row debe estar entre 0 y 63")
    if lines < 0 or lines > 14 or lines % 2 != 0:
        raise ValueError("Lines debe ser par entre 0 y 14")

    # Construir el paquete de 24 bits
    data = 0
    data |= valid << 23
    data |= lightpen_active << 22
    data |= (column & 0x3F) << 16           # 6 bits para columna (0-63)
    data |= ((points // 2) & 0x07) << 13    # 3 bits para puntos (8,4,2)
    data |= (row & 0x3F) << 4               # 6 bits para fila (0-63)
    data |= ((lines // 2) & 0x07) << 1      # 3 bits para líneas (8,4,2)

    print(f"Bits enviados: {data:024b}")
    
    # Convertir a 3 bytes (big-endian)
    return data.to_bytes(3, byteorder='big')

# Configuración de comunicación serial
SERIAL_PORT = '/dev/ttyUSB0'
BAUDRATE = 500000

# Configuración de la pantalla
COLS, ROWS = 64, 41
CHAR_WIDTH, CHAR_HEIGHT = 10, 14
SCREEN_WIDTH, SCREEN_HEIGHT = 631, ROWS * CHAR_HEIGHT

# Mapa de colores (BF1-BF2)
COLOR_MAP = {
    0b00: (0, 0, 0),       # Negro
    0b01: (128, 128, 128), # Gris
    0b10: (255, 255, 255), # Blanco
    0b11: (0, 0, 0)        # Negro
}

# Inicializar VRAM
vram = np.zeros((ROWS, COLS), dtype=np.uint16)
vram_lock = threading.Lock()

# Iniciar serial
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)

# Iniciar hilo serial
serial_thread = threading.Thread(target=serial_receiver, daemon=True)
serial_thread.start()

# Configurar ventana y callback de mouse
cv2.namedWindow('Video LCC', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Video LCC', SCREEN_WIDTH, SCREEN_HEIGHT)
cv2.setMouseCallback('Video LCC', mouse_callback)

# Inicializar cámara
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    print("Error al abrir la cámara")
    exit()

"""
C0 = 0b000;  # nada
C1 = 0b001;  # arriba
C2 = 0b010;  # izquierda
C3 = 0b011;  # arriba-izquierda
C4 = 0b100;  # abajo
C5 = 0b101;  # arriba-abajo
C6 = 0b110;  # izquierda-abajo
C7 = 0b111;  # arriba-izquierda-abajo

vram[2][0] = ord('A') | (C3 << 7) | (0b11 << 10)
vram[2][1] = ord('/') | (C1 << 7) | (0b11 << 10)
vram[2][2] = ord('N') | (C1 << 7) | (0b11 << 10)
vram[2][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[3][0] = ord('P') | (C6 << 7) | (0b11 << 10)
vram[3][1] = ord('A') | (C4 << 7) | (0b11 << 10)
vram[3][2] = ord('G') | (C4 << 7) | (0b11 << 10)
vram[3][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
"""


# Bucle principal
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error de captura")
        break
    
    # Redimensionar y convertir frame
    frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay = frame.copy()
    
    # Dibujar caracteres desde VRAM
    with vram_lock:
        for row in range(ROWS):
            for col in range(COLS):
                if vram[row, col] != 0:
                    char_code, borders, color = decode_char(vram[row, col])
                    draw_char(overlay, col, row, char_code, borders, color)
    
    # Mezclar overlay con transparencia
    cv2.addWeighted(overlay, 0.99, frame, 0.1, 0, frame)
    
    # Mostrar resultado
    cv2.imshow('Video LCC', frame)
    
    # Salir con ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Limpieza
cap.release()
cv2.destroyAllWindows()
