# import streamlit as st
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from helper import (
#     read_pdf,
#     rewrite_to_four_sections,
#     rewrite_to_image_prompt,
#     generate_image,
#     create_clickable_image_selector,
# )

# # set general settings
# st.set_page_config(page_title="Doodler", 
#                    page_icon="✏️", 
#                    initial_sidebar_state="expanded",
#                    menu_items={
#                         'Get Help': 'mailto:ayala.ohyon@gmail.com',
#                         'About': "Welkom bij Doodler!"
#                         }
#     )


# # --- Sidebar ---
# st.sidebar.image("imgs/logo_white.png")
# st.sidebar.image("imgs/explainer.png") 
# st.sidebar.write("""Zorggesprekken zijn vaak erg verbaal, snel en abstract. Ouders en jeugdigen missen overzicht en verliezen regie.
# Doodler brengt overzicht met AI-gegenereerde praatplaten – zodat iedereen aan tafel weet waar het over gaat.""")

# # --- Main page ---
# # CSS to control button width
# st.markdown(
#     """
#     <style>
#     /* make every Streamlit button at least 120px wide */
#     div.stButton > button {
#         min-width: 120px;
#     }
#     /* if you prefer buttons to stretch to fill their column: */
#     /* div.stButton > button { width: 100%; } */
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # Initiate session state for file reset
# if 'file_uploader_key' not in st.session_state:
#     st.session_state.file_uploader_key = 0

# titles = [
#     "Introductie",
#     "Klachten",
#     "Oorzaken", 
#     "Advies"
# ]

# # --- Carousel state ---
# if "idx" not in st.session_state:
#     st.session_state.idx = 0

# # --- Processing state to prevent infinite loops ---
# if "processing" not in st.session_state:
#     st.session_state.processing = False

# # --- Generation completed state ---
# if "generation_completed" not in st.session_state:
#     st.session_state.generation_completed = False

# # --- File upload section (only visible when no results are shown) ---
# if not st.session_state.generation_completed:
#     col1, col2, col3 = st.columns([1, 3, 1])
#     with col2:
#         st.subheader("Genereer een AI Doodle")
#         st.write("Upload een geanonimiseerd medisch verslag en wij maken er een doodle van.")
#         st.markdown("**1: Upload een medisch verslag** ")
#         uploaded_file = st.file_uploader("", type=['pdf'], key=f"file_uploader_{st.session_state.file_uploader_key}")
#         st.markdown("**2: Selecteer een stijl** ")
#         create_clickable_image_selector()
    
#         st.markdown("**3: Omschrijf patient karakteristieken** ")
#         patient_eigenschappen = st.text_input(label= "patient_eigenschappen", label_visibility="hidden")
        
#         # Store uploaded file in session state
#         if uploaded_file is not None:
#             st.session_state.uploaded_file = uploaded_file
        
#         # Generate button
#         generate_clicked = st.button("Genereer Doodle", type="primary")
        
#         # Error message if no file is uploaded and generate is clicked
#         if generate_clicked and uploaded_file is None:
#             st.error("⚠️ Upload eerst een PDF bestand voordat je doodles kunt genereren.")
# else:
#     # When results are shown, get the uploaded file from session state
#     uploaded_file = st.session_state.get('uploaded_file')
#     generate_clicked = False

# # --- Check if we should start generation ---
# should_generate = (
#     generate_clicked and 
#     uploaded_file is not None and 
#     not st.session_state.processing and
#     (
#         not st.session_state.generation_completed or
#         ("last_upload_name" not in st.session_state or 
#          st.session_state.last_upload_name != uploaded_file.name)
#     )
# )

# if should_generate:
#     st.session_state.processing = True
#     st.session_state.generation_completed = False
#     st.rerun()

# # --- Processing section ---
# if st.session_state.processing and uploaded_file is not None:
#     # show waiting image
#     st.write("<br>" * 2, unsafe_allow_html=True) 
#     st.image("imgs/placeholder.png", use_container_width=True)
    
#     # parse the PDF (cached)
#     with st.spinner("Adviesrapport wordt gelezen.."):
#         report = read_pdf(uploaded_file)

#     # structure into 4 sections (cached)
# with st.spinner("Verhaallijn wordt gemaakt.."):
#     sections = rewrite_to_four_sections(report)
#     input_text = {
#         "Eigenschappen": sections.alinea_1,
#         "Klachten": sections.alinea_2,
#         "Klacht Oorzaken": sections.alinea_3,
#         "Behandeladviezen": sections.alinea_4,
#     }

# with st.spinner("Doodlers worden ontworpen.."):
#     # write image prompt per section (sequential)
#     prompts = {
#         name: rewrite_to_image_prompt(txt, name, patient_eigenschappen)
#         for name, txt in input_text.items()
#     }

# with st.spinner("Doodles worden getekend.."):
#     # generate images per prompt (sequential)
#     images_dict = {
#         name: generate_image(prompt)
#         for name, prompt in prompts.items()
#     }

#     # save for next run
#     st.session_state.prompts = prompts
#     st.session_state.images = [images_dict[name] for name in input_text.keys()]
#     st.session_state.input_text = input_text    
#     st.session_state.last_upload_name = uploaded_file.name
#     st.session_state.idx = 0
#     st.session_state.processing = False
#     st.session_state.generation_completed = True
#     st.rerun()

# # --- Display results section (only if generation is completed) ---
# if st.session_state.generation_completed and 'images' in st.session_state:
#     images = st.session_state.images
#     names = list(st.session_state.input_text.keys())

#     st.write("<br>" * 2, unsafe_allow_html=True)
    
#     # --- Navigation buttons ---
#     col1, col2, col3 = st.columns([1, 3, 1])
#     with col1:
#         if st.button("Vorige"):
#             st.session_state.idx = max(st.session_state.idx - 1, 0)
#     with col3:
#         if st.button("Volgende"):
#             st.session_state.idx = min(st.session_state.idx + 1, len(images) - 1)

#     # --- Display current image & text ---
#     i = st.session_state.idx
#     st.image(images[i], use_container_width=True)

#     with st.expander(f"**{titles[st.session_state.idx]}**", expanded=False):
#         st.markdown(st.session_state.input_text[names[i]]) 

# # --- Reset button (only visible when there are results) ---
# if st.session_state.generation_completed:
#     st.write("<br>", unsafe_allow_html=True)
#     if st.button("🔄 Upload een nieuw bestand"):
#         # Reset the file uploader by changing the key and clearing session state
#         st.session_state.file_uploader_key += 1
#         st.session_state.uploaded_file = None
#         st.session_state.processing = False
#         st.session_state.generation_completed = False
#         st.cache_data.clear()  # This clears all cached functions
#         # Clear other states 
#         for key in ['last_upload_name', 'images', 'input_text', 'prompts']:
#             if key in st.session_state:
#                 del st.session_state[key]
#         st.rerun()

import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from helper import (
    read_pdf,
    rewrite_to_four_sections,
    rewrite_to_image_prompt,
    generate_image,
    generate_pdf_bytes,
)
# new imports at the top
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image

# set general settings
st.set_page_config(
    page_title="Doodler", 
    page_icon="✏️", 
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:ayala.ohyon@gmail.com',
        'About': "Welkom bij Doodler!"
    }
)

# --- Sidebar ---
st.sidebar.image("imgs/logo_white.png")
st.sidebar.image("imgs/explainer.png")
st.sidebar.write(
    """
    Zorggesprekken zijn vaak erg verbaal, snel en abstract. Ouders en jeugdigen missen overzicht en verliezen regie.
    Doodler brengt overzicht met AI-gegenereerde praatplaten – zodat iedereen aan tafel weet waar het over gaat.
    """
)

# --- Main page CSS ---
st.markdown(
    """
    <style>
    div.stButton > button {
        min-width: 135px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state variables
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = 0
if 'idx' not in st.session_state:
    st.session_state.idx = 0
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'generation_completed' not in st.session_state:
    st.session_state.generation_completed = False

# Titles for display
titles = ["Introductie", "Klachten", "Oorzaken", "Advies"]

# File upload and controls (when generation not completed)
if not st.session_state.generation_completed:
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.subheader("Genereer een AI Doodle")
        st.markdown("**1: Upload een medisch verslag** ")
        st.text("Kies een adviesgesprek verslag waar je een Doodle van wilt hebben")
        uploaded_file = st.file_uploader(
            "", type=['pdf'], key=f"file_uploader_{st.session_state.file_uploader_key}"
        )
        # st.markdown("**2: Selecteer een stijl** ")
        # create_clickable_image_selector()
        st.markdown("**2: Omschrijf patient karakteristieken** ")
        st.text("Omschrijf client uiterlijke kenmerk")
        patient_eigenschappen = st.text_input(
            label="patient_eigenschappen", label_visibility="hidden"
        )
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
        generate_clicked = st.button("Genereer Doodle", type="primary")
        if generate_clicked and 'uploaded_file' not in st.session_state:
            st.error("⚠️ Upload eerst een PDF bestand voordat je doodles kunt genereren.")
else:
    uploaded_file = st.session_state.uploaded_file
    generate_clicked = False

# Determine if generation should start
generate_condition = (
    generate_clicked and
    uploaded_file is not None and
    not st.session_state.processing and
    (
        not st.session_state.generation_completed or
        st.session_state.last_upload_name != uploaded_file.name
    )
)
if generate_condition:
    st.session_state.processing = True
    st.session_state.generation_completed = False
    st.rerun()

# Processing and generation pipeline
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    if st.session_state.processing and 'uploaded_file' in st.session_state:
        uploaded_file = st.session_state.uploaded_file
        # Step 1: Read PDF
        with st.spinner("Adviesrapport wordt gelezen.."):
            report = read_pdf(uploaded_file)
        # Step 2: Rewrite into 4 sections
        with st.spinner("Verhaallijn wordt gemaakt.."):
            sections = rewrite_to_four_sections(report)
            input_text = {
                "Eigenschappen": sections.alinea_1,
                "Klachten": sections.alinea_2,
                "Klacht Oorzaken": sections.alinea_3,
                "Behandeladviezen": sections.alinea_4,
            }
        # Step 3: Create prompts
        with st.spinner("Doodlers worden ontworpen.."):
            with ThreadPoolExecutor(max_workers=len(input_text)) as exe:
                prompt_futures = {
                    exe.submit(rewrite_to_image_prompt, txt, name, patient_eigenschappen): name
                    for name, txt in input_text.items()
                }
                prompts = {}
                for fut in as_completed(prompt_futures):
                    name = prompt_futures[fut]
                    prompts[name] = fut.result()
        # Step 4: Generate images
        with st.spinner("Doodles worden getekend.."):
            with ThreadPoolExecutor(max_workers=len(prompts)) as exe:
                image_futures = {
                    exe.submit(generate_image, pr): name
                    for name, pr in prompts.items()
                }
                images_dict = {}
                for fut in as_completed(image_futures):
                    name = image_futures[fut]
                    images_dict[name] = fut.result()

        # Save results and update state
        st.session_state.prompts = prompts
        st.session_state.images = [images_dict[name] for name in input_text.keys()]
        st.session_state.input_text = input_text
        st.session_state.last_upload_name = uploaded_file.name
        st.session_state.processing = False
        st.session_state.generation_completed = True
        st.session_state.idx = 0
        st.rerun()

# Display results when ready
if st.session_state.generation_completed and 'images' in st.session_state:
    images = st.session_state.images
    names = list(st.session_state.input_text.keys())
    i = st.session_state.idx
    st.write("<br>" * 2, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("Vorige"):
            st.session_state.idx = max(st.session_state.idx - 1, 0)
    with col2:
        st.markdown(f"<h3 style='text-align: center; '>{titles[i]}</h1>", unsafe_allow_html=True)
    with col3:
        if st.button("Volgende"):
            st.session_state.idx = min(
                st.session_state.idx + 1, len(images) - 1
            )
    st.image(images[i], use_container_width=True)
    with st.expander(f"**{titles[i]}**", expanded=False):
        st.markdown(st.session_state.input_text[names[i]])
    print(st.session_state.prompts)
    # Reset button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("Nieuwe Doodler", type="primary"): 
            st.session_state.file_uploader_key += 1
            for key in ['uploaded_file', 'last_upload_name', 'prompts', 'images', 'input_text', 'generation_completed']:
                st.session_state.pop(key, None)
            st.session_state.processing = False
            st.cache_data.clear()
    with col3:
        st.write("<br>", unsafe_allow_html=True)
        st.download_button(
            label="Download PDF",
            data=generate_pdf_bytes(names, images),
            file_name="doodles.pdf",
            mime="application/pdf",
            type="primary"
        ) 