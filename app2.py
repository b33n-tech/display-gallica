import re
import requests
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
        print(f"Erreur lors de la récupération du manifeste : {e}")
        return None

    # IIIF v2
    if "sequences" in data:
        canvases = data["sequences"][0].get("canvases", [])
    # IIIF v3
    elif "items" in data:
        canvases = data["items"]
    else:
        return []

    return [
        f"https://gallica.bnf.fr/{ark}/f{i + 1}.image"
        for i in range(len(canvases))
    ]
