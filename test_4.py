import numpy as np
import cv2
from font2 import font_7x10

COLOR_MAP = {
    0b00: (0, 0, 0),
    0b01: (128, 128, 128),
    0b10: (255, 255, 255),
    0b11: (0, 0, 0)
}

C0 = 0b000
C1 = 0b001
C2 = 0b010
C3 = 0b011
C4 = 0b100
C5 = 0b101
C6 = 0b110
C7 = 0b111

char_width = 10
char_height = 14
cols = 64
rows = 41
img_width, img_height = 631, 574

# Inicializar VRAM
vram = np.zeros((rows, cols), dtype=np.uint16)

def decode_char(value):
    char_idx = value & 0x7F
    border = (value >> 7) & 0b111
    color_bits = (value >> 10) & 0b11
    return char_idx, border, color_bits

def draw_char_block(img, col, row, char_idx, font, border=0, color_bits=0b00):
    start_x = col * char_width
    start_y = row * char_height

    char = chr(char_idx)
    glyph = font.get(char, font.get(' ', ['0000000'] * 10))
    color = COLOR_MAP.get(color_bits, (255, 255, 255))

    img[start_y:start_y+14, start_x:start_x+11] = color

    if border & 0b001:
        img[start_y, start_x:start_x+10] = (128, 128, 128)
    if border & 0b010:
        img[start_y:start_y+14, start_x] = (128, 128, 128)
    if border & 0b100:
        img[start_y+13, start_x:start_x+10] = (128, 128, 128)

    if col != 63:
        for r in range(min(10, len(glyph))):
            row_data = glyph[r]
            for c in range(min(7, len(row_data))):
                if row_data[c] == '1':
                    img[start_y + 2 + r, start_x + 2 + c] = (128, 128, 128)

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        col = x // char_width
        row = y // char_height

        if 0 <= col < cols and 0 <= row < rows:
            print(f"\nClick en: X={x}, Y={y} | Celda: Col={col}, Fila={row}")
            value = vram[row][col]
            char_idx, border, color_bits = decode_char(value)
            char = chr(char_idx)

            print(f"Carácter: {char} (ASCII: {char_idx})")
            print(f"Bordes: {bin(border)}")
            print(f"Color (BF1-BF2): {bin(color_bits)} → {COLOR_MAP[color_bits]}")
            
            if char in font_7x10:
                print("Glyph:")
                for line in font_7x10[char]:
                    print(line)

# === Cargar VRAM con contenido como antes ===
vram[0, :64] = np.arange(32, 96) | (0b11 << 10)

# Filas 1-4 (solo primeras 20 columnas)
vram[1:5, :20] = ord(' ') | (0b11 << 10)
# Fila 40 (solo primeras 20 columnas)
vram[40, :64] = ord(' ') | (0b11 << 10)

vram[2][0] = ord('A') | (C3 << 7) | (0b11 << 10)
vram[2][1] = ord('/') | (C1 << 7) | (0b11 << 10)
vram[2][2] = ord('N') | (C1 << 7) | (0b11 << 10)
vram[2][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[3][0] = ord('P') | (C6 << 7) | (0b11 << 10)
vram[3][1] = ord('A') | (C4 << 7) | (0b11 << 10)
vram[3][2] = ord('G') | (C4 << 7) | (0b11 << 10)
vram[3][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[2][4] = ord('L') | (C3 << 7) | (0b11 << 10)
vram[2][5] = ord('I') | (C1 << 7) | (0b11 << 10)
vram[2][6] = ord('N') | (C1 << 7) | (0b11 << 10)
vram[2][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[3][4] = ord('U') | (C6 << 7) | (0b11 << 10)
vram[3][5] = ord('P') | (C4 << 7) | (0b11 << 10)
vram[3][6] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[3][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[5][0] = ord(' ') | (C3 << 7) | (0b10 << 10)
vram[5][1] = ord('S') | (C1 << 7) | (0b10 << 10)
vram[5][2] = ord('U') | (C1 << 7) | (0b10 << 10)
vram[5][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[6][0] = ord('A') | (C7 << 7) | (0b11 << 10)
vram[6][1] = ord('I') | (C5 << 7) | (0b11 << 10)
vram[6][2] = ord('R') | (C5 << 7) | (0b11 << 10)
vram[6][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[5][4] = ord('H') | (C3 << 7) | (0b11 << 10)
vram[5][5] = ord('L') | (C1 << 7) | (0b11 << 10)
vram[5][6] = ord('D') | (C1 << 7) | (0b11 << 10)
vram[5][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[6][4] = ord('F') | (C6 << 7) | (0b11 << 10)
vram[6][5] = ord('R') | (C4 << 7) | (0b11 << 10)
vram[6][6] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[6][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[32][0] = ord('O') | (C3 << 7) | (0b11 << 10)
vram[32][1] = ord('P') | (C1 << 7) | (0b11 << 10)
vram[32][2] = ord('T') | (C1 << 7) | (0b11 << 10)
vram[32][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[33][0] = ord('S') | (C6 << 7) | (0b11 << 10)
vram[33][1] = ord('E') | (C4 << 7) | (0b11 << 10)
vram[33][2] = ord('T') | (C4 << 7) | (0b11 << 10)
vram[33][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[32][4] = ord('G') | (C3 << 7) | (0b11 << 10)
vram[32][5] = ord('T') | (C1 << 7) | (0b11 << 10)
vram[32][6] = ord(' ') | (C1 << 7) | (0b11 << 10)
vram[32][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[33][4] = ord('A') | (C6 << 7) | (0b11 << 10)
vram[33][5] = ord('U') | (C4 << 7) | (0b11 << 10)
vram[33][6] = ord('T') | (C4 << 7) | (0b11 << 10)
vram[33][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[35][0] = ord('R') | (C3 << 7) | (0b11 << 10)
vram[35][1] = ord('G') | (C1 << 7) | (0b11 << 10)
vram[35][2] = ord('S') | (C1 << 7) | (0b11 << 10)
vram[35][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[36][0] = ord(' ') | (C6 << 7) | (0b11 << 10)
vram[36][1] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[36][2] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[36][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[35][4] = ord('A') | (C3 << 7) | (0b11 << 10)
vram[35][5] = ord('T') | (C1 << 7) | (0b11 << 10)
vram[35][6] = ord('K') | (C1 << 7) | (0b11 << 10)
vram[35][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[36][4] = ord('J') | (C3 << 7) | (0b11 << 10)
vram[36][5] = ord('A') | (C1 << 7) | (0b11 << 10)
vram[36][6] = ord('M') | (C1 << 7) | (0b11 << 10)
vram[36][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[37][4] = ord('H') | (C3 << 7) | (0b11 << 10)
vram[37][5] = ord('A') | (C1 << 7) | (0b11 << 10)
vram[37][6] = ord('Z') | (C1 << 7) | (0b11 << 10)
vram[37][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[38][0] = ord('R') | (C3 << 7) | (0b10 << 10)
vram[38][1] = ord('D') | (C1 << 7) | (0b10 << 10)
vram[38][2] = ord('R') | (C1 << 7) | (0b10 << 10)
vram[38][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[39][0] = ord('S') | (C6 << 7) | (0b10 << 10)
vram[39][1] = ord('I') | (C4 << 7) | (0b10 << 10)
vram[39][2] = ord('L') | (C4 << 7) | (0b10 << 10)
vram[39][3] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[38][4] = ord('L') | (C3 << 7) | (0b11 << 10)
vram[38][5] = ord('D') | (C1 << 7) | (0b11 << 10)
vram[38][6] = ord(' ') | (C1 << 7) | (0b11 << 10)
vram[38][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[39][4] = ord('R') | (C7 << 7) | (0b11 << 10)
vram[39][5] = ord('A') | (C5 << 7) | (0b11 << 10)
vram[39][6] = ord('D') | (C5 << 7) | (0b11 << 10)
vram[39][7] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[38][8] = ord('R') | (C3 << 7) | (0b11 << 10)
vram[38][9] = ord('N') | (C1 << 7) | (0b11 << 10)
vram[38][10] = ord('G') | (C1 << 7) | (0b11 << 10)
vram[38][11] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[39][8] = ord('G') | (C6 << 7) | (0b11 << 10)
vram[39][9] = ord('T') | (C4 << 7) | (0b11 << 10)
vram[39][10] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[39][11] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[38][56] = ord('T') | (C3 << 7) | (0b11 << 10)
vram[38][57] = ord('O') | (C1 << 7) | (0b11 << 10)
vram[38][58] = ord(' ') | (C1 << 7) | (0b11 << 10)
vram[38][59] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[39][56] = ord(' ') | (C6 << 7) | (0b11 << 10)
vram[39][57] = ord('3') | (C4 << 7) | (0b11 << 10)
vram[39][58] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[39][59] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[38][60] = ord('S') | (C3 << 7) | (0b11 << 10)
vram[38][61] = ord('B') | (C1 << 7) | (0b11 << 10)
vram[38][62] = ord(' ') | (C1 << 7) | (0b11 << 10)
vram[38][63] = ord(' ') | (C2 << 7) | (0b11 << 10)
vram[39][60] = ord(' ') | (C6 << 7) | (0b11 << 10)
vram[39][61] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[39][62] = ord(' ') | (C4 << 7) | (0b11 << 10)
vram[39][63] = ord(' ') | (C2 << 7) | (0b11 << 10)

# === Render loop ===
#img = np.zeros((img_height, img_width, 3), dtype=np.uint8)

# Configuración de la cámara
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cv2.namedWindow('Video LCC', cv2.WINDOW_NORMAL)
#cv2.setWindowProperty('Video LCC', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_KEEPRATIO)
cv2.setMouseCallback('Video LCC', mouse_callback)

if not cap.isOpened():
    print("Error: No se pudo abrir la cámara")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("No se pudo capturar la cámara.")
        break

    # Redimensionar imagen de la cámara al tamaño del buffer
    frame_resized = cv2.resize(frame, (img_width, img_height))

    for row in range(rows):
        for col in range(cols):
            value = vram[row][col]
            # Solo dibujar si el valor en VRAM no es cero
            if value != 0:
                char_idx, border, color_bits = decode_char(value)
                draw_char_block(frame_resized, col, row, char_idx, font_7x10, border, color_bits)

    # Mostrar
    cv2.imshow("Video LCC", frame_resized)

    # Salida con ESC
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
