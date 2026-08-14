# Classifies a cropped ring product photo as yellow / white / rose gold by
# sampling pixel colors and comparing channel differences. Calibrated against
# known reference SKUs from the Aug 2026 supplier PDF (see README.md).
#
# Usage: python3 classify_color.py /path/to/image.jpg
# Or import classify_color(path) into another script.

import sys
from PIL import Image

def classify_color(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    pixels = []
    for x in range(0, w, 3):
        for y in range(0, h, 3):
            r, g, b = im.getpixel((x, y))
            if r > 245 and g > 245 and b > 245:
                continue  # skip near-white background
            pixels.append((r, g, b))
    if not pixels:
        return "white"
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)
    diff_rg = avg_r - avg_g
    diff_gb = avg_g - avg_b
    if diff_gb - diff_rg > 15:
        return "yellow"
    elif diff_rg - diff_gb > 15:
        return "rose"
    else:
        return "white"

if __name__ == "__main__":
    path = sys.argv[1]
    print(classify_color(path))
