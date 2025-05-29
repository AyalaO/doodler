import streamlit as st
from PyPDF2 import PdfReader
import openai, base64
from pydantic import BaseModel
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


@st.cache_data(show_spinner=True)
def read_pdf(file):
    reader = PdfReader(file)
    all_text = []

    for page in reader.pages:
        txt = page.extract_text() or ""
        all_text.append(txt)

    return "\n\n".join(all_text)


@st.cache_data(show_spinner=True)
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


@st.cache_data(show_spinner=True)
def rewrite_to_image_prompt(
    report: str,
    topic: str,
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
    system_prompt = IMAGE_PROMPT_SYSTEM_TEMPLATE.format(topic=topic, topic_short=topic[:-2])
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Dry description:\n{report}"}
    ]

    response = client.responses.create(
        model=model,
        input=messages,
    )

    return response.output_text


@st.cache_data(show_spinner=True)
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
    