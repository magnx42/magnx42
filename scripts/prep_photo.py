"""Prep a photo for ASCII conversion: remove background, boost local contrast.

Output: source-prepped.png (grayscale + alpha). The alpha channel is kept so the
background can be mapped to blank space regardless of its brightness.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent


def main(src: str, crop: str | None = None) -> None:
    img = Image.open(src).convert("RGB")
    if crop:  # "left,top,right,bottom" in source pixels
        img = img.crop(tuple(int(v) for v in crop.split(",")))

    cut = remove(img)  # RGBA, subject isolated
    rgba = np.array(cut)
    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)

    # CLAHE: gives a flatly-lit face real highlights and shadows
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(6, 6))
    gray = clahe.apply(gray)

    out = np.dstack([gray, rgba[:, :, 3]])
    Image.fromarray(out, "LA").save(ROOT / "source-prepped.png")
    print(f"wrote source-prepped.png {out.shape[1]}x{out.shape[0]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: prep_photo.py <photo> [left,top,right,bottom]")
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
