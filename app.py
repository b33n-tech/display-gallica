import streamlit as st
import re

st.title("Gallica → Image viewer multi-URL")


# ---------- fonction conversion ----------

def gallica_to_iiif(url):

    ark_match = re.search(r"(ark:/12148/[a-z0-9]+)", url)
    page_match = re.search(r"/f(\d+)", url)

    if not ark_match or not page_match:
        return None

    ark = ark_match.group(1)
    page = page_match.group(1)

    iiif = f"https://gallica.bnf.fr/iiif/{ark}/f{page}/full/full/0/native.jpg"

    return iiif


# ---------- session state ----------

if "urls" not in st.session_state:
    st.session_state.urls = []


# ---------- input ----------

url = st.text_input(
    "Ajouter une URL Gallica",
    ""
)


# ---------- bouton ----------

if st.button("Afficher l'image"):

    if url:
        st.session_state.urls.append(url)


# ---------- affichage ----------

st.subheader("Images")

for u in st.session_state.urls:

    iiif = gallica_to_iiif(u)

    if iiif:
        st.image(iiif)
        st.caption(iiif)

    else:
        st.error(f"URL invalide : {u}")
