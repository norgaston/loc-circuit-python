import cv2
import numpy as np
from font import *

# Dimensiones de la imagen
img_width, img_height = 631, 576
rect_width, rect_height = 31, 29
spacing_x, spacing_y = 9, 13

# Fuente: función para dibujar caracteres 7x10
def draw_character(image, char, x, y):
    if char not in font_7x10:
        return
    for row_index, row in enumerate(font_7x10[char]):
        for col_index, pixel in enumerate(row):
            if pixel == '1' and 0 <= x + col_index < img_width and 0 <= y + row_index < img_height:
                image[y + row_index, x + col_index] = 0  # negro

# Crear imagen de LOCs con fondo blanco
overlay = np.ones((img_height, img_width), dtype=np.uint8) * 255

# LOCs activos
actives_locs = [0, 1, 14, 15, 16, 17, 18, 30, 31, 32, 46, 47, 62, 63, 109, 110, 111, 112, 113,
                125, 126, 127, 128, 129, 141, 142, 143, 144, 145, 157, 158, 159, 160, 161, 162,
                173, 174, 175, 176, 177, 178, 189, 190, 191, 192, 193, 194, 197, 198, 200, 201,
                203, 205, 206, 207]

locs_posibles =  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
                   29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
                   56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82,
                   83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107,
                   108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129,
                   130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151,
                   152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173,
                   174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195,
                   196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207]


# Posiciones de cada LOC activo para detección de clics
loc_positions = {}

# Dibujar rectángulos y números
current_x, current_y = 0, 27
for i in range(208):
    if i in locs_posibles:
        end_x = current_x + rect_width - 1
        end_y = current_y + rect_height - 1
        cv2.rectangle(overlay, (current_x, current_y), (end_x, end_y), 0, 1)
        text = str(i + 1)
        text_x = current_x + 1
        text_y = current_y + 1
        #for char_index, char in enumerate(text):
        #    draw_character(overlay, char, text_x + char_index * 8, text_y)
        loc_positions[i + 1] = (current_x, current_y, end_x, end_y)

    current_x += rect_width + spacing_x
    if current_x + rect_width > img_width:
        current_x = 0
        current_y += rect_height + spacing_y
    if current_y + rect_height > img_height:
        break
"""
# Dibujar caracteres
num_chars_per_row = 63
num_rows = 41
char_width, char_height = 7, 10
horizontal_padding = 3
vertical_padding = 3
center_x = (img_width - (num_chars_per_row * (char_width + horizontal_padding))) // 2
center_y_start = (img_height - (num_rows * (char_height + vertical_padding))) // 2
center_y_start = 30

for row in range(num_rows):
    current_x = center_x
    current_x = 2
    for col in range(num_chars_per_row):
        char_index = col + row * num_chars_per_row
        if char_index < len(caracteres_font_7x10):
            char = caracteres_font_7x10[char_index]
            draw_character(overlay, char, current_x, center_y_start + row * (char_height + vertical_padding))
        current_x += char_width + horizontal_padding
"""
# Dibujar caracteres en toda la pantalla
num_chars_per_row = 63
num_rows = 41
char_width, char_height = 7, 10
horizontal_padding = 3
vertical_padding = 4

# Iniciar desde la parte superior izquierda
start_x = 2
start_y = 2

for row in range(num_rows):
    current_y = start_y + row * (char_height + vertical_padding)
    for col in range(num_chars_per_row):
        current_x = start_x + col * (char_width + horizontal_padding)
        char_index = (col + row * num_chars_per_row) % len(caracteres_font_7x10)  # Repetir si se pasa
        char = caracteres_font_7x10[char_index]
        draw_character(overlay, char, current_x, current_y)


# Función para manejar clics del mouse
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        for loc_num, (x1, y1, x2, y2) in loc_positions.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                print(f"LOC {loc_num}")
                break

# Captura de cámara
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cv2.namedWindow('Video LCC', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Video LCC', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_KEEPRATIO)
cv2.setWindowProperty("Video LCC", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Registrar callback de mouse
cv2.setMouseCallback('Video LCC', mouse_callback)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_resized = cv2.resize(frame, (img_width, img_height))
    overlay_color = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)

    mask = overlay_color < 250
    mask_single = np.any(mask, axis=2)

    blended = frame_resized.copy()
    blended[mask_single] = (0, 0, 0)

    cv2.imshow("Video LCC", blended)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
