"""One-off helper (not part of the shipped app) used during development to
search Wikimedia Commons for openly-licensed sample photos, print their
license, and download the ones that check out. Kept here so the provenance
of data/samples/ is reproducible/inspectable, not because the app needs it
at runtime.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "vision-benchmark-dev-script/1.0 (github.com/manuelbomi)"}


def _get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def search(query, limit=10):
    q = f"{query} filetype:bitmap"
    params = f"?action=query&list=search&srsearch={urllib.parse.quote(q)}&srnamespace=6&format=json&srlimit={limit}"
    data = _get(API + params)
    titles = [item["title"] for item in data["query"]["search"]]
    return [t for t in titles if t.lower().endswith((".jpg", ".jpeg", ".png"))]


def get_info(title):
    params = f"?action=query&titles={urllib.parse.quote(title)}&prop=imageinfo&iiprop=url|extmetadata|size&format=json"
    data = _get(API + params)
    page = next(iter(data["query"]["pages"].values()))
    info = page["imageinfo"][0]
    meta = info.get("extmetadata", {})
    return {
        "url": info["url"],
        "width": info.get("width"),
        "height": info.get("height"),
        "license": meta.get("LicenseShortName", {}).get("value", "?"),
        "artist": meta.get("Artist", {}).get("value", "?"),
        "credit": meta.get("Credit", {}).get("value", "?"),
        "attribution_required": meta.get("AttributionRequired", {}).get("value", "?"),
    }


if __name__ == "__main__":
    query = sys.argv[1]
    for title in search(query, limit=int(sys.argv[2]) if len(sys.argv) > 2 else 10):
        time.sleep(1.5)
        try:
            info = get_info(title)
        except Exception as e:
            print(title, "ERROR", e)
            continue
        print(f"{title}\n  license={info['license']} attribution_required={info['attribution_required']} size={info['width']}x{info['height']}\n  url={info['url']}\n")
