import re
import requests
import streamlit as st
from typing import Optional

ARK_PATTERN = re.compile(r"(ark:/12148/[a-z0-9]+)")

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
        r = requests.get(manifest_url(ark), timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        st.error(f"Erreur lors de la récupération du manifeste : {e}")
        return None

    if "sequences" in data:
        canvases = data["sequences"][0].get("canvases", [])
    elif "items" in data:
        canvases = data["items"]
    else:
        return []

    return [
        f"https://gallica.bnf.fr/{ark}/f{i + 1}.image"
        for i in range(len(canvases))
    ]

# --- Interface Streamlit ---
st.title("📖 Gallica – Extraction des pages")

url = st.text_input("Colle l'URL d'un document Gallica :")

if url:
    with st.spinner("Récupération du manifeste..."):
        pages = get_all_pages_urls(url)

    if pages is None:
        st.error("Impossible d'extraire l'ARK ou de récupérer le manifeste.")
    elif len(pages) == 0:
        st.warning("Manifeste trouvé mais aucune page détectée.")
    else:
        st.success(f"{len(pages)} page(s) trouvée(s).")
        st.write("**Liste des URLs :**")
        for p in pages:
            st.write(p)

        # Bouton pour tout copier
        all_urls = "\n".join(pages)
        st.download_button(
            label="⬇️ Télécharger la liste (.txt)",
            data=all_urls,
            file_name="pages_gallica.txt",
            mime="text/plain"
        )
