"""Fetch a Splice sample page, extract S3 URL, download and descramble."""
import requests
import re
import html
import sys
import os
from descramble import descramble

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")


def fetch_and_descramble(sample_url: str, output: str = None):
    print(f"Fetching page: {sample_url}")
    page = requests.get(sample_url, headers={"User-Agent": "Mozilla/5.0"})

    # Extract original filename from <h1> tag
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', page.text)
    clean_title = None
    if h1_match:
        raw_name = html.unescape(h1_match.group(1)).strip()
        # Strip audio extensions - we always save as .mp3
        clean_title = re.sub(r'\.(wav|aif|aiff|flac|mp3|ogg)$', '', raw_name, flags=re.IGNORECASE)
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', clean_title)
        print(f"Sample: {clean_title}")

    # Extract S3 URL
    pattern = r'https://spliceproduction\.s3\.us-west-1\.amazonaws\.com/audio_samples/[^"\s<>]+'
    matches = re.findall(pattern, page.text)

    if not matches:
        print("No S3 URL found in page!")
        return

    s3_url = html.unescape(matches[0])
    s3_url = s3_url.rstrip("\\")

    # Download scrambled MP3
    r = requests.get(s3_url, headers={"Referer": "https://splice.com/", "Origin": "https://splice.com"})
    print(f"Download status: {r.status_code}, size: {len(r.content)} bytes")

    if r.status_code != 200:
        print(f"Failed! Response: {r.text[:200]}")
        return

    # Descramble
    mp3 = descramble(r.content)

    # Save with sample title as filename into downloads dir
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    if output:
        out_file = output
    elif clean_title:
        out_file = os.path.join(DOWNLOAD_DIR, f"{clean_title}.mp3")
    else:
        out_file = os.path.join(DOWNLOAD_DIR, "output.mp3")

    with open(out_file, "wb") as f:
        f.write(mp3)
    print(f"Saved to {out_file} ({len(mp3)} bytes)")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else input("Splice sample URL: ").strip()
    output = sys.argv[2] if len(sys.argv) > 2 else None
    fetch_and_descramble(url, output)
