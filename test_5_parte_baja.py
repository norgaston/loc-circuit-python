#!/usr/bin/env python3
import numpy as np
import cv2
import serial
import threading
from font import *

# Configuración de comunicación serial
SERIAL_PORT = '/dev/ttyUSB0'
BAUDRATE = 500000

# Configuración de la pantalla
COLS, ROWS = 64, 41
CHAR_WIDTH, CHAR_HEIGHT = 10, 14
SCREEN_WIDTH, SCREEN_HEIGHT = COLS * CHAR_WIDTH, ROWS * CHAR_HEIGHT

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

# Función para decodificar caracteres
def decode_char(value):
    char_code = value & 0x7F       # Bits 6-0: ASCII
    borders = (value >> 7) & 0x7   # Bits 9-7: bordes
    color = (value >> 10) & 0x3    # Bits 11-10: color
    return char_code, borders, color

#!/usr/bin/env python3
import numpy as np
import cv2
import serial
import threading
from font import *   


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

def serial_receiver_():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    buffer = bytearray()
    
    while ser.is_open:
        try:
            data = ser.read(ser.in_waiting or 1)
            if data:
                buffer.extend(data)
                
                # Procesar paquetes completos (14 bytes)
                while len(buffer) >= 14:
                    # Decodificar palabras de 12 bits (big-endian) con máscara
                    words = [((buffer[i] << 8 | buffer[i+1]) & 0x0FFF) for i in range(0, 14, 2)]
                    
                    # Extraer posición y datos
                    row = (words[2] & 0x3F)  # 6 bits bajos (RN)
                    col = (words[4] & 0x3F)  # 6 bits bajos (CN)
                    char_data = words[5]      # CHAR sin desplazamiento
                    
                    # Ajustar índices (empiezan en 1)
                    row += 1
                    col += 1
                    
                    # Actualizar VRAM (verificar límites)
                    with vram_lock:
                        if 1 <= row <= ROWS and 1 <= col <= COLS:
                            vram[row-1, col-1] = char_data  # Índices 0-based
                    
                    buffer = buffer[14:]
                    
        except Exception as e:
            print(f"Error serial: {e}")
            break

def serial_receiver():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    buffer = bytearray()
    state = "WAIT_STX"
    current_row = 0
    current_col = 0
    
    # Constantes de 12 bits
    CONTROL_WORDS = {
        0x002: "STX",
        0x00B: "VT", 
        0x009: "HT",
        0x003: "ETX"
    }

    def process_word(word):
        nonlocal current_row, current_col
        if word in CONTROL_WORDS:
            return CONTROL_WORDS[word]
        
        # Decodificar RN/CN (000001xxxxxx)
        if (word & 0xFC0) == 0x040:  # Máscara 111111000000
            return ("POS", word & 0x3F)  # Extraer 6 bits bajos
        
        # Carácter normal
        return ("CHAR", word)

    while True:
        data = ser.read(ser.in_waiting or 1)
        if data:
            buffer.extend(data)
        
        while len(buffer) >= 2:
            word = (buffer[0] << 8) | buffer[1]
            buffer = buffer[2:]
            
            res = process_word(word & 0x0FFF)  # Solo 12 bits
            
            if state == "WAIT_STX":
                if res == "STX":
                    state = "HEADER"
                    
            elif state == "HEADER":
                if res[0] == "POS":
                    current_row = res[1] + 1  # 1-based
                    state = "HEADER_COL"
                    
            elif state == "HEADER_COL":
                if res[0] == "POS":
                    current_col = res[1] + 1
                    state = "DATA"
                    
            elif state == "DATA":
                if res == "ETX":
                    state = "WAIT_STX"
                elif res[0] == "CHAR":
                    with vram_lock:
                        if current_row <= ROWS and current_col <= COLS:
                            vram[current_row-1, current_col-1] = res[1]
                            current_col += 1
                            if current_col > COLS:
                                current_col = 1
                                current_row += 1

    while ser.is_open:
        try:
            # Leer datos disponibles
            data = ser.read(ser.in_waiting or 1)
            if data:
                buffer.extend(data)
            
            # Procesar buffer
            while len(buffer) >= 2:
                if not in_packet:
                    # Buscar STX
                    if get_word(buffer[0:2]) == STX:
                        in_packet = True
                        current_packet = bytearray()
                        buffer = buffer[2:]
                    else:
                        buffer.pop(0)  # Descartar byte no válido
                else:
                    # Buscar ETX en todo el buffer
                    found_etx = False
                    for i in range(0, len(buffer)-1, 2):
                        if get_word(buffer[i:i+2]) == ETX:
                            # Agregar datos al paquete y procesar
                            current_packet.extend(buffer[:i])
                            process_packet(current_packet)
                            buffer = buffer[i+2:]
                            in_packet = False
                            found_etx = True
                            break
                    
                    if not found_etx:
                        # Agregar todos los datos al paquete actual
                        current_packet.extend(buffer)
                        buffer.clear()
                    break
                        
        except Exception as e:
            print(f"Error en receptor avanzado: {e}")
            buffer.clear()
            in_packet = False

# Callback para clics del mouse
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        col, row = x // CHAR_WIDTH, y // CHAR_HEIGHT
        if 0 <= col < COLS and 0 <= row < ROWS:
            with vram_lock:
                value = vram[row, col]
            char_code, borders, color = decode_char(value)
            
            print(f"\nCelda: Fila {row+1}, Columna {col+1}")
            print(f"Carácter: {char_code} ('{chr(char_code) if 32 <= char_code < 127 else ' '}')")
            #print(f"Bordes: Superior={bool(borders & 0b4)}, Izquierdo={bool(borders & 0b2)}, Inferior={bool(borders & 0b1)}")
            print(f"Color: {['Negro', 'Gris', 'Blanco', 'Negro'][color]}")

# Iniciar hilo serial
serial_thread = threading.Thread(target=serial_receiver, daemon=True)
serial_thread.start()

# Configurar ventana y callback de mouse
cv2.namedWindow('Video con Texto', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Video con Texto', SCREEN_WIDTH, SCREEN_HEIGHT)
cv2.setMouseCallback('Video con Texto', mouse_callback)

# Inicializar cámara
cap = cv2.VideoCapture(0)
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
    cv2.imshow('Video con Texto', frame)
    
    # Salir con ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Limpieza
cap.release()
cv2.destroyAllWindows()
