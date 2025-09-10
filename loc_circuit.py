import cv2
import serial
import subprocess
from font import *
from vram import *

# Función para decodificar caracteres (12 bits)
def decode_char(value):
    char_code = value & 0x7F       # Bits 6-0: ASCII
    borders = (value >> 7) & 0x7   # Bits 9-7: bordes
    color = (value >> 10) & 0x3    # Bits 11-10: color
    return char_code, borders, color
 
def draw_char(img, col, row, char_code, borders, color):
    start_x, start_y = col * CHAR_WIDTH, row * CHAR_HEIGHT
    
    # Dibujar fondo
    img[start_y:start_y+CHAR_HEIGHT, start_x:start_x+CHAR_WIDTH] = COLOR_MAP[color]
    
    # Dibujar bordes, hago una AND para ver que bordes dibujo
    if borders & 0b001: img[start_y, start_x:start_x+CHAR_WIDTH] = (128, 128, 128) # arriba
    if borders & 0b010: img[start_y:start_y+CHAR_HEIGHT, start_x] = (128, 128, 128) # izquierda
    if borders & 0b100: img[start_y+CHAR_HEIGHT-1, start_x:start_x+CHAR_WIDTH] = (128, 128, 128) # abajo
    
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

    # Abrir el archivo manualmente
    #archivo = open('datos_octal.txt', 'a')
    
    try:
    
        while True:
            # Leer datos del serial
            data = ser.read(ser.in_waiting or 1)
            if data:
                buffer.extend(data)
            
            # Procesar buffer mientras tengamos al menos 2 bytes
            while len(buffer) >= 2:
                word = get_word(buffer[:2])
                buffer = buffer[2:]  # Consumir los bytes procesados
                
                # Convertir palabra a octal (4 dígitos con padding de ceros)
                #octal_word = f"{word:04o}"  # Formato octal de 4 dígitos
                #print(f"{word:08b}")   
                # Escribir en archivo
                #archivo.write(octal_word + '\n')
                #print(octal_word)
                
                if state == "WAIT_STX":
                    if word == STX:
                        packet_active = True
                        state = "IN_PACKET"
                        #print("\nSTX")
                        #print(octal_word)  # Guardar STX en octal
                
                elif state == "IN_PACKET":
                    if word == ETX:
                        packet_active = False
                        state = "WAIT_STX"
                        #print("ETX\n")
                        #print(octal_word)  # Guardar ETX en octal
                    
                    elif word == VT:
                        state = "READ_ROW"
                        #print("VT\n")
                        #print(octal_word)  # Guardar VT en octal
                    
                    elif word == HT:
                        state = "READ_COL"
                        #print("HT\n")
                        #print(octal_word)  # Guardar HT en octal
                    
                    elif packet_active:
                        # Procesar como carácter
                        char_data = word
                        with vram_lock:
                            if 1 <= current_row <= ROWS and 1 <= current_col <= COLS:
                                vram[current_row-1, current_col-1] = char_data
                                # Imprimir el valor octal en lugar del carácter
                                current_col += 1
                                if current_col > COLS:
                                    current_col = 1
                                    current_row += 1
                                    if current_row > ROWS:
                                        current_row = 1
                
                elif state == "READ_ROW":
                    if word == VT:
                        state = "READ_ROW"
                    else:
                        current_row = decode_position(word)
                    #print(current_row)
                    #print(octal_word)  # Guardar valor de fila en octal
                        state = "IN_PACKET"
                
                elif state == "READ_COL":
                    current_col = decode_position(word)
                    #print(current_col)
                    #print(octal_word)  # Guardar valor de columna en octal
                    state = "IN_PACKET"

    except KeyboardInterrupt:
        print("\nInterrupción recibida, cerrando archivo...")
    finally:
        #archivo.close()  # Cerrar el archivo
        ser.close()      # Cerrar el serial

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        col, row = x // CHAR_WIDTH, y // CHAR_HEIGHT
        
        if 0 <= col < COLS and 0 <= row < ROWS:
            with vram_lock:
                value = vram[row][col]

            char_code, borders, color = decode_char(value)
            
            # Asegurar booleanos nativos de Python
            is_loc = bool(char_code != ord(' ') and borders != 0)  # Conversión explícita
            lightpen_active = True  # Booleano directo

            print(f"\nFila {row+1}, Columna {col+1} - {'LOC' if is_loc else 'No es LOC'}")
            
            #print(f"Point: {(x%10)+1} Line: {(y%14)+1}")

            # Empaquetar con booleanos válidos
            data = pack_data(
                valid=is_loc,
                lightpen_active=lightpen_active,  # Asegurar tipo booleano
                column=col,
                points=6,
                row=row,
                lines=8
            )
            send_24bits(data)
    elif event == cv2.EVENT_LBUTTONUP:
        data = pack_data(
                valid= False,
                lightpen_active= False,  # Asegurar tipo booleano
                column=11,
                points=6,
                row=11,
                lines=8
            )
        send_24bits(data)
        

def send_24bits(data):    
    ser.write(data)
    #print(f"bytes enviados: {data.hex()}")

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

    print(f"paquete: {data:024b}")
    
    # Convertir a 3 bytes (big-endian)
    return data.to_bytes(3, byteorder='big')

def save_vram(filename):
    with vram_lock:
        np.save(filename, vram)
        print(f"VRAM guardada en {filename}")

# Configuración de comunicación serial
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 500000

# Configuración de la pantalla
#CHAR_WIDTH, CHAR_HEIGHT = int(10*1.625), int(14*1.338)
CHAR_WIDTH, CHAR_HEIGHT = 10,  14
SCREEN_WIDTH, SCREEN_HEIGHT = 631, ROWS * CHAR_HEIGHT

# Mapa de colores (BF1-BF2)
COLOR_MAP = {
    0b00: (0, 0, 0),       # Negro
    0b01: (127, 127, 127), # Gris
    0b10: (255, 255, 255), # Blanco
    0b11: (0, 0, 0)        # Negro
}

vram = vram
vram_lock = vram_lock

# Iniciar serial
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)

# Iniciar hilo serial
serial_thread = threading.Thread(target=serial_receiver, daemon=True)
serial_thread.start()

# Configurar ventana y callback de mouse
#cv2.namedWindow('Video LCC', cv2.WINDOW_NORMAL)
#cv2.resizeWindow('Video LCC', SCREEN_WIDTH, SCREEN_HEIGHT)
cv2.namedWindow("Video LCC", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Video LCC", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback('Video LCC', mouse_callback)

# Inicializar cámara
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    print("Error al abrir la cámara")
    exit()


# Bucle principal
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error de captura")
        break
    
    # Redimensionar y convertir frame
    frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
    #frame = cv2.resize(frame, (1024, 768))
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

    frame = cv2.resize(frame, (1366, 768))
    # Mostrar resultado
    cv2.imshow('Video LCC', frame)
    
    # Salir con 'q' (apaga el sistema) o ESC (solo cierra la app)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Tecla 'q' → Apagar
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=True)
        break
    elif key == 27:     # Tecla ESC → Solo salir
        break

# Limpieza
cap.release()
cv2.destroyAllWindows()
