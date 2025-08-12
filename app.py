
import streamlit as st
from helper import (
    read_pdf,
    rewrite_to_four_sections,
    rewrite_to_image_prompt,
    generate_all_images,
    overlay_labels,
    add_logo_with_frame,
    generate_pdf_bytes,
)
from datetime import datetime
import os

# ---------- Config ----------
st.set_page_config(
    page_title="Doodler",
    page_icon="✏️",
    initial_sidebar_state="collapsed",
    menu_items={'Get Help': 'mailto:ayala@doodler.app','About': "Welkom bij Doodler!"}
)

# Pad naar je voorbeeld PDF (pas aan naar wens)
SAMPLE_PDF_PATH = "assets/voorbeeld_verslag.pdf"

# ---------- Sidebar ----------
st.sidebar.image("imgs/logo_white.png")

# ---------- Kleine CSS tweak ----------
st.markdown(
    """
    <style>
      /* ====== Brand kleuren ====== */
      :root {
        --brand-link: #8ca38f;
        --brand-link-hover: #7d9c90;
      }

      /* ====== Basis layout ====== */
      .hero { text-align:center; padding-top:.5rem; }
      .hero img { margin-bottom:.5rem; }
      .tagline { font-size:1.05rem; color:#374151; max-width:820px; margin:0 auto .25rem auto; }
      .muted { color:#8ca38f; }
      .center { text-align:center; }

      /* ====== CTA-knop dominant, tekst zwart ====== */
      div.stButton > button {
        width:100%;
        padding:0.5rem 1.1rem;
        border-radius:9999px;
        font-weight:600;
        font-size:1.05rem;
      }
      div.stButton > button[kind="primary"],
      div.stButton > button[kind="primary"]:hover,
      div.stButton > button[kind="primary"]:focus,
      div.stButton > button[kind="primary"]:active {
        color: #000 !important;
      }

      /* ====== Link-styling (globaal) ====== */
      a, a:visited {
        color: var(--brand-link) !important;
        text-decoration: underline; /* haal desgewenst weg */
      }
      a:hover, a:focus {
        color: var(--brand-link-hover) !important;
      }
      a:focus {
        outline: 2px solid var(--brand-link-hover);
        outline-offset: 2px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Session state ----------
st.session_state.setdefault('view', 'home')           # home vs generator
st.session_state.setdefault('file_uploader_key', 0)
st.session_state.setdefault('idx', 0)
st.session_state.setdefault('processing', False)
st.session_state.setdefault('generation_completed', False)

# UI labels & vaste sectievolgorde
ui_titles = ["Eigenschappen", "Aanleidingen", "Inzichten", "Adviezen"]
sections_order = ["eigenschappen", "aanleidingen", "inzichten", "adviezen"]

# ====== HOMESCREEN ======
if st.session_state.view == 'home':
    col1, col2 = st.columns([1, 1])
    with col1:
        # Logo + korte waardepropositie
        st.markdown("<div class='hero'>", unsafe_allow_html=True)
        st.image("imgs/logo.png", width=300)
        st.subheader("Doodler maakt zorggesprekken visueel")
        st.markdown(
            "<p class='tagline'>Upload een verslag en AI creëert automatisch heldere illustraties die het gesprek ondersteunen. " \
            "Zo kan iedereen aan tafel – zorgverlener én cliënt – gemakkelijker meepraten en onthouden wat er besproken is.</p>",
            unsafe_allow_html=True,
        )
        st.divider()
        # Één duidelijke CTA
        if st.button("Bekijk demo", type="primary", use_container_width=True):
            st.session_state.view = 'generator'
            st.rerun()
    with col2:
        st.markdown("<div style='height:5rem'></div>", unsafe_allow_html=True)  # kleine spacer
        st.image("imgs/homepage.png", use_container_width=True)

    st.stop()


# ====== GENERATOR SCHERM ======
# Top navigatie
nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
with nav_col1:
    if st.button("←"):
        # reset naar homescreen
        st.session_state.view = 'home'
        st.session_state.file_uploader_key += 1
        for key in ['uploaded_file', 'last_upload_name', 'prompts', 'images', 'input_text', 'generation_completed']:
            st.session_state.pop(key, None)
        st.session_state.processing = False
        st.rerun()

# ---------- Upload + knop ----------
if not st.session_state.generation_completed:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        # Korte uitleg + inline link naar voorbeeld-PDF (geen extra knop)
        import os, base64
        def _inline_pdf_link(path: str, label: str) -> str:
            if not os.path.exists(path):
                return ""
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            # data-URL met download-attribuut; subtiele link, geen button
            return f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(path)}">{label}</a>'

        link_html = _inline_pdf_link(SAMPLE_PDF_PATH, "download dit voorbeeldverslag")
        st.subheader("Visualiseer je verslag")
        st.markdown("<p class='muted'><em>momenteel alleen beschikbaar voor adviesgesprekken</em></p>", unsafe_allow_html=True)
        st.markdown(f"""
                    1. **Upload** een geanonimiseerd adviesgesprek verslag  
                    *geen verslag bij de hand? {link_html}*
                    2. **Genereer illustraties** met Doodler AI
                    3. **Pas de tekst aan** indien gewenst
                    3. **Gebruik** de illustraties tijdens het gesprek
                    """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "", type=['pdf'], key=f"file_uploader_{st.session_state.file_uploader_key}"
        )
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)  # kleine spacer
        generate_clicked = st.button("Genereer Doodle", type="primary")
        if generate_clicked and 'uploaded_file' not in st.session_state:
            st.error("⚠️ Upload eerst een PDF bestand voordat je doodles kunt genereren.")
else:
    uploaded_file = st.session_state.get('uploaded_file')
    generate_clicked = False

# ---------- Startconditie ----------
generate_condition = (
    ('uploaded_file' in st.session_state)
    and not st.session_state.processing
    and (
        (generate_clicked)
        or (
            st.session_state.generation_completed
            and st.session_state.get('last_upload_name') != st.session_state.uploaded_file.name
        )
    )
)

if generate_condition:
    st.session_state.processing = True
    st.session_state.generation_completed = False
    st.rerun()

# ---------- Pipeline ----------
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    if st.session_state.processing and 'uploaded_file' in st.session_state:
        uploaded_file = st.session_state.uploaded_file

        # 1) PDF lezen
        with st.spinner("Adviesrapport wordt gelezen.."):
            report = read_pdf(uploaded_file)

        # 2) Naar 4 secties (Document)
        with st.spinner("Verhaallijn wordt gemaakt.."):
            sections_doc = rewrite_to_four_sections(report)

        # 3) Prompts (korte titels + visuele beschrijvingen)
        with st.spinner("Doodlers worden ontworpen.."):
            visuals = rewrite_to_image_prompt(sections_doc.model_dump_json())

            # clean_input voor image generatie
            clean_input = {}
            visuals_dict = visuals.model_dump()
            for section in sections_order:
                content = visuals_dict[section]
                section_titles = [topic['title'] for topic in content['topics']]
                descriptions = [topic['description'] for topic in content['topics']]
                clean_input[section] = {'titels': section_titles, 'descriptions': descriptions}

            # Tekst voor expanders/PDF
            section_texts = {}
            orig = sections_doc.model_dump()
            for section in sections_order:
                lines = []
                for t in orig[section]['topics']:
                    lines.append(f"**{t['title']}** — {t['description']}")
                section_texts[section] = "\n\n".join(lines)

        # 4) Afbeeldingen genereren (strict: precies 4 of fout)
        with st.spinner("Doodles worden getekend.."):
            try:
                images_map = generate_all_images(clean_input)
            except Exception as e:
                st.session_state.processing = False
                st.session_state.generation_completed = False
                st.error(f"Afbeeldingen genereren mislukt: {e}")
                st.stop()

        # 5) Labels + logo + frame
        images_with_labels = {}
        images_final = {}
        for section in sections_order:
            annotations = [
                {"label": clean_input[section]['titels'][0], "x_pct": 0.10, "y_pct": 0.40},
                {"label": clean_input[section]['titels'][1], "x_pct": 0.70, "y_pct": 0.40},
                {"label": clean_input[section]['titels'][2], "x_pct": 0.10, "y_pct": 0.85},
                {"label": clean_input[section]['titels'][3], "x_pct": 0.70, "y_pct": 0.85},
            ]
            images_with_labels[section] = overlay_labels(images_map[section], annotations, font_size=45)
            images_final[section] = add_logo_with_frame(
                images_with_labels[section],
                logo_path="imgs/logo.png",  # jouw gekleurde logo
                title=section.title(),
                output_path=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{section}.png",
                font_path="./fonts/Avenir Regular.ttf",
                font_size=40,
                padding=10,
                bg_color=(225, 238, 230),
                logo_ratio=0.22,
                frame_width=10
            )

        # 6) State opslaan
        st.session_state.prompts = clean_input
        st.session_state.images = [images_final[s] for s in sections_order]
        st.session_state.input_text = section_texts
        st.session_state.last_upload_name = uploaded_file.name
        st.session_state.processing = False
        st.session_state.generation_completed = True
        st.session_state.idx = 0
        st.rerun()

# ---------- Weergave ----------
if st.session_state.generation_completed and 'images' in st.session_state:
    images = st.session_state.images
    names = [s for s in sections_order if s in st.session_state.input_text]
    i = st.session_state.idx

    st.write("<br>" * 2, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Vorige", key="prev_btn"):
            st.session_state.idx = max(st.session_state.idx - 1, 0)

    with col3:
        if st.button("Volgende", key="next_btn"):
            st.session_state.idx = min(st.session_state.idx + 1, len(images) - 1)

    # >>> lees i pas na het verwerken van de knoppen
    i = st.session_state.idx

    with col2:
        st.markdown(f"<h3 style='text-align: center;'>{ui_titles[i]}</h3>", unsafe_allow_html=True)

    st.image(images[i], use_container_width=True)
    with st.expander(f"**Toelichting**", expanded=False):
        st.markdown(st.session_state.input_text[names[i]])

    col1, col2, col3 = st.columns([1, 3, 1])
    # with col1:
    #     st.write("<br>", unsafe_allow_html=True)
    #     if st.button("Nieuwe Doodler", type="primary"):
    #         st.session_state.file_uploader_key += 1
    #         for key in ['uploaded_file', 'last_upload_name', 'prompts', 'images', 'input_text', 'generation_completed']:
    #             st.session_state.pop(key, None)
    #         st.session_state.processing = False
    #         st.cache_data.clear()
    #         st.session_state.view = 'home'  # terug naar homescreen
    #         st.rerun()
    with col3:
        st.write("<br>", unsafe_allow_html=True)
        st.download_button(
            label="Download PDF",
            data=generate_pdf_bytes(names, images),
            file_name="Doodler.pdf",
            mime="application/pdf",
            type="primary"
        )
