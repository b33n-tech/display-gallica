import re
import requests
import streamlit as st
from typing import Optional

# --- Constantes ---
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# --- Fonctions ---
def extract_identifier(url: str) -> Optional[str]:
    """Extrait l'identifiant depuis une URL archive.org/details/<id>"""
    m = re.search(r"archive\.org/details/([^/?#]+)", url)
    return m.group(1) if m else None

def get_all_pages_urls(url: str) -> Optional[list[str]]:
    identifier = extract_identifier(url)
    if not identifier:
        st.error("URL non reconnue. Format attendu : https://archive.org/details/<identifiant>")
        return None

    # 1. Récupère le manifeste IIIF
    manifest_url = f"https://iiif.archivelab.org/iiif/{identifier}/manifest.json"
    try:
        r = requests.get(manifest_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        st.error(f"Erreur réseau ou HTTP : {e}")
        return None

    pages = []

    # IIIF v2 (sequences/canvases)
    if "sequences" in data:
        canvases = data["sequences"][0].get("canvases", [])
        for canvas in canvases:
            try:
                image_url = canvas["images"][0]["resource"]["@id"]
                pages.append(image_url)
            except (KeyError, IndexError):
                pass

    # IIIF v3 (items)
    elif "items" in data:
        for canvas in data["items"]:
            try:
                image_url = (
                    canvas["items"][0]["items"][0]["body"]["id"]
                )
                pages.append(image_url)
            except (KeyError, IndexError):
                pass

    if not pages:
        st.warning("Manifeste trouvé mais aucune image détectée.")
        return []

    return pages

# --- Interface Streamlit ---
st.title("📚 Archive.org – Extraction des pages")
st.caption("Colle l'URL d'un livre archive.org pour obtenir les liens directs vers toutes ses pages.")

url = st.text_input(
    "URL Archive.org",
    placeholder="https://archive.org/details/lartreligieuxdel0000emil_j3b4"
)

if url:
    with st.spinner("Récupération du manifeste IIIF..."):
        pages = get_all_pages_urls(url)

    if pages is not None and len(pages) > 0:
        st.success(f"✅ {len(pages)} page(s) trouvée(s).")

        with st.expander("Voir toutes les URLs", expanded=True):
            for i, p in enumerate(pages, 1):
                st.write(f"**Page {i}** — {p}")

        st.download_button(
            label="⬇️ Télécharger la liste (.txt)",
            data="\n".join(pages),
            file_name="pages_archive.txt",
            mime="text/plain"
        )
