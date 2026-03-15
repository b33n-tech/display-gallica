import streamlit as st
import re
import requests
import zipfile
import io

st.title("Gallica viewer / downloader")


# -----------------------
# extract ark
# -----------------------

def extract_ark(url):

    m = re.search(r"(ark:/12148/[a-z0-9]+)", url)

    if m:
        return m.group(1)

    return None


# -----------------------
# page image
# -----------------------

def gallica_to_iiif(url):

    ark = extract_ark(url)

    page_match = re.search(r"/f(\d+)", url)

    if not ark or not page_match:
        return None

    page = page_match.group(1)

    return f"https://gallica.bnf.fr/iiif/{ark}/f{page}/full/full/0/native.jpg"


# -----------------------
# manifest url
# -----------------------

def manifest_url(ark):

    return f"https://gallica.bnf.fr/{ark}/manifest.json"


# -----------------------
# get images from manifest
# -----------------------

def get_images_from_manifest(ark):

    url = manifest_url(ark)

    r = requests.get(url)

    if r.status_code != 200:
        return None

    try:
        data = r.json()
    except:
        return None

    images = []

    # IIIF v2
    if "sequences" in data:

        canvases = data["sequences"][0]["canvases"]

        for c in canvases:

            try:
                img = c["images"][0]["resource"]["@id"]
                images.append(img)
            except:
                pass

    # IIIF v3
    elif "items" in data:

        for canvas in data:

            try:
                img = canvas["items"][0]["items"][0]["body"]["id"]
                images.append(img)
            except:
                pass

    return images


# -----------------------
# session
# -----------------------

if "urls" not in st.session_state:
    st.session_state.urls = []


# -----------------------
# input
# -----------------------

url = st.text_input("URL Gallica")

if st.button("Afficher"):

    if url:
        st.session_state.urls.append(url)


# -----------------------
# display
# -----------------------

for i, u in enumerate(st.session_state.urls):

    st.write("---")

    ark = extract_ark(u)

    img = gallica_to_iiif(u)

    if img:

        st.image(img)

        # download page

        try:

            r = requests.get(img)

            if r.status_code == 200:

                st.download_button(
                    "Télécharger page",
                    r.content,
                    file_name=f"page_{i}.jpg",
                    mime="image/jpeg",
                    key=f"page{i}"
                )

        except:
            st.write("Erreur page")


    # --------------------
    # download document
    # --------------------

    if st.button(f"📥 Télécharger tout le document {i}"):

        if not ark:

            st.error("ark non trouvé")

        else:

            st.write("Chargement manifest...")

            imgs = get_images_from_manifest(ark)

            if not imgs:

                st.error("Manifest introuvable")

            else:

                st.write(f"{len(imgs)} pages")

                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w") as z:

                    for n, img_url in enumerate(imgs):

                        try:

                            r = requests.get(img_url)

                            if r.status_code == 200:

                                z.writestr(
                                    f"page_{n+1}.jpg",
                                    r.content
                                )

                        except:
                            pass

                zip_buffer.seek(0)

                st.download_button(
                    "Télécharger ZIP",
                    zip_buffer,
                    file_name=f"{ark.replace('/', '_')}.zip",
                    mime="application/zip",
                    key=f"zip{i}"
                )
