import streamlit as st

# set-up sidebar 
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #C8D2DA;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.image("imgs/logo.png")
st.sidebar.write("")
st.sidebar.write("")
my_upload = st.sidebar.file_uploader("")

# set-up main page
if my_upload is not None:
    # read data
    df = pd.read_excel(my_upload) 

# set-up mainpage
# 1) Your list of images (URLs or local file paths)
images = [
    "imgs/1.png",
    "imgs/2.png",
    "imgs/3.png",
    "imgs/4.png",
]

titles = [
    "Intro",
    "Klachten",
    "Oorzaken", 
    "Behandeling"
]

# 0) Inject CSS to control button width
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

# 2) Initialize the index in session_state
if "idx" not in st.session_state:
    st.session_state.idx = 0

# 3) Display the navigation buttons
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    if st.button("Vorige"):
        st.session_state.idx = max(st.session_state.idx - 1, 0)

with col3:
    if st.button("Volgende"):
        st.session_state.idx = min(st.session_state.idx + 1, len(images) - 1)

col2.subheader(titles[st.session_state.idx])

# 4) Display image, caption & description
st.image(images[st.session_state.idx], use_container_width=True)
# st.caption(f"Plaatje {st.session_state.idx + 1} / {len(images)}")
with st.expander(f"{titles[st.session_state.idx]} uitleg", expanded=False):
    st.markdown("""
    - **Vriendelijkheid en humor**: Je staat bekend als een vriendelijke en humorvolle jongere. Dit merk je vaak op school en thuis, waar je met je grapjes en vriendelijkheid mensen aan het lachen maakt en een fijne sfeer creëert.\n\n

    - **Basale sociale vaardigheden**: Je kunt gemakkelijk contact maken met anderen. Bijvoorbeeld als je iemand voor het eerst ontmoet, ben je goed in het beginnen van een gesprek.\n\n

    - **Cognitief ingesteld**: Je hebt interesses die soms anders zijn dan die van je leeftijdsgenoten. Dit kan bijvoorbeeld zijn als je dingen leuk vindt die andere kinderen niet direct snappen.\n\n

    - **Sterk rechtvaardigheidsgevoel**: Je vindt het belangrijk dat dingen eerlijk zijn en hebt daar soms uitgesproken meningen over, vooral als je ziet dat anderen onrecht worden aangedaan.\n\n

    - **Verbaal sterk en hoog werkgeheugen**: Jij kunt goed je gedachten onder woorden brengen en onthoudt veel dingen die je ziet of hoort, waardoor je vaak snel dingen oppikt in de les.
    """)