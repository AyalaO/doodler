import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from helper import (
    read_pdf,
    rewrite_to_four_sections,
    rewrite_to_image_prompt,
    generate_image,
)

# set general settings
st.set_page_config(page_title="Doodler", 
                   page_icon="✏️", 
                   initial_sidebar_state="expanded",
                   menu_items={
                        'Get Help': 'mailto:ayala.ohyon@gmail.com',
                        'About': "# This is a header. This is an *extremely* cool app!"
                        }
    )


# --- Sidebar ---
st.sidebar.image("imgs/logo_white.png")
# st.sidebar.write("<br>" * 16, unsafe_allow_html=True) 
# upload = st.sidebar.file_uploader("")


# --- Main page ---
# CSS to control button width
st.markdown(
    """
    <style>
    /* make every Streamlit button at least 120px wide */
    div.stButton > button {
        min-width: 120px;
    }
    /* if you prefer buttons to stretch to fill their column: */
    /* div.stButton > button { width: 100%; } */
    </style>
    """,
    unsafe_allow_html=True,
)

# Initiate session state voforor file reset
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = 0

titles = [
    "Introductie",
    "Klachten",
    "Oorzaken", 
    "Advies"
]

# --- Carousel state ---
if "idx" not in st.session_state:
    st.session_state.idx = 0

# --- If no file: show start screen ---
if 'uploaded_file' not in st.session_state or st.session_state.uploaded_file is None:
    st.write("<br>" * 5, unsafe_allow_html=True) 
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.subheader("Doodler helpt het grote plaatje te bespreken")
        st.markdown("Doodler is een AI-tool waarmee patiënten hun medische kwestie beter kunnen begrijpen door middel van doodles.")
        st.write("<br>", unsafe_allow_html=True) 
        st.markdown("Upload een geanonimseerd medisch verslag en wij maken er een doodle van.")
        uploaded_file = st.file_uploader("", type=['pdf'])

    # Sla uploaded file op in session state
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
        st.rerun()
else:
    uploaded_file = st.session_state.uploaded_file
    # --- Only rerun generation when we see a new file ---
    if (
        "last_upload_name" not in st.session_state
        or st.session_state.last_upload_name != uploaded_file.name
    ):
        # show waiting image
        st.write("<br>" * 5, unsafe_allow_html=True) 
        st.image("imgs/placeholder.png", use_container_width=True)
        
        # parse the PDF (cached)
        with st.spinner("Adviesrapport wordt gelezen.."):
            report = read_pdf(uploaded_file)

        # structure into 4 sections (cached)
        with st.spinner("Verhaallijn wordt gemaakt.."):
            sections = rewrite_to_four_sections(report)
            input_text = {"Eigenschappen": sections.alinea_1,
                            "Klachten": sections.alinea_2,
                            "Klacht Oorzaaken": sections.alinea_3,
                            "Behandeladviezen": sections.alinea_4,
                        }

            # write image prompt per section
            with ThreadPoolExecutor(max_workers=len(input_text)) as exe:
                prompt_futures = {
                    exe.submit(rewrite_to_image_prompt, txt, name): name
                    for name, txt in input_text.items()
                }
                prompts = {}
                for fut in as_completed(prompt_futures):
                    name = prompt_futures[fut]
                    prompts[name] = fut.result()

        with st.spinner("Doodles worden getekend.."):
            # generate images 
            with ThreadPoolExecutor(max_workers=len(prompts)) as exe:
                image_futures = {
                    exe.submit(generate_image, pr): name
                    for name, pr in prompts.items()
                }
                images_dict = {}
                for fut in as_completed(image_futures):
                    name = image_futures[fut]
                    images_dict[name] = fut.result()

        # save for next run
        st.session_state.prompts = prompts
        st.session_state.images = [images_dict[name] for name in input_text.keys()]
        st.session_state.input_text = input_text    
        st.session_state.last_upload_name = uploaded_file.name
        st.session_state.idx = 0

    images = st.session_state.images
    names  = list(st.session_state.input_text.keys())

    # --- Navigation buttons ---
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Vorige"):
            st.session_state.idx = max(st.session_state.idx - 1, 0)
    with col3:
        if st.button("Volgende"):
            st.session_state.idx = min(st.session_state.idx + 1, len(images) - 1)

    # --- Display current image & text ---
    i = st.session_state.idx
    st.image(images[i], use_container_width=True)

    with st.expander(f"**{titles[st.session_state.idx]}**", expanded=False):
        st.markdown(st.session_state.input_text[names[i]]) 
    
    # Optie om een nieuw bestand te uploaden
    if st.button("🔄 Upload een nieuw bestand"):
        # Reset de file uploader door de key te veranderen en session state te wissen
        st.session_state.file_uploader_key += 1
        st.session_state.uploaded_file = None
        st.rerun()


