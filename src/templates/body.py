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


import streamlit as st
import html

from src.braillebook import (
    pdf_to_image, 
    create_braille_pdf, 
    get_pdf_page_count,
    braille_alphabet,
    braille_numbers,
    braille_punctuation,
    braille_multicell
)

def get_char_cell_count(char):
    """Calcula cuántas celdas Braille físicas ocupa un carácter."""
    cells = 0
    if char.isupper():
        cells += 1
        if char.lower() in braille_alphabet:
            cells += 1
    elif char.isdigit():
        cells += 1
        if char in braille_numbers:
            cells += 1
    elif char in braille_multicell:
        # Suma la cantidad de celdas que requiere el símbolo especial (ej. 2 para el slash)
        cells += len(braille_multicell[char])
    elif char in braille_punctuation:
        cells += 1
    elif char.lower() in braille_alphabet:
        cells += 1
    return cells

def config_page():
    st.set_page_config(
        page_title="BrailleBook | Scriptorium",
        page_icon="𒁾",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
        <style>
        /* Ocultar elementos predeterminados que restan autoridad al diseño */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Ajustar espaciados del contenedor principal */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        /* Personalización estilizada de la caja de edición */
        .stTextArea textarea {
            font-family: 'Courier New', Courier, monospace;
            font-size: 15px;
            border-radius: 6px;
            border: 1px solid rgba(49, 51, 63, 0.2);
            box-shadow: none;
        }

        /* Forzar que las pestañas tengan un diseño limpio */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        </style>
        """, unsafe_allow_html=True)

def prev_page():
    if st.session_state.preview_page > 1:
        st.session_state.preview_page -= 1

def next_page(total_pages):
    if st.session_state.preview_page < total_pages:
        st.session_state.preview_page += 1

def load_file_content():
    if st.session_state.uploaded_file is not None:
        st.session_state.input_text = st.session_state.uploaded_file.read().decode("utf-8")

def apply_alignment(mode):
    text = st.session_state.input_text
    lines = text.split('\n')

    # Extraemos el número de línea seleccionada (restando 1 porque las listas inician en 0)
    target_idx = st.session_state.get("target_line", 1) - 1
    
    if 0 <= target_idx < len(lines):
        line = lines[target_idx]
        stripped_line = line.strip()
        
        if stripped_line: # Solo procedemos si la línea no está completamente vacía
            b_len = 0
            for char in stripped_line:
                cells = get_char_cell_count(char)
                b_len += cells

            # Solo aplicamos espacios si la longitud es menor al límite de 30 celdas
            if b_len < 30:
                spaces_needed = 30 - b_len
                if mode == "center":
                    pad_left = spaces_needed // 2
                    lines[target_idx] = (" " * pad_left) + stripped_line
                elif mode == "right":
                    lines[target_idx] = (" " * spaces_needed) + stripped_line
                else: # left
                    lines[target_idx] = stripped_line

    # Reconstruimos el texto y forzamos la actualización visual
    st.session_state.input_text = '\n'.join(lines)
    st.session_state.preview_page = 1

def body():
    # Inicialización del estado de la sesión
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    if "preview_page" not in st.session_state:
        st.session_state.preview_page = 1

    # Barra lateral izquierdo
    with st.sidebar:
        st.markdown("<h2 style='letter-spacing: 1px;'>⚙️ Archivo Fuente</h2>", unsafe_allow_html=True)

        st.file_uploader(
            "Selecciona un manuscrito fuente:", 
            type=["txt"], 
            key="uploaded_file",
            on_change=load_file_content,
            label_visibility="collapsed"
        )

        st.info("💡 **Guía rápida:** Sube un archivo con extensión `.txt` o redacta directamente sobre el lienzo del Scriptorium.")


    col_editor, col_preview = st.columns([1.2, 1], gap="large")
    with col_editor:
        st.markdown("<h2 style='letter-spacing: 1px;'>Scriptorium</h2>", unsafe_allow_html=True)

        # Calculamos cuántas líneas existen actualmente para el selector
        current_lines_count = max(1, len(st.session_state.input_text.split('\n')))

        # --- ACTUALIZACIÓN: Barra de herramientas con Selector de Línea ---
        st.markdown("<span style='font-size: 14px; color: #555; font-weight: 600;'>Herramientas de Párrafo</span>", unsafe_allow_html=True)
        col_line, col_btn_l, col_btn_c, col_btn_r = st.columns([1.5, 1, 1, 1])

        with col_line:
            st.number_input(
                "Línea N°", 
                min_value=1, 
                max_value=current_lines_count, 
                value=1, 
                key="target_line", 
                help="Indica el número del renglón que deseas alinear."
            )
        with col_btn_l:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("⫷ Izq.", width='stretch', on_click=apply_alignment, args=("left",))
        with col_btn_c:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("≡ Cen.", width='stretch', on_click=apply_alignment, args=("center",))
        with col_btn_r:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("⫸ Der.", width='stretch', on_click=apply_alignment, args=("right",))

        current_input = st.text_area(
            "Texto original a transcribir:", 
            height=400,
            key="input_text",
            label_visibility="collapsed",
            placeholder="Escribe o edita el texto aquí para acuñar la matriz Braille..."
        )

        # --- Vigilancia de Desbordamiento en Tiempo Real ---
        if current_input:
            lines = current_input.split('\n')
            overflow_html = ""

            for i, line in enumerate(lines):
                braille_len = 0
                safe_chars = []
                danger_chars = []

                for char in line:
                    cells = get_char_cell_count(char)

                    if braille_len + cells <= 30:
                        safe_chars.append(char)
                    else:
                        danger_chars.append(char)

                    braille_len += cells

                if braille_len > 30:
                    safe_text = html.escape("".join(safe_chars))
                    danger_text = html.escape("".join(danger_chars))

                    overflow_html += f"<div style='font-family: monospace; font-size: 13px; margin-top: 4px;'>"
                    overflow_html += f"<span style='color: #888;'>Lín {i+1}: </span>"
                    overflow_html += f"<span style='color: #aaa;'>...{safe_text[-10:] if len(safe_text) > 10 else safe_text}</span>"
                    overflow_html += f"<mark style='background-color: #ff4b4b; color: white; padding: 0 3px; border-radius: 2px; font-weight: bold;'>{danger_text}</mark>"
                    overflow_html += f"</div>"

            if overflow_html:
                st.markdown("<div style='border-left: 3px solid #ff4b4b; padding-left: 10px; margin-top: 10px; background-color: rgba(255, 75, 75, 0.05); padding: 10px; border-radius: 0 4px 4px 0;'>", unsafe_allow_html=True)
                st.markdown("**⚠️ Exceso de 30 celdas detectado:**", unsafe_allow_html=True)
                st.markdown(overflow_html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Transcribir y Acuñar en Braille", type="primary", width='stretch'):
            st.session_state.preview_page = 1

    with col_preview:
        st.markdown("<h2 style='letter-spacing: 1px;'>Visualización</h2>", unsafe_allow_html=True)

        current_text = st.session_state.input_text

        if current_text:
            tab_pdf, tab_analisis = st.tabs(["📄 Prototipo de Folio", "📏 Auditoría de Celdas"])
            with tab_pdf:
                pdf_buffer_mirror = create_braille_pdf(current_text, mirror=True)
                pdf_buffer_normal = create_braille_pdf(current_text, mirror=False)
                total_pages = get_pdf_page_count(pdf_buffer_normal)

                if st.session_state.preview_page > total_pages:
                    st.session_state.preview_page = total_pages
                if st.session_state.preview_page < 1:
                    st.session_state.preview_page = 1

                # Renderizado de la muestra tipográfica
                pdf_buffer_normal.seek(0)
                img_bytes = pdf_to_image(pdf_buffer_normal, page_number=st.session_state.preview_page - 1)
                with st.container(border=True):
                    st.image(
                        img_bytes, 
                        caption=f"Muestra del Folio {st.session_state.preview_page} de {total_pages}", 
                        width='stretch'
                    )

                col_izq, col_centro, col_der = st.columns([1, 1.8, 1])
                with col_izq:
                    st.button("⬅️ Anterior", on_click=prev_page, disabled=(st.session_state.preview_page == 1), width='stretch')

                with col_centro:
                    st.download_button(
                        label="📥 Descargar Matriz Espejo",
                        data=pdf_buffer_mirror,
                        file_name="braille_matriz.pdf",
                        mime="application/pdf",
                        width='stretch'
                    )

                with col_der:
                    st.button("Siguiente ➡️", on_click=next_page, args=(total_pages,), disabled=(st.session_state.preview_page == total_pages), width='stretch')

                if total_pages > 1:
                    st.slider(
                        "Folio", 
                        min_value=1, 
                        max_value=total_pages, 
                        key="preview_page", 
                        label_visibility="collapsed"
                    )

            with tab_analisis:
                st.info("🔍 **Examen de Restricciones:** Las líneas que excedan el límite estricto de 30 celdas se resaltarán en rojo. El conversor truncará el excedente automático tomando en cuenta los prefijos indispensables para mayúsculas y caracteres numéricos.")

                lines = current_text.split('\n')
                overflow_count = 0

                html_code_analisis = "<div style='font-family: monospace; font-size: 14px;'>"

                for i, line in enumerate(lines):
                    braille_len = 0
                    safe_chars = []
                    danger_chars = []

                    for char in line:
                        cells = get_char_cell_count(char)

                        if braille_len + cells <= 30:
                            safe_chars.append(char)
                        else:
                            danger_chars.append(char)

                        braille_len += cells

                    if braille_len > 30:
                        overflow_count += 1
                        page_num = (i // 27) + 1
                        line_in_page = (i % 27) + 1

                        safe_text = "".join(safe_chars)
                        danger_text = "".join(danger_chars)

                        safe_html = html.escape(safe_text)
                        danger_html = html.escape(danger_text)

                        html_code_analisis += f"<div style='margin-bottom: 6px; border-bottom: 1px solid rgba(128,128,128,0.2); padding-bottom: 4px;'>"
                        html_code_analisis += f"<span style='color: #888; font-weight: bold;'>Folio {page_num} | Lín {line_in_page:02d}: </span>"
                        html_code_analisis += f"<span style='white-space: pre-wrap;'>{safe_html}</span>"
                        html_code_analisis += f"<mark style='background-color: #ff4b4b; color: white; padding: 0 2px; border-radius: 3px;'>{danger_html}</mark>"
                        html_code_analisis += f" <span style='color: #ff4b4b; font-weight: bold;'>({braille_len}/30 celdas)</span>"
                        html_code_analisis += f"</div>"

                html_code_analisis += "</div>"

                if overflow_count == 0:
                    st.success("**OK:** Ninguna línea supera el umbral de las 30 celdas. La matriz textual fluirá intacta.")
                else:
                    st.warning(f"⚠️ **Alerta de Desbordamiento:** Se detectaron **{overflow_count} línea(s)** que exceden la capacidad permitida. Modifica los cortes en el Scriptorium.")
                    with st.container(height=350):
                        st.markdown(html_code_analisis, unsafe_allow_html=True)

        else:
            st.info("A la espera de un manuscrito en el Scriptorium para labrar el texto e iniciar la previsualización...")
