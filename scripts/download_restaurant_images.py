
#!/usr/bin/env python3

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "frontend" / "images" / "restaurant_preview"
REPORT = ROOT / "scripts" / "restaurant_image_preview.csv"

API_URL = "http://localhost:8000/restaurants"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "FoodExpressRestaurantImageResearch/1.0 (image preview script)"
LIMIT = 10


def request_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


def load_restaurants():
    url = API_URL + "?" + urllib.parse.urlencode({
        "limit": LIMIT,
        "offset": 0,
    })
    data = request_json(url)

    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("restaurants", data.get("items", data.get("data", [])))
    else:
        rows = []

    if not isinstance(rows, list):
        raise RuntimeError("Unexpected /restaurants API response")

    return rows[:LIMIT]


def search_commons(query):
    params = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 1000,
    })

    result = request_json(f"{COMMONS_API}?{params}")
    pages = result.get("query", {}).get("pages", {})
    candidates = []

    for page in pages.values():
        info = page.get("imageinfo", [])
        if not info:
            continue

        image = info[0]
        metadata = image.get("extmetadata", {})
        candidates.append({
            "title": page.get("title", ""),
            "image_url": image.get("thumburl") or image.get("url", ""),
            "page_url": "https://commons.wikimedia.org/wiki/" +
                        urllib.parse.quote(page.get("title", "").replace(" ", "_")),
            "license": metadata.get("LicenseShortName", {}).get("value", ""),
            "artist": metadata.get("Artist", {}).get("value", ""),
        })

    return candidates


def download_image(url, number):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "").split(";")[0].lower()

        if not content_type.startswith("image/"):
            raise ValueError(f"Not an image: {content_type}")

        data = response.read(12 * 1024 * 1024 + 1)

    if len(data) > 12 * 1024 * 1024:
        raise ValueError("Image is larger than 12 MB")

    if data.startswith(b"\xff\xd8\xff"):
        ext = ".jpg"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        ext = ".webp"
    elif data.startswith((b"GIF87a", b"GIF89a")):
        ext = ".gif"
    else:
        raise ValueError("Unsupported or unrecognized image format")

    destination = OUTPUT_DIR / f"{number}{ext}"
    with destination.open("xb") as file:
        file.write(data)

    return destination.name


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    restaurants = load_restaurants()
    if not restaurants:
        raise RuntimeError("No restaurants returned by the backend")

    fields = [
        "number", "restaurant_id", "restaurant_name", "address",
        "search_query", "filename", "image_title", "source_url",
        "license", "artist", "status", "details",
    ]

    with REPORT.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()

        for number, restaurant in enumerate(restaurants, start=1):
            name = str(restaurant.get("name") or "").strip()
            address = str(restaurant.get("address") or "").strip()
            category = str(restaurant.get("category") or "").strip()

            query = f'"{name}" {address}' if address else f'"{name}"'
            print(f"[{number}/{len(restaurants)}] Searching: {name}")

            record = {
                "number": number,
                "restaurant_id": restaurant.get("id", ""),
                "restaurant_name": name,
                "address": address,
                "search_query": query,
                "filename": "",
                "image_title": "",
                "source_url": "",
                "license": "",
                "artist": "",
                "status": "",
                "details": "",
            }

            try:
                candidates = search_commons(query)

                # If no venue-specific results, try cuisine/category terms.
                if not candidates and category:
                    query = f"{category} restaurant food"
                    record["search_query"] = query
                    candidates = search_commons(query)

                if not candidates:
                    record["status"] = "no_results"
                    record["details"] = "No Commons image results found"
                else:
                    # Candidate selection is automatic; venue match is unverified.
                    candidate = candidates[0]
                    record.update({
                        "image_title": candidate["title"],
                        "source_url": candidate["page_url"],
                        "license": candidate["license"],
                        "artist": candidate["artist"],
                    })

                    filename = download_image(candidate["image_url"], number)
                    record["filename"] = filename
                    record["status"] = "downloaded_unverified"
                    record["details"] = (
                        "Image downloaded; not verified as this specific restaurant. "
                        "Check licensing and relevance before publication."
                    )
                    print(f"  Saved: {filename} (venue match unverified)")

            except Exception as exc:
                record["status"] = "error"
                record["details"] = f"{type(exc).__name__}: {exc}"
                print(f"  Error: {exc}")

            writer.writerow(record)
            csvfile.flush()
            time.sleep(1.0)

    print("\nTest complete.")
    print(f"Images: {OUTPUT_DIR}")
    print(f"Report: {REPORT}")
    print("Review every photo manually before using it on the website.")


if __name__ == "__main__":
    main()
