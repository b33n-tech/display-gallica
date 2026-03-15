import streamlit as st
import re
import requests
import zipfile
import io

st.title("Gallica viewer + download document")


# -------------------
# conversion URL
# -------------------

def extract_ark(url):

    m = re.search(r"(ark:/12148/[a-z0-9]+)", url)

    if m:
        return m.group(1)

    return None


def gallica_to_iiif(url):

    ark = extract_ark(url)
    page_match = re.search(r"/f(\d+)", url)

    if not ark or not page_match:
        return None

    page = page_match.group(1)

    return f"https://gallica.bnf.fr/iiif/{ark}/f{page}/full/full/0/native.jpg"


def manifest_url(ark):

    return f"https://gallica.bnf.fr/iiif/{ark}/manifest.json"


# -------------------
# session
# -------------------

if "urls" not in st.session_state:
    st.session_state.urls = []


# -------------------
# input
# -------------------

url = st.text_input("URL Gallica")

if st.button("Afficher l'image"):

    if url:
        st.session_state.urls.append(url)


# -------------------
# affichage
# -------------------

for i, u in enumerate(st.session_state.urls):

    iiif = gallica_to_iiif(u)
    ark = extract_ark(u)

    if iiif:

        st.image(iiif)

        # ---- bouton download page

        r = requests.get(iiif)

        if r.status_code == 200:

            st.download_button(
                "Télécharger page",
                r.content,
                file_name=f"page_{i}.jpg",
                mime="image/jpeg",
                key=f"page{i}"
            )

        # ---------------------------
        # bouton download document
        # ---------------------------

        if st.button(f"📥 Télécharger tout le document {i}"):

            if not ark:
                st.error("ark non trouvé")
            else:

                m_url = manifest_url(ark)

                manifest = requests.get(m_url).json()

                canvases = manifest["sequences"][0]["canvases"]

                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w") as z:

                    for n, c in enumerate(canvases):

                        img = c["images"][0]["resource"]["@id"]

                        try:
                            img_data = requests.get(img).content

                            z.writestr(
                                f"page_{n+1}.jpg",
                                img_data
                            )

                        except:
                            pass

                zip_buffer.seek(0)

                st.download_button(
                    "Télécharger ZIP complet",
                    zip_buffer,
                    file_name=f"{ark.replace('/', '_')}.zip",
                    mime="application/zip",
                    key=f"zip{i}"
                )
