import numpy as np
import cv2
from font2 import font_7x10  # font_7x10 debe ser un dict con claves tipo 'A', 'B', etc.

# Configuración de la cámara
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    print("Error: No se pudo abrir la cámara")
    exit()
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cv2.namedWindow('Video LCC', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Video LCC', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_KEEPRATIO)
cv2.setWindowProperty("Video LCC", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Configuración de visualización
char_width = 10
char_height = 14
cols = 63
rows = 4
img_width, img_height = 640, 576

# Datos de prueba con caracteres y bordes
char_data = [
    *[(col, 0, idx + 32) for col, idx in enumerate(range(63 + 32))],
    #*[(col, 1, idx + 63) for col, idx in enumerate(range(63))],

    #C, F    
    (0, 2, (ord('A') | (0b011 << 7))),         
    (1, 2, (ord('/') | (0b001 << 7))),   
    (2, 2, (ord('N') | (0b001 << 7))),   
    (3, 2, (ord(' ') | (0b010 << 7))),   
    
    (0, 3, (ord('P') | (0b110 << 7))),   
    (1, 3, (ord('A') | (0b100 << 7))),   
    (2, 3, (ord('G') | (0b100 << 7))),   
    (3, 3, (ord(' ') | (0b010 << 7))),

    (0, 5, (ord('L') | (0b011 << 7))),         
    (1, 5, (ord('I') | (0b001 << 7))),   
    (2, 5, (ord('N') | (0b001 << 7))),   
    (3, 5, (ord(' ') | (0b010 << 7))),   
    
    (0, 6, (ord('U') | (0b110 << 7))),   
    (1, 6, (ord('P') | (0b100 << 7))),   
    (2, 6, (ord(' ') | (0b100 << 7))),   
    (3, 6, (ord(' ') | (0b010 << 7))),      

    (0, 38, (ord('R') | (0b011 << 7))),         
    (1, 38, (ord('N') | (0b001 << 7))),   
    (2, 38, (ord('G') | (0b001 << 7))),   
    (3, 38, (ord(' ') | (0b010 << 7))),   
    
    (0, 39, (ord('M') | (0b110 << 7))),   
    (1, 39, (ord('A') | (0b100 << 7))),   
    (2, 39, (ord('N') | (0b100 << 7))),   
    (3, 39, (ord(' ') | (0b010 << 7))), 

    (30, 10, (ord('0') | (0b000 << 7))),
    (30, 12, (ord('1') | (0b001 << 7))),
    (30, 14, (ord('2') | (0b010 << 7))),
    (30, 16, (ord('3') | (0b011 << 7))),
    (30, 18, (ord('4') | (0b100 << 7))),
    (30, 20, (ord('5') | (0b101 << 7))),
    (30, 22, (ord('6') | (0b110 << 7))),
    (30, 24, (ord('7') | (0b111 << 7))),
]

def decode_char(value):
    char_idx = value & 0x7F
    border = (value >> 7) & 0b111
    return char_idx, border

def draw_char_block(img, col, row, char_idx, font, border=0):
    start_x = col * char_width
    start_y = row * char_height

    char = chr(char_idx)
    glyph = font.get(char, font.get(' ', ['0000000'] * 10))

    # Dibujar carácter
    for r in range(min(10, len(glyph))):
        row_data = glyph[r]
        for c in range(min(7, len(row_data))):
            if row_data[c] == '1':
                img[start_y + 2 + r, start_x + 2 + c] = (0, 0, 0)  # negro

    # Bordes
    if border & 0b001:
        img[start_y, start_x:start_x+10] = (0, 0, 0)
    if border & 0b010:
        img[start_y:start_y+14, start_x] = (0, 0, 0)
    if border & 0b100:
        img[start_y+13, start_x:start_x+10] = (0, 0, 0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.resize(frame, (img_width, img_height))

    for col, row, val in char_data:
        char_idx, border = decode_char(val)
        draw_char_block(frame, col, row, char_idx, font_7x10, border)

    cv2.imshow("Video LCC", frame)
    
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
