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
# normalise une URL image IIIF
# -----------------------
def normalize_iiif_url(img_url):
    # Remplace la fin de l'URL pour forcer native.jpg en full
    parts = img_url.rsplit("/", 4)
    if len(parts) >= 2:
        return parts[0] + "/full/full/0/native.jpg"
    return img_url

# -----------------------
# get images from manifest
# -----------------------
def get_images_from_manifest(ark):
    url = manifest_url(ark)
    try:
        r = requests.get(url, timeout=15)
    except Exception as e:
        st.error(f"Erreur réseau : {e}")
        return None

    if r.status_code != 200:
        st.error(f"Manifest HTTP {r.status_code}")
        return None

    try:
        data = r.json()
    except Exception:
        st.error("Manifest JSON invalide")
        return None

    images = []

    # IIIF v2
    if "sequences" in data:
        canvases = data["sequences"][0]["canvases"]
        for c in canvases:
            try:
                img = c["images"][0]["resource"]["@id"]
                images.append(normalize_iiif_url(img))
            except Exception:
                pass

    # IIIF v3 — ✅ itérer sur data["items"] et non data
    elif "items" in data:
        for canvas in data["items"]:
            try:
                img = canvas["items"][0]["items"][0]["body"]["id"]
                images.append(normalize_iiif_url(img))
            except Exception:
                pass

    return images if images else None

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
        try:
            r = requests.get(img, timeout=15)
            if r.status_code == 200:
                st.download_button(
                    "Télécharger cette page",
                    r.content,
                    file_name=f"page_{i}.jpg",
                    mime="image/jpeg",
                    key=f"page{i}"
                )
        except Exception:
            st.write("Erreur téléchargement page")

    # --------------------
    # download document
    # --------------------
    # ✅ key explicite pour éviter les conflits Streamlit
    if st.button(f"📥 Télécharger tout le document {i}", key=f"btn_dl_{i}"):
        if not ark:
            st.error("ARK non trouvé dans l'URL")
        else:
            with st.spinner("Chargement du manifest..."):
                imgs = get_images_from_manifest(ark)

            if not imgs:
                st.error("Aucune image trouvée dans le manifest")
            else:
                st.write(f"{len(imgs)} pages trouvées, téléchargement en cours...")
                progress = st.progress(0)
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
                    for n, img_url in enumerate(imgs):
                        try:
                            r = requests.get(img_url, timeout=15)
                            if r.status_code == 200:
                                z.writestr(f"page_{n+1:04d}.jpg", r.content)
                        except Exception:
                            pass
                        progress.progress((n + 1) / len(imgs))

                zip_buffer.seek(0)
                st.download_button(
                    "⬇️ Télécharger le ZIP",
                    zip_buffer,
                    file_name=f"{ark.replace('/', '_')}.zip",
                    mime="application/zip",
                    key=f"zip{i}"
                )
