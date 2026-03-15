import re
import requests
import streamlit as st
from typing import Optional

# --- Constantes ---
ARK_PATTERN = re.compile(r"(ark:/12148/[a-z0-9]+)")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# --- Fonctions ---
def extract_ark(url: str) -> Optional[str]:
    m = ARK_PATTERN.search(url)
    return m.group(1) if m else None

def manifest_url(ark: str) -> str:
    return f"https://gallica.bnf.fr/{ark}/manifest.json"

def get_all_pages_urls(url: str) -> Optional[list[str]]:
    ark = extract_ark(url)
    if not ark:
        return None

    try:
        r = requests.get(manifest_url(ark), headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        st.error(f"Erreur réseau ou HTTP : {e}")
        return None

    if "sequences" in data:
        canvases = data["sequences"][0].get("canvases", [])
    elif "items" in data:
        canvases = data["items"]
    else:
        st.warning("Format de manifeste IIIF non reconnu.")
        return []

    return [
        f"https://gallica.bnf.fr/{ark}/f{i + 1}.image"
        for i in range(len(canvases))
    ]

# --- Interface Streamlit ---
st.title("📖 Gallica – Extraction des pages")
st.caption("Colle l'URL d'un document Gallica pour obtenir les liens de toutes ses pages.")

url = st.text_input("URL Gallica", placeholder="https://gallica.bnf.fr/ark:/12148/...")

if url:
    with st.spinner("Récupération du manifeste IIIF..."):
        pages = get_all_pages_urls(url)

    if pages is None:
        st.error("Impossible d'extraire l'ARK ou de récupérer le manifeste.")
    elif len(pages) == 0:
        st.warning("Manifeste trouvé mais aucune page détectée.")
    else:
        st.success(f"✅ {len(pages)} page(s) trouvée(s).")

        with st.expander("Voir toutes les URLs", expanded=True):
            for i, p in enumerate(pages, 1):
                st.write(f"**Page {i}** — {p}")

        st.download_button(
            label="⬇️ Télécharger la liste (.txt)",
            data="\n".join(pages),
            file_name="pages_gallica.txt",
            mime="text/plain"
        )
