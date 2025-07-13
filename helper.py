import streamlit as st
from PyPDF2 import PdfReader
import openai, base64
from pydantic import BaseModel
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
import textwrap
from prompts import (
    FOUR_SECTIONS_SYSTEM,
    IMAGE_PROMPT_SYSTEM_TEMPLATE,
    STATIC_IMAGE_PROMPT,
)

client = openai.OpenAI()

class Alineas(BaseModel):
    alinea_1: str
    alinea_2: str
    alinea_3: str
    alinea_4: str


@st.cache_data(show_spinner=False)
def read_pdf(file):
    reader = PdfReader(file)
    all_text = []

    for page in reader.pages:
        txt = page.extract_text() or ""
        all_text.append(txt)

    return "\n\n".join(all_text)


@st.cache_data(show_spinner=False)
def rewrite_to_four_sections(
    report: str,
    model: str = "gpt-4o",
) -> Alineas:
    """
    Transforms a dry psychological report into four sections: 
    1. the childs characteristics
    2. the childs symptoms 
    3. explanation why the child experiences those symptoms
    4. treatment advice

    Parameters:
    - report: The original text from the doctor's report.
    - model: OpenAI model to use (default "gpt-4o").

    Returns:
    - An Alineas object with four separate alineas
    """
    
    system_prompt = FOUR_SECTIONS_SYSTEM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"VERSLAG:\n{report}"}
    ]
    response = client.responses.parse(
        model=model,
        input=messages,
        text_format = Alineas,
    )

    return response.output_parsed


@st.cache_data(show_spinner=False)
def rewrite_to_image_prompt(
    report: str,
    topic: str,
    patient_eigenschappen: str,
    model: str = "gpt-4o",
) -> str:
    """
    Transforms a psychological report description into a detailed image-generation prompt.

    Parameters:
    - report: The summary text from the doctor's report.
    - topics: Topic of the image (Eigenschappen, Klachten, Klacht verklaringen, Behandeladviezen) 
    - model: OpenAI model to use (default "gpt-4o").

    Returns:
    - A single string ready to pass to an image-generation API.
    """
    system_prompt = IMAGE_PROMPT_SYSTEM_TEMPLATE.format(topic=topic, 
                                                        topic_short=topic[:-2], 
                                                        patient_eigenschappen=patient_eigenschappen)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Dry description:\n{report}"}
    ]

    response = client.responses.create(
        model=model,
        input=messages,
    )

    return response.output_text


@st.cache_data(show_spinner=False)
def generate_image(prompt):

    # TODO: collect all prompts in one file
    static_prompt = STATIC_IMAGE_PROMPT

    final_prompt = static_prompt + prompt
    result = client.images.edit(
    model="gpt-image-1",
    image=[
        open("imgs/example_1.png", "rb"),
        open("imgs/example_2.png", "rb"),
        open("imgs/example_3.png", "rb"),
    ],
    prompt=final_prompt,
    size="1536x1024"
    )
    
    image_base64 = result.data[0].b64_json
    return base64.b64decode(image_base64)

# def create_clickable_image_selector():
#     """Create a clickable image selector for style selection"""
    
#     # Initialize selected style in session state if not exists
#     if 'selected_style' not in st.session_state:
#         st.session_state.selected_style = 'stijl1'
    
#     # Add custom CSS for styling
#     st.markdown("""
#     <style>
#     /* Container for the image grid */
#     .image-selector-container {
#         display: flex;
#         gap: 20px;
#         justify-content: center;
#         margin: 20px 0;
#     }
    
#     /* Individual image container */
#     .image-option {
#         flex: 1;
#         cursor: pointer;
#         border-radius: 10px;
#         overflow: hidden;
#         transition: all 0.3s ease;
#         border: 3px solid transparent;
#         position: relative;
#     }
    
#     .image-option:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 5px 15px rgba(0,0,0,0.3);
#     }
    
#     .image-option.selected {
#         border-color: #F4E1A1;
#         box-shadow: 0 5px 20px rgba(31, 119, 180, 0.4);
#     }
    
#     .image-option img {
#         width: 100%;
#         height: auto;
#         display: block;
#     }
    
#     /* Checkmark for selected image */
#     .image-option.selected::after {
#         content: '✓';
#         position: absolute;
#         top: 10px;
#         right: 10px;
#         background: #F4E1A1;
#         color: white;
#         width: 30px;
#         height: 30px;
#         border-radius: 50%;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#         font-weight: bold;
#         font-size: 18px;
#     }
#     </style>
#     """, unsafe_allow_html=True)
    
#     # Create columns for the images
#     col1, col2, col3 = st.columns(3)
    
#     # Style 1
#     with col1:
#         if st.button("Stijl 1", key="style1_btn", help="Selecteer Stijl 1", use_container_width=True):
#             st.session_state.selected_style = 'stijl1'
#             st.rerun()
        
#         # Apply selected styling
#         selected_class = "selected" if st.session_state.selected_style == 'stijl1' else ""
#         st.markdown(f'<div class="image-option {selected_class}">', unsafe_allow_html=True)
#         st.image("imgs/stijl_1.png", use_container_width=True)
#         st.markdown('</div>', unsafe_allow_html=True)
    
#     # Style 2
#     with col2:
#         if st.button("Stijl 2", key="style2_btn", help="Selecteer Stijl 2", use_container_width=True):
#             st.session_state.selected_style = 'stijl2'
#             st.rerun()
        
#         selected_class = "selected" if st.session_state.selected_style == 'stijl2' else ""
#         st.markdown(f'<div class="image-option {selected_class}">', unsafe_allow_html=True)
#         st.image("imgs/stijl_2.png", use_container_width=True)
#         st.markdown('</div>', unsafe_allow_html=True)
    
    # Style 3
    with col3:
        if st.button("Stijl 3", key="style3_btn", help="Selecteer Stijl 3", use_container_width=True):
            st.session_state.selected_style = 'stijl3'
            st.rerun()
        
        selected_class = "selected" if st.session_state.selected_style == 'stijl3' else ""
        st.markdown(f'<div class="image-option {selected_class}">', unsafe_allow_html=True)
        st.image("imgs/stijl_3.png", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

def generate_pdf_bytes(names, images):
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    for idx, key in enumerate(names):
        img = Image.open(io.BytesIO(images[idx]))
        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        img_buf.seek(0)
        reader = ImageReader(img_buf)
        iw, ih = reader.getSize()
        dw = width - 80
        dh = dw * (ih / iw)
        pdf.drawImage(reader, 40, height - dh - 40, dw, dh)
        pdf.setFont("Helvetica", 10)
        txt = st.session_state.input_text[key]
        text_obj = pdf.beginText(40, height - dh - 60)
        # Wrap text to fit page width
        max_chars = int((width - 80) / 6)
        wrapped = []
        for paragraph in txt.split("\n"):
            wrapped.extend(textwrap.wrap(paragraph, max_chars))
        for line in wrapped:
            text_obj.textLine(line)
        pdf.drawText(text_obj)
        pdf.showPage()
    pdf.save()
    return buf.getvalue()