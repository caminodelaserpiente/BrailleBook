# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Repository: https://github.com/caminodelaserpiente/BrailleBook


from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import fitz # PyMuPDF
from PIL import Image
import io

# --- Definición de Constantes Basadas en el Estándar Braille ---

# Factor de conversión de pulgadas a puntos (1 pulgada = 72 puntos)
INCHES_TO_POINTS = 72

# Dimensiones estándar del braille (en pulgadas)
DOT_DIAMETER_INCHES = 0.036  # Diámetro del punto
DOT_SPACING_INCHES = 0.09    # Espaciado entre centros de puntos (horizontal y vertical dentro de una celda)
CHARACTER_PITCH_INCHES = 0.24 # Paso horizontal de celda a celda (distancia de inicio de una celda a inicio de la siguiente)
LINE_PITCH_INCHES = 0.4      # Paso vertical de línea a línea (distancia de inicio de una línea a inicio de la siguiente)

# Dimensiones derivadas en puntos
POINT_RADIUS = (DOT_DIAMETER_INCHES / 2) * INCHES_TO_POINTS # Radio de un punto de braille
COLUMN_SEPARATION = DOT_SPACING_INCHES * INCHES_TO_POINTS  # Distancia horizontal entre centros de puntos (columnas izquierda y derecha)
ROW_SEPARATION = DOT_SPACING_INCHES * INCHES_TO_POINTS     # Distancia vertical entre centros de puntos (filas)

# Dimensiones de avance de celda (paso para el movimiento del "cursor")
CELL_ADVANCE_WIDTH = CHARACTER_PITCH_INCHES * INCHES_TO_POINTS
CELL_ADVANCE_HEIGHT = LINE_PITCH_INCHES * INCHES_TO_POINTS

# Márgenes para tamaño carta (US Letter: 8.5 x 11 pulgadas)
LEFT_MARGIN_POINTS = .8 * INCHES_TO_POINTS
TOP_MARGIN_POINTS = .29 * INCHES_TO_POINTS
RIGHT_MARGIN_POINTS = .4 * INCHES_TO_POINTS
BOTTOM_MARGIN_POINTS = 0.1 * INCHES_TO_POINTS

# Dimensiones de la página US Letter en puntos
US_LETTER_WIDTH_POINTS = 8.5 * INCHES_TO_POINTS  # 612 puntos
US_LETTER_HEIGHT_POINTS = 11 * INCHES_TO_POINTS # 792 puntos

# Calcular el número máximo de celdas por línea y líneas por página
AVAILABLE_WIDTH_FOR_TEXT = US_LETTER_WIDTH_POINTS - LEFT_MARGIN_POINTS - RIGHT_MARGIN_POINTS
MAX_CELLS_PER_LINE = int(AVAILABLE_WIDTH_FOR_TEXT / CELL_ADVANCE_WIDTH)

AVAILABLE_HEIGHT_FOR_TEXT = US_LETTER_HEIGHT_POINTS - TOP_MARGIN_POINTS - BOTTOM_MARGIN_POINTS
# Calcular MAX_LINES_PER_PAGE dinámicamente para asegurar que quepan en la página
MAX_LINES_PER_PAGE = int(AVAILABLE_HEIGHT_FOR_TEXT / CELL_ADVANCE_HEIGHT) +1

if MAX_CELLS_PER_LINE < 1:
    MAX_CELLS_PER_LINE = 1
if MAX_LINES_PER_PAGE < 1:
    MAX_LINES_PER_PAGE = 1

# Ajustes finos manuales para el interlineado de cada línea.
# Estos valores se sumarán a CELL_ADVANCE_HEIGHT para cada línea.
# Puedes modificar estos valores para ajustar el desfase.
# El índice 0 corresponde a la primera línea después del margen superior.
# El tamaño de esta lista corresponde a MAX_LINES_PER_PAGE.
# Con los márgenes actuales, caben 30 líneas. Si necesitas más, ajusta TOP_MARGIN_POINTS y BOTTOM_MARGIN_POINTS.
LINE_ADJUSTMENTS = [0.0] * MAX_LINES_PER_PAGE
LINE_ADJUSTMENTS[3] = -1
LINE_ADJUSTMENTS[4] = -1
LINE_ADJUSTMENTS[5] = -1

LINE_ADJUSTMENTS[9] = -1.5
LINE_ADJUSTMENTS[10] = -1.5
LINE_ADJUSTMENTS[11] = -1.5

LINE_ADJUSTMENTS[15] = -1
LINE_ADJUSTMENTS[16] = -.5
LINE_ADJUSTMENTS[17] = -.5

LINE_ADJUSTMENTS[18] = -1.5
LINE_ADJUSTMENTS[19] = -1.5
LINE_ADJUSTMENTS[20] = -.5


# --- Mapeo de Caracteres Braille (Grado 1) ---
braille_uppercase_marker = '010001'
braille_number_marker = '010111'

braille_alphabet = {
    'a': '100000', 'b': '101000', 'c': '110000', 'd': '110100', 'e': '100100',
    'f': '111000', 'g': '111100', 'h': '101100', 'i': '011000', 'j': '011100',
    'k': '100010', 'l': '101010', 'm': '110010', 'n': '110110', 'o': '100110',
    'p': '111010', 'q': '111110', 'r': '101110', 's': '011010', 't': '011110',
    'u': '100011', 'v': '101011', 'w': '011101', 'x': '110011', 'y': '110111',
    'z': '100111', ' ': '000000', # El espacio en braille es una celda vacía

    'á': '101111', 'é': '011011', 'í': '010010', 'ó': '010011', 'ú': '011111',
    'ñ': '111101'
}

braille_numbers = {
    '0': '011100', '1': '100000', '2': '101000', '3': '110000', '4': '110100',
    '5': '100100', '6': '111000', '7': '111100', '8': '101100', '9': '011000'
}

braille_punctuation = {
    ',': '001000', '.': '000010', ';': '001010', ':': '001100',
    '¿': '001001', '?': '001001', '¡': '001110', '!': '001110',
    '“': '001011', '”': '001011', '(': '101001', ')': '010110',
    '«': '001011', '»': '001011', '-': '000011', '*': '000110',
}

braille_multicell = {
    '/': ['000001', '001000']
}

# --- Funciones de Dibujo Braille ---

def _binary_to_braille(binary_string):
    """
    Convierte una cadena binaria de 6 bits en un formato de celda Braille.
    """
    if len(binary_string) != 6:
        raise ValueError("La cadena binaria debe tener 6 bits.")
    braille_cell = [
        binary_string[0] + binary_string[1],
        binary_string[2] + binary_string[3],
        binary_string[4] + binary_string[5]
    ]
    return braille_cell


def _draw_braille_cell(c, x, y_top_of_cell, braille_cell_data):
    """
    Dibuja una celda Braille en las coordenadas especificadas.
    x es la coordenada X de la esquina izquierda de la celda.
    y_top_of_cell es la coordenada Y de la parte superior de la celda.
    """
    # Las coordenadas Y en ReportLab aumentan hacia arriba.
    # Si y_top_of_cell es la parte superior, los puntos se dibujan "hacia abajo" desde allí.
    point_positions = [
        # Posiciones de los puntos dentro de la celda Braille (superior izquierda a inferior derecha)
        # Punto 1 (superior izquierda)
        (x + POINT_RADIUS, y_top_of_cell - POINT_RADIUS),
        # Punto 4 (superior derecha)
        (x + COLUMN_SEPARATION + POINT_RADIUS, y_top_of_cell - POINT_RADIUS),
        # Punto 2 (medio izquierda)
        (x + POINT_RADIUS, y_top_of_cell - (ROW_SEPARATION + POINT_RADIUS)),
        # Punto 5 (medio derecha)
        (x + COLUMN_SEPARATION + POINT_RADIUS, y_top_of_cell - (ROW_SEPARATION + POINT_RADIUS)),
        # Punto 3 (inferior izquierda)
        (x + POINT_RADIUS, y_top_of_cell - (2 * ROW_SEPARATION + POINT_RADIUS)),
        # Punto 6 (inferior derecha)
        (x + COLUMN_SEPARATION + POINT_RADIUS, y_top_of_cell - (2 * ROW_SEPARATION + POINT_RADIUS))
    ]

    for i, pos in enumerate(point_positions):
        # Verifica si el bit correspondiente en braille_cell_data es '1' para dibujar el punto
        # Los índices de braille_cell_data son 'fila' y 'columna' (0,0), (0,1), (1,0), (1,1), (2,0), (2,1)
        if braille_cell_data[i // 2][i % 2] == '1':
            c.circle(pos[0], pos[1], POINT_RADIUS, fill=1)


def create_braille_pdf(text, mirror=False):
    """
    Crea un documento PDF con texto convertido a Braille.
    Args:
        text (str): El texto de entrada a convertir.
        mirror (bool): Si es True, el PDF se generará en modo espejo (útil para impresión en relieve).
    Returns:
        BytesIO: Un objeto BytesIO que contiene el PDF generado.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Posición inicial X: Margen izquierdo
    x = LEFT_MARGIN_POINTS
    # Posición inicial Y: La coordenada Y de la parte superior de la primera línea de braille.
    # Esta 'y' representará la parte superior de la celda Braille actual.
    y = height - TOP_MARGIN_POINTS

    # Aplicar transformación de espejo si se solicita
    if mirror:
        c.translate(width, 0)
        c.scale(-1, 1)

    current_braille_line_count = 0 # Contador de líneas de braille generadas en la página actual
    num_cells_in_current_braille_line = 0 # Contador de celdas en la línea de braille actual


    # Función auxiliar para avanzar a la siguiente línea de braille
    def move_to_next_braille_line():
        nonlocal x, y, current_braille_line_count, num_cells_in_current_braille_line
        x = LEFT_MARGIN_POINTS # Reiniciar X al margen izquierdo

        # Incrementar el contador de línea para obtener el índice de la siguiente línea
        current_braille_line_count += 1 

        # Aplicar ajuste para la nueva línea si el índice está dentro de los límites de LINE_ADJUSTMENTS
        adjustment = 0.0
        if current_braille_line_count < len(LINE_ADJUSTMENTS):
            adjustment = LINE_ADJUSTMENTS[current_braille_line_count]

        y -= (CELL_ADVANCE_HEIGHT + adjustment) 
        num_cells_in_current_braille_line = 0 

        # Manejo de salto de página
        if current_braille_line_count >= MAX_LINES_PER_PAGE:
            c.showPage() # Iniciar nueva página

            # Volver a aplicar el espejo en la página nueva
            if mirror:
                c.translate(width, 0)
                c.scale(-1, 1)

            y = height - TOP_MARGIN_POINTS # Reiniciar Y para la nueva página
            current_braille_line_count = 0 # Reiniciar contador de líneas


    # Iterar sobre cada carácter del texto de entrada
    for char_index, char in enumerate(text):
        if char == '\n':
            move_to_next_braille_line()
            continue 

        # 1. Recolectar la secuencia completa de celdas para este carácter
        celdas_a_dibujar = []

        if char.isupper():
            char_lower = char.lower()
            if char_lower in braille_alphabet:
                celdas_a_dibujar.append(braille_uppercase_marker)
                celdas_a_dibujar.append(braille_alphabet[char_lower])
        elif char.isdigit():
            if char in braille_numbers:
                celdas_a_dibujar.append(braille_number_marker)
                celdas_a_dibujar.append(braille_numbers[char])
        elif char in braille_multicell:
            # Símbolos de 2 o más celdas (como el slash)
            celdas_a_dibujar.extend(braille_multicell[char])
        elif char in braille_punctuation:
            celdas_a_dibujar.append(braille_punctuation[char])
        elif char.lower() in braille_alphabet:
            celdas_a_dibujar.append(braille_alphabet[char.lower()])

        # 2. Vigilancia de Desbordamiento en Tiempo Real
        if len(celdas_a_dibujar) > 0:
            # Evaluar si la secuencia entera cabe en el espacio restante de la línea
            if num_cells_in_current_braille_line + len(celdas_a_dibujar) > MAX_CELLS_PER_LINE:
                move_to_next_braille_line()

            # 3. Dibujar las celdas de forma secuencial garantizando que no se separen
            for binario in celdas_a_dibujar:
                # Chequeo de seguridad por si una secuencia por sí sola supera MAX_CELLS_PER_LINE
                if num_cells_in_current_braille_line >= MAX_CELLS_PER_LINE:
                    move_to_next_braille_line()

                braille_cell_data = _binary_to_braille(binario)
                _draw_braille_cell(c, x, y, braille_cell_data)
                
                x += CELL_ADVANCE_WIDTH
                num_cells_in_current_braille_line += 1

    # Asegurar que la última línea de braille se guarde, incluso si no llenó la página
    c.save()
    buffer.seek(0)
    return buffer


def pdf_to_image(pdf_file, page_number=0):
    """
    Convierte la página especificada de un archivo PDF a una imagen PNG.
    Args:
        pdf_file (BytesIO): Objeto BytesIO que contiene los datos del PDF.
        page_number (int): El número de página a convertir (0-indexado).
    Returns:
        BytesIO: Un objeto BytesIO que contiene la imagen PNG.
    """
    # Asegúrate de que el buffer esté al inicio antes de leerlo
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    page = doc.load_page(page_number)
    pix = page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    doc.close() # Es buena práctica cerrar el documento
    return img_bytes

def get_pdf_page_count(pdf_file):
    """Devuelve el número total de páginas de un PDF en memoria."""
    pdf_file.seek(0)
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    count = doc.page_count
    doc.close()
    pdf_file.seek(0)
    return count
