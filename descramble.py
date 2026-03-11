import requests
import sys

def descramble(data: bytes) -> bytes:
    """Splice MP3 descrambler.

    Format:
    - Byte 0-1: Header (skip)
    - Byte 2-10: Scrambled block size (little-endian, 8 bytes)
    - Byte 10-28: XOR key (18 bytes)
    - Byte 28+: Scrambled MP3 data

    Two blocks of 'size' bytes are XOR'd with the key:
    - Block 1: [0, size)
    - Block 2: [2*size, 3*size)
    """
    raw = bytearray(data)

    # Read size from bytes 2-10 (little-endian)
    size = 0
    for i in range(7, -1, -1):
        size = size * 256 + raw[2 + i]

    # Read XOR key from bytes 10-28
    key = raw[10:28]

    # MP3 data starts at byte 28
    mp3 = bytearray(raw[28:])

    # Descramble block 1: [0, size)
    block1_end = _xor_block(mp3, key, 0, size)

    # Descramble block 2: [2*size, 3*size) — NOT [size, 2*size)!
    block2_start = block1_end + size
    _xor_block(mp3, key, block2_start, block2_start + size)

    return bytes(mp3)


def _xor_block(data: bytearray, key: bytes, start: int, end: int) -> int:
    """XOR a block of data with key. Returns the index where it stopped."""
    key_idx = 0
    i = start
    while i < min(end, len(data)):
        if key_idx >= len(key):
            key_idx = 0
        xored = data[i] ^ key[key_idx]
        if xored == data[i]:
            # Key byte is 0 — sentinel, stop here
            break
        data[i] = xored
        key_idx += 1
        i += 1
    return i


def download_and_descramble(sample_hash: str, output: str = None):
    """Download scrambled MP3 from Splice and descramble it."""
    url = f"https://spliceproduction.s3.us-west-1.amazonaws.com/audio_samples/{sample_hash}-scrambled/{sample_hash}.mp3"

    headers = {
        "Referer": "https://splice.com/",
        "Origin": "https://splice.com",
    }

    print(f"Downloading scrambled MP3...")
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print(f"Failed to download: {r.status_code}")
        print("Note: S3 signed URL may be needed. Provide full URL as argument.")
        return

    print(f"Downloaded {len(r.content)} bytes")

    mp3_data = descramble(r.content)

    out_file = output or f"{sample_hash}.mp3"
    with open(out_file, "wb") as f:
        f.write(mp3_data)

    print(f"Saved descrambled MP3 to {out_file} ({len(mp3_data)} bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python descramble.py <s3_url_or_sample_hash> [output.mp3]")
        print("  python descramble.py <full_s3_signed_url> output.mp3")
        print("  python descramble.py <scrambled_file.mp3> output.mp3")
        sys.exit(1)

    arg = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None

    # If it's a local file, descramble directly
    if arg.endswith(".mp3") and not arg.startswith("http"):
        with open(arg, "rb") as f:
            data = f.read()
        mp3_data = descramble(data)
        out_file = output or arg.replace(".mp3", "_clean.mp3")
        with open(out_file, "wb") as f:
            f.write(mp3_data)
        print(f"Saved descrambled MP3 to {out_file} ({len(mp3_data)} bytes)")
    elif arg.startswith("http"):
        # Full URL provided
        print("Downloading from URL...")
        r = requests.get(arg, headers={"Referer": "https://splice.com/", "Origin": "https://splice.com"})
        if r.status_code == 200:
            mp3_data = descramble(r.content)
            out_file = output or "output.mp3"
            with open(out_file, "wb") as f:
                f.write(mp3_data)
            print(f"Saved descrambled MP3 to {out_file} ({len(mp3_data)} bytes)")
        else:
            print(f"Failed: {r.status_code}")
    else:
        # Assume it's a sample hash
        download_and_descramble(arg, output)
