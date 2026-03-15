import streamlit as st
import re
import requests
import zipfile
import io

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Gallica Viewer",
    page_icon="📜",
    layout="centered",
)

st.markdown("""
<style>
    .main { max-width: 800px; margin: auto; }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

st.title("📜 Gallica Viewer / Downloader")
st.caption("Visualisez et téléchargez des documents depuis Gallica (BnF)")

# ─────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────

def extract_ark(url: str) -> str | None:
    """Extrait l'identifiant ARK d'une URL Gallica."""
    m = re.search(r"(ark:/12148/[a-zA-Z0-9]+)", url)
    return m.group(1) if m else None


def extract_page(url: str) -> int | None:
    """Extrait le numéro de folio depuis l'URL (ex: /f4)."""
    m = re.search(r"/f(\d+)", url)
    return int(m.group(1)) if m else None


def build_iiif_image_url(ark: str, page: int, size: str = "full") -> str:
    """Construit une URL image IIIF Gallica."""
    return f"https://gallica.bnf.fr/iiif/{ark}/f{page}/{size}/full/0/native.jpg"


def normalize_iiif_url(img_url: str) -> str:
    """
    Normalise une URL image IIIF en remplaçant les paramètres
    de fin par full/full/0/native.jpg.
    """
    # Supprime tout ce qui suit le 5e segment après le dernier identifiant
    # Format IIIF : .../identifier/region/size/rotation/quality.format
    # On garde jusqu'à l'identifiant de canvas et on force les params
    m = re.match(r"(https://gallica\.bnf\.fr/iiif/ark:/12148/[^/]+/f\d+)", img_url)
    if m:
        return m.group(1) + "/full/full/0/native.jpg"
    # Fallback : remplace juste les 4 derniers segments
    parts = img_url.rsplit("/", 4)
    if len(parts) == 5:
        return parts[0] + "/full/full/0/native.jpg"
    return img_url


def fetch_manifest(ark: str) -> dict | None:
    """
    Récupère le manifest IIIF d'un document Gallica.
    Essaie deux formats d'URL.
    """
    candidates = [
        f"https://gallica.bnf.fr/{ark}/manifest.json",
        f"https://gallica.bnf.fr/iiif/{ark}/manifest.json",
    ]
    for url in candidates:
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue
    return None


def extract_images_from_manifest(manifest: dict) -> list[str]:
    """
    Extrait toutes les URLs d'images depuis un manifest IIIF v2 ou v3.
    Retourne une liste d'URLs normalisées.
    """
    images = []

    # ── IIIF v2 ──────────────────────────────
    if "sequences" in manifest:
        try:
            canvases = manifest["sequences"][0]["canvases"]
            for canvas in canvases:
                img_url = canvas["images"][0]["resource"]["@id"]
                images.append(normalize_iiif_url(img_url))
        except (KeyError, IndexError, TypeError):
            pass

    # ── IIIF v3 ──────────────────────────────
    elif "items" in manifest:
        for canvas in manifest["items"]:
            try:
                img_url = canvas["items"][0]["items"][0]["body"]["id"]
                images.append(normalize_iiif_url(img_url))
            except (KeyError, IndexError, TypeError):
                pass

    return images


def fetch_bytes(url: str) -> bytes | None:
    """Télécharge le contenu binaire d'une URL. Retourne None en cas d'échec."""
    try:
        r = requests.get(url, timeout=20)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None


def build_zip(image_urls: list[str], progress_bar) -> io.BytesIO | None:
    """
    Télécharge toutes les images et les empaquète dans un ZIP.
    Met à jour la barre de progression.
    """
    total = len(image_urls)
    if total == 0:
        return None

    zip_buffer = io.BytesIO()
    downloaded = 0

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for n, url in enumerate(image_urls):
            data = fetch_bytes(url)
            if data:
                zf.writestr(f"page_{n + 1:04d}.jpg", data)
                downloaded += 1
            progress_bar.progress((n + 1) / total)

    zip_buffer.seek(0)
    return zip_buffer if downloaded > 0 else None


# ─────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────
if "entries" not in st.session_state:
    # Chaque entrée : {"url": str, "ark": str, "page": int|None}
    st.session_state.entries = []

# ─────────────────────────────────────────
# SAISIE URL
# ─────────────────────────────────────────
with st.form("input_form", clear_on_submit=True):
    url_input = st.text_input(
        "URL Gallica",
        placeholder="https://gallica.bnf.fr/ark:/12148/bpt6k5444412w/f4.item",
    )
    submitted = st.form_submit_button("➕ Ajouter et afficher")

if submitted:
    if not url_input.strip():
        st.warning("Veuillez entrer une URL.")
    else:
        ark = extract_ark(url_input)
        if not ark:
            st.error("❌ Impossible d'extraire un identifiant ARK depuis cette URL.")
        else:
            page = extract_page(url_input)
            st.session_state.entries.append({
                "url": url_input.strip(),
                "ark": ark,
                "page": page,
            })

# ─────────────────────────────────────────
# AFFICHAGE DES ENTRÉES
# ─────────────────────────────────────────
if not st.session_state.entries:
    st.info("Aucune URL ajoutée. Collez une URL Gallica ci-dessus pour commencer.")

for i, entry in enumerate(st.session_state.entries):
    ark  = entry["ark"]
    page = entry["page"]
    url  = entry["url"]

    st.divider()
    st.subheader(f"Document {i + 1}")
    st.code(ark, language=None)

    # ── Aperçu de la page ────────────────
    if page is not None:
        img_url = build_iiif_image_url(ark, page, size="1000,")
        st.image(img_url, caption=f"Folio f{page}", use_container_width=True)

        img_bytes = fetch_bytes(img_url)
        if img_bytes:
            st.download_button(
                label=f"⬇️ Télécharger la page f{page}",
                data=img_bytes,
                file_name=f"{ark.replace('/', '_')}_f{page}.jpg",
                mime="image/jpeg",
                key=f"dl_page_{i}",
            )
        else:
            st.warning("Impossible de télécharger cette page.")
    else:
        st.info("Pas de numéro de folio dans l'URL — aperçu non disponible.")

    # ── Téléchargement du document entier ─
    st.markdown("**Télécharger tout le document**")
    if st.button(f"📥 Lancer le téléchargement complet", key=f"dl_full_{i}"):
        with st.spinner("Récupération du manifest IIIF…"):
            manifest = fetch_manifest(ark)

        if manifest is None:
            st.error("❌ Manifest IIIF introuvable pour ce document.")
        else:
            image_urls = extract_images_from_manifest(manifest)
            if not image_urls:
                st.error("❌ Aucune image trouvée dans le manifest.")
            else:
                st.write(f"📄 {len(image_urls)} pages détectées. Téléchargement en cours…")
                progress = st.progress(0)
                zip_buf = build_zip(image_urls, progress)

                if zip_buf is None:
                    st.error("❌ Aucune image n'a pu être téléchargée.")
                else:
                    st.success("✅ ZIP prêt !")
                    st.download_button(
                        label="⬇️ Télécharger le ZIP",
                        data=zip_buf,
                        file_name=f"{ark.replace('/', '_')}.zip",
                        mime="application/zip",
                        key=f"dl_zip_{i}",
                    )

    # ── Supprimer l'entrée ───────────────
    if st.button(f"🗑️ Retirer ce document", key=f"remove_{i}"):
        st.session_state.entries.pop(i)
        st.rerun()
