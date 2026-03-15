import re
import requests


def extract_ark(url):

    m = re.search(r"(ark:/12148/[a-z0-9]+)", url)

    if m:
        return m.group(1)

    return None


def manifest_url(ark):

    return f"https://gallica.bnf.fr/{ark}/manifest.json"


def get_all_pages_urls(url):

    ark = extract_ark(url)

    if not ark:
        return None

    m_url = manifest_url(ark)

    r = requests.get(m_url)

    if r.status_code != 200:
        return None

    data = r.json()

    pages = []

    # IIIF v2

    if "sequences" in data:

        canvases = data["sequences"][0]["canvases"]

        for i, c in enumerate(canvases):

            page = i + 1

            pages.append(
                f"https://gallica.bnf.fr/{ark}/f{page}.image"
            )

    # IIIF v3

    elif "items" in data:

        for i, c in enumerate(data["items"]):

            page = i + 1

            pages.append(
                f"https://gallica.bnf.fr/{ark}/f{page}.image"
            )

    return pages
