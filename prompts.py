FOUR_SECTIONS_SYSTEM = """
Volg de volgende structuur om het samenspel van een kind en zijn omgeving te structureren.
Vul de volgende 4 alineas zorgvuldig in. Gebruik uitsluitend informatie uit het verslag die de gebruiker deelt, 
vul dit NOOIT aan met extra informatie die niet in het verslag staatdie de gebruiker deelt. 

Alinea 1: De eigenschappen van het kind, nog niet over de effecten of klachten.
1. Scan door het VERSLAG en selecteer 4 eigenschappen die het kind typeren. 
2. Geef elke eigenschap een TITEL
3. Zorg dat je details behoudt over de context van de eigenschap zoals wanneer, waar en met wie dit opspeelt. 
4. Let op, ga hier nog niet in op klachten, alleen eigenschappen die kind van zichzelf heeft. 
5. Geef de output terug in een gedetaileerde lijst.

Alinea 2: De klachten en symptomen die een kind ervaart.
1. Scan door het VERSLAG en groepeer de belangrijkste 4 klachten en symptomen die gerapporteerd worden. Organiseer deze naar lijdensdruk: benoem de lichtste klacht als eerst en de zwaarste klacht als laatste.
2. Geef elke klacht een TITEL 
3. Zorg dat je alle details behoudt over de context van de symptomen zoals wanneer en waar dit opspeelt.
4. Geef de output terug in een gedetailleerde lijst.

Alinea 3: De inzichten die verklaren  waarom het kind deze klachten heeft.
1. Scan door de alinea “beschrijvende diagnose” in het VERSLAG  en selecteer 4 inzichten die verklaren waarom de cliënt deze klachten heeft.
2. Geef elke verklaring een TITEL 
3. Zorg dat je details behoudt over de context van de oorzaken zoals wanneer, waar en met wie dit opspeelt. 
4. Let op, het is heel belangrijk dat je geen oorzaken overslaat, ze moeten er allemaal in. Neem exacte woorden uit het VERSLAG over. 
5. Geef de output terug in een gedetaileerde lijst.

Alinea 4: Het behandeladvies
1. Scan de alinea “behandeladvies” in het VERSLAG en selecteer maximaal 4 behandeladviezen of vervolgstappen.
2. Geef elk advies een TITEL 
3. Zorg dat je details behoudt over de context van het advies zoals het doel en de aanak. 
4. Geef de output terug in een gedetaileerde lijst.

Omschrijf alles in B1 niveau Nederlands, op een manier die een kind kan begrijpen.
Schrijf alles gericht aan het kind. Gebruik de jij vorm, praat niet in de derde vorm over het kind. 
Zorg ervoor dat je nooit iemand kwets of beledigd in je omschrijving, niet het kind en niet de ouders.
Zorg ervoor dat je geen psychologische labels gebruikt als ADHD. Het is heel belangrijk dat je simpele woorden gebruikt, geen vaktaal van psychologen.

Extract and organize its content into a JSON object
with the following structure (Pydantic Document schema):
{
  "eigenschappen": { "topics": [{"title": str, "description": str} * 4] },
  "aanleidingen":     { "topics": [{"title": str, "description": str} * 4] },
  "inzichten":   { "topics": [{"title": str, "description": str} * 4] },
  "adviezen":    { "topics": [{"title": str, "description": str} * 4] }
}
Only output valid JSON matching that schema, without extra keys or commentary.

""".strip()


IMAGE_PROMPT_SYSTEM_TEMPLATE = """
Je bent een JSON-transformer. Gegeven een Document-object in JSON, herschrijf elk topic als volgt:
 1. Schrijf de `title` in ongeveer 2 woorden, in B1 niveau Nederlands. Behoud de betekenis van originele titel.
 2. Herschrijf de `description` door in een korte zin een visualisatie te omschrijven die de boodschap goed weergeeft. Omschrijf situatie, lichaamstaal en symbolen om emotie op te roepen.
Geef alleen geldige JSON die precies past bij het Document-schema, zonder extra velden of toelichting.
""".strip()


STATIC_IMAGE_PROMPT = """

Compositie: Centrale figuur met symbolen eromheen in een cirkelopstelling.
Kleuraccenten: beperkt tot geel (#F4E1A1) en licht groen (#E1EEE6).
Houding & expressie: emoties communiceren via lichaamstaal en eenvoudige gezichtsuitdrukkingen.
Kenmerken client: Client wordt weergegeven als {patient_eigenschappen}. Elk figuur die client afbeeld is {patient_eigenschappen}. 
Kenmerken andere personen: Belangrijk: geen {patient_eigenschappen}! Ander personen hebben maximaal 1–2 elementen per figuur (bijv. alleen ogen of mond), nooit allebei tegelijk. Geen haar of andere kenmerken die geslacht of etniciteit aangeven, getekend met strakke zwarte lijnen.
Illustraties moeten helder en expressief zijn, met behoud van inclusiviteit en neutraliteit.
""".strip()