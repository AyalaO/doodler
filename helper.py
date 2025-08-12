import streamlit as st
from PyPDF2 import PdfReader
import base64
from pydantic import BaseModel, Field
from typing import List, Dict, Tuple
import io
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Resampling
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from prompts import (
    FOUR_SECTIONS_SYSTEM,
    IMAGE_PROMPT_SYSTEM_TEMPLATE,
    STATIC_IMAGE_PROMPT,
)

client = OpenAI()

@st.cache_data(show_spinner=False)
def read_pdf(file):
    reader = PdfReader(file)
    all_text = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        all_text.append(txt)
    return "\n\n".join(all_text)

class Topic(BaseModel):
    title: str
    description: str

class Alinea(BaseModel):
    topics: List[Topic] = Field(..., min_length=4, max_length=4)

class Document(BaseModel):
    eigenschappen: Alinea
    aanleidingen: Alinea
    inzichten: Alinea
    adviezen: Alinea

@st.cache_data(show_spinner=False)
def rewrite_to_four_sections(report: str, model: str = "gpt-4o") -> Document:
    messages = [
        {"role": "system", "content": FOUR_SECTIONS_SYSTEM},
        {"role": "user",   "content": f"VERSLAG:\n{report}"}
    ]
    response = client.responses.parse(
        model=model,
        input=messages,
        text_format=Document
    )
    return response.output_parsed

@st.cache_data(show_spinner=False)
def rewrite_to_image_prompt(
    doc_json: str,
    model: str = "gpt-4o"
) -> Document:
    messages = [
        {"role": "system", "content": IMAGE_PROMPT_SYSTEM_TEMPLATE},
        {"role": "user",   "content": f"INPUT_DOCUMENT:\n{doc_json}"}
    ]
    response = client.responses.parse(
        model=model,
        input=messages,
        text_format=Document
    )
    return response.output_parsed

@st.cache_data(show_spinner=False)
def generate_image(prompt: str) -> bytes:
    # NB: zorg dat dit pad bestaat
    result = client.images.edit(
        model="gpt-image-1",
        image=[open("imgs/example_4.png", "rb")],
        prompt=prompt,
        size="1536x1024"
    )
    image_bytes = base64.b64decode(result.data[0].b64_json)
    return image_bytes

def overlay_labels(
    image_bytes: bytes,
    annotations: List[Dict[str, float]],
    font_path: str = "./fonts/Avenir Regular.ttf",
    font_size: int = 24
) -> bytes:
    img = Image.open(BytesIO(image_bytes)).convert("RGBA")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        raise FileNotFoundError(f"Kan het font niet laden van {font_path}. Plaats je .ttf in de fonts/ map?")

    pad = 4
    for ann in annotations:
        label = ann['label']
        x = int(ann['x_pct'] * img.width)
        y = int(ann['y_pct'] * img.height)
        bbox = draw.textbbox((x, y), label, font=font)
        rect = [(bbox[0] - pad, bbox[1] - pad),(bbox[2] + pad, bbox[3] + pad)]
        draw.rectangle(rect, fill="white")
        draw.text((x, y), label, font=font, fill="black")

    output = BytesIO()
    img.convert("RGB").save(output, format="PNG")
    return output.getvalue()

def add_logo_with_frame(
    image_bytes: bytes,
    logo_path: str,
    title: str,
    output_path: str,
    font_path: str = "./fonts/Avenir Regular.ttf",
    font_size: int = 24,
    padding: int = 20,
    bg_color: Tuple[int, int, int] = (225, 238, 230),
    logo_ratio: float = 1.0,
    frame_width: int = 20
) -> bytes:
    base = Image.open(BytesIO(image_bytes)).convert("RGBA")
    if base.size != (1536, 1024):
        raise ValueError(f"Expected base size 1536×1024 but got {base.size}")

    logo = Image.open(logo_path).convert("RGBA")
    if logo_ratio != 1.0:
        logo = logo.resize(
            (int(logo.width * logo_ratio), int(logo.height * logo_ratio)),
            resample=Resampling.LANCZOS
        )

    try:
        font = ImageFont.truetype(font_path, font_size)
    except OSError:
        raise FileNotFoundError(
            f"Cannot load font from {font_path}. Please ensure the .ttf is in the fonts/ directory."
        )

    inner_w = 1536
    inner_h = 1024 + padding + logo.height + padding
    full_w = inner_w + 2 * frame_width
    full_h = inner_h + 2 * frame_width

    canvas_img = Image.new("RGBA", (full_w, full_h), (*bg_color, 255))
    canvas_img.paste(base, (frame_width, frame_width), base)

    strip_y = frame_width + 1024 + padding
    logo_x = frame_width + inner_w - logo.width - padding
    logo_y = strip_y
    canvas_img.paste(logo, (logo_x, logo_y), logo)

    draw = ImageDraw.Draw(canvas_img)
    bbox = draw.textbbox((0, 0), title, font=font)
    text_h = bbox[3] - bbox[1]
    text_x = frame_width + padding
    text_y = logo_y + (logo.height - text_h) // 2 - 10
    draw.text((text_x, text_y), title, font=font, fill="black")

    final_img = canvas_img.convert("RGB")
    final_img.save(output_path)

    buf = BytesIO()
    final_img.save(buf, format="PNG")
    return buf.getvalue()

def generate_all_images(clean_input: dict) -> Dict[str, bytes]:
    jobs = []
    for section, data in clean_input.items():
        desc = data['descriptions']
        prompt = f"""
Keep exactly the same grid and placement as the example.
Maintain identical drawing area and blank-space margins.
Match the exact style: neutral, minimal line figures with single-line arms/legs.
IMPORTANT: Heads must be simple circles with no hair—do not draw any hairlines, bangs, curls, or styles.
Use only light yellow (#F4E1A1) and light green (#E1EEE6) accents.
Do NOT add any text.

Change the content as follows:
1. middle figure has expression that matches emotions below
2. top left shows: {desc[0]}
3. top right shows: {desc[1]}
4. bottom left shows: {desc[2]}
5. bottom right shows: {desc[3]}
"""
        jobs.append((section, prompt))

    results: Dict[str, bytes] = {}
    if not jobs:
        return results

    with ThreadPoolExecutor(max_workers=min(len(jobs), 4)) as executor:
        future_to_section = {executor.submit(generate_image, prompt): section for section, prompt in jobs}
        for future in as_completed(future_to_section):
            section = future_to_section[future]
            try:
                img_bytes = future.result()
                results[section] = img_bytes
            except Exception as e:
                # log naar Streamlit in plaats van crashen
                st.warning(f"Genereren mislukt voor '{section}': {e}")

    return results

def generate_pdf_bytes(names, images):
    import io, os, re
    from xml.sax.saxutils import escape as xml_escape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from PIL import Image as PILImage

    # --- (optioneel) eigen font registreren voor PDF-tekst ---
    font_name = "Helvetica"
    font_path = "./fonts/Avenir Regular.ttf"
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("Avenir", font_path))
            font_name = "Avenir"
        except Exception:
            pass  # val terug op Helvetica

    # --- Markdown -> ReportLab inline markup ---
    def md_to_rl(text: str) -> str:
        # Escape eerst &, <, >
        s = xml_escape(text)
        # **bold** -> <b>bold</b>
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        # *italic* of _italic_ -> <i>italic</i>
        s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", s)
        s = re.sub(r"_(.+?)_", r"<i>\1</i>", s)
        # Nieuwe regels -> <br/>
        s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br/>")
        return s

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=11,
        leading=14,
    )

    story = []
    page_width, page_height = A4

    for idx, key in enumerate(names):
        # --- Afbeelding schalen op paginabreedte ---
        img_bytes = images[idx]
        pil = PILImage.open(io.BytesIO(img_bytes))
        iw, ih = pil.size
        avail_w = doc.width
        scaled_h = avail_w * (ih / iw)

        story.append(RLImage(io.BytesIO(img_bytes), width=avail_w, height=scaled_h))
        story.append(Spacer(1, 8*mm))

        # --- Markdown-tekst omzetten en plaatsen ---
        raw_md = st.session_state.input_text.get(key, "")
        para = Paragraph(md_to_rl(raw_md), body)
        story.append(para)

        # Nieuwe pagina per sectie (behalve na de laatste)
        if idx < len(names) - 1:
            story.append(PageBreak())

    doc.build(story)
    return buf.getvalue()

