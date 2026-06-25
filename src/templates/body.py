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
    braille_punctuation
)

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

        st.text_area(
            "Texto original a transcribir:", 
            height=480,
            key="input_text",
            label_visibility="collapsed",
            placeholder="Escribe o edita el texto aquí para acuñar la matriz Braille..."
        )

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

                html_code = "<div style='font-family: monospace; font-size: 14px;'>"

                for i, line in enumerate(lines):
                    braille_len = 0
                    safe_chars = []
                    danger_chars = []

                    for char in line:
                        cells = 0
                        if char.isupper():
                            cells += 1
                            if char.lower() in braille_alphabet:
                                cells += 1
                        elif char.isdigit():
                            cells += 1
                            if char in braille_numbers:
                                cells += 1
                        elif char in braille_punctuation:
                            cells += 1
                        elif char.lower() in braille_alphabet:
                            cells += 1

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

                        html_code += f"<div style='margin-bottom: 6px; border-bottom: 1px solid rgba(128,128,128,0.2); padding-bottom: 4px;'>"
                        html_code += f"<span style='color: #888; font-weight: bold;'>Folio {page_num} | Lín {line_in_page:02d}: </span>"
                        html_code += f"<span>{safe_html}</span>"
                        html_code += f"<mark style='background-color: #ff4b4b; color: white; padding: 0 2px; border-radius: 3px;'>{danger_html}</mark>"
                        html_code += f" <span style='color: #ff4b4b; font-weight: bold;'>({braille_len}/30 celdas)</span>"
                        html_code += f"</div>"

                html_code += "</div>"

                if overflow_count == 0:
                    st.success("**OK:** Ninguna línea supera el umbral de las 30 celdas. La matriz textual fluirá intacta.")
                else:
                    st.warning(f"⚠️ **Alerta de Desbordamiento:** Se detectaron **{overflow_count} línea(s)** que exceden la capacidad permitida. Modifica los cortes en el Scriptorium.")
                    with st.container(height=350):
                        st.markdown(html_code, unsafe_allow_html=True)

        else:
            st.info("A la espera de un manuscrito en el Scriptorium para labrar el texto e iniciar la previsualización...")
