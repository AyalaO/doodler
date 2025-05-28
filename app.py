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

# 2) Initialize the index in session_state
if "idx" not in st.session_state:
    st.session_state.idx = 0

# 3) Display the current image
st.image(images[st.session_state.idx], use_container_width=True)
st.caption(f"Plaatje {st.session_state.idx + 1} / {len(images)}")

# 4) Layout: Prev & Next buttons
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️   Vorige"):
        # go back, but not below zero
        st.session_state.idx = max(st.session_state.idx - 1, 0)
with col3:
    if st.button("Volgende   ➡️"):
        # go forward, but not past end
        st.session_state.idx = min(
            st.session_state.idx + 1, len(images) - 1
        )