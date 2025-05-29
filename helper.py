from PyPDF2 import PdfReader
import openai
import base64
from pydantic import BaseModel
import streamlit as st

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
) -> str:
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
    
    system_prompt = (
"""
Volg het volgende structuur om het samenspel van een kind en zijn omgeving te structureren.
Vul de volgende 4 alineas zorgvuldig in. Gebruik uitsluitend informatie uit het verslag die de gebruiker deelt, 
vul dit NOOIT aan met extra informatie die niet in het verslag staatdie de gebruiker deelt. 

Alinea 1: De eigenschappen van het kind, nog niet over de effecten of klachten.
1. Scan door het VERSLAG en selecteer maximaal 5 eigenschappen die het kind typeren. 
2. Zorg dat je details behoudt over de context van de eigenschap zoals wanneer, waar en met wie dit opspeelt. 
3. Let op, ga hier nog niet in op klachten, alleen eigenschappen die kind van zichzelf heeft. 
4. Geef de output terug in een gedetaileerde lijst, behoud alle details

Alinea 2: De klachten en symptomen die een kind ervaart.
1. Scan door het VERSLAG en selecteer maximaal 5 klachten en symptomen die het kind typeren. 
2. Zorg dat je alle details behoudt over de context van de sympotomen zoals wanneer en waar dit opspeelt. 
4. Geef de output terug in een gedetaileerde lijst, behoud alle details

Alinea 3: De oorzaken waarom het kind deze klachten en symptomen heeft.
1. Scan door het VERSLAG en selecteer alle stukken waar klachten en symptomen verklaard worden.
2. Zorg dat je details behoudt over de context van de oorzaken zoals wanneer, waar en met wie dit opspeelt. 
3. Let op, het is heel belangrijk dat je geen oorzaken overslaat, ze moeten er allemaal in. Neem exacte woorden uit het VERSLAG over. 
4. Geef de output terug in een gedetaileerde lijst, behoud alle details

Alinea 4: Het behandeladvies
1. Scan door het VERSLAG en selecteer maximaal 5 behandeladviezen of vervolgstappen zoals onderzoeken.
2. Leg duidelijk uit waarom dit advies in lijn is met de eigenschappen en klachten van het kind.
3. Leg duidelijk uit waarom dit het kind kan helpen.
4. Geef de output terug in een gedetaileerde lijst, behoud alle details

Omschrijf alles in makkelijk te begrijpen natuurlijk klinkend Nederlands, op een manier die een kind kan begrijpen.
Schrijf alles gericht aan het kind. Gebruik de jij vorm, praat niet in de derde vorm of het kind. 
Zorg ervoor dat je nooit iemand kwets of beledigd in je omschrijving, niet het kind en niet de ouders.
Zorg ervoor dat je geen psychologische labels gebruikt als ADHD. Het is heel belangrijk dat je simpele woorden gebruikt, geen vaktaal van psychologen.


"""
    )
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
    
    system_prompt = (
f"""
Je bent een assistent die psychologische rapporten omzet in gestructureerde prompts voor een beeldgenerator. De beelden zijn eenvoudige, duidelijke lijntekeningen voor klinische of educatieve contexten: empathisch, inclusief en genderneutraal.
Het doel van dit plaatje is om de {topic} van het kind te visualiseren. 

Stijlrichtlijnen
	•	Personen: genderneutraal, strakke zwarte lijnen, minimale gezichtskenmerken (max. 1–2 details: ogen, mond of eenvoudige haarkenmerking).
	•	Kleuren: beperkt, hoofdzakelijk geel (#F4E1A1) en licht groen (#E1EEE6) als accent.
	•	Houding & expressie: emoties via lichaamstaal en gezichtsuitdrukking, zonder geslachts- of etniciteitskenmerken.
	•	Achtergrond: minimaal of symbolisch. 
    

Gewenste output-structuur
	1	Emotie centrale figuur: Wat is de emotie van de centrale figuur in de afbeelding, hoe wordt dat gevisualiseerd
	2	{topic} (max. 5): Voor elk gekozen {topic[:-2]} geef je:
	◦	Omschrijving {topic[:-2]}: Zorg dat je details behoudt over de context van de {topic[:-2]} zoals wanneer, waar en met wie dit voorkomt.
	◦	Visualisatie: Omschrijf visualisatie die emotie oproept door passende lichaamstaal en symbolen.
	◦	Kleuren: accentkleuren geel (#F4E1A1) en licht groen (#E1EEE6).
	◦	Tekst inhoud: Korte zin in het Nederlands die alle details over {topic[:-2]} bevat.
	◦	Tekst positie: positionering in de afbeelding.


Werkwijze
	1	Scan: Neem nauwkeurig de {topic} uit het rapport over met alle details. 
	2	Emotie: bepaal wat de emotie van centrale figuur is.
	3	Output: lever de invulling zoals beschreven in de “Gewenste output-structuur”.

"""
    )
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
    static_prompt = """
Compositie: Centrale figuur met symbolen eromheen in een cirkelopstelling.
Kleuraccenten: beperkt tot geel (#F4E1A1) en licht groen (#E1EEE6).
Houding & expressie: emoties communiceren via lichaamstaal en eenvoudige gezichtsuitdrukkingen.
Gezichtsdetails: maximaal 1–2 elementen per figuur (bijv. alleen ogen of mond), nooit allebei tegelijk. Geen haar of andere kenmerken die geslacht of etniciteit aangeven, getekend met strakke zwarte lijnen.
Illustraties moeten helder en expressief zijn, met behoud van inclusiviteit en neutraliteit.
"""

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
    