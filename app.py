import streamlit as st

# set-up sidebar 
st.markdown("""
<style>
    [data-testid=stSidebar] {
        background-color: #C8D2DA;
    }
</style>
""", unsafe_allow_html=True)

# st.sidebar.image("imgs/logo_valident.png")
st.sidebar.write("")
st.sidebar.write("")
my_upload = st.sidebar.file_uploader("")

# set-up main page
if my_upload is not None:
    # read data
    df = pd.read_excel(my_upload)