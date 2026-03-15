import streamlit as st
import re

st.title("Gallica → Image viewer")

url = st.text_input(
    "URL Gallica",
    "https://gallica.bnf.fr/ark:/12148/bpt6k15568271/f65.image.r=toutankhamon?rk=321890;0"
)


def gallica_to_iiif(url):
    """
    Convertit URL gallica vers URL image IIIF
    """

    # ark
    ark_match = re.search(r"(ark:/12148/[a-z0-9]+)", url)
    
    # page fXX
    page_match = re.search(r"/f(\d+)", url)

    if not ark_match or not page_match:
        return None

    ark = ark_match.group(1)
    page = page_match.group(1)

    iiif = f"https://gallica.bnf.fr/iiif/{ark}/f{page}/full/full/0/native.jpg"

    return iiif


if url:

    iiif_url = gallica_to_iiif(url)

    if iiif_url:
        st.write("Image URL :", iiif_url)
        st.image(iiif_url, use_column_width=True)
    else:
        st.error("URL non reconnue")
