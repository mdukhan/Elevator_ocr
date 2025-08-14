from __future__ import annotations
from typing import List, Optional
import os

import pytesseract
from PIL import Image, ImageOps

try:
    from pdf2image import convert_from_bytes
    _HAS_PDF2IMG = True
except Exception:
    _HAS_PDF2IMG = False

try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False


class OCRService:
    """Simple OCR wrapper around Tesseract with optional preprocessing."""
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif os.name == "nt":  # Windows heuristics
            for p in (
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ):
                if os.path.exists(p):
                    pytesseract.pytesseract.tesseract_cmd = p
                    break

    def _binarize(self, img: Image.Image) -> Image.Image:
        if _HAS_CV2:
            import numpy as np
            arr = np.array(img.convert("L"))
            import cv2
            _, th = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return Image.fromarray(th)
        else:
            return ImageOps.autocontrast(img.convert("L")).point(lambda p: 255 if p > 128 else 0).convert("L")

    def image_to_text(self, image: Image.Image, *, lang="eng", psm=3, oem=3, binarize=True) -> str:
        proc = self._binarize(image) if binarize else image.convert("RGB")
        config = f"--psm {psm} --oem {oem}"
        return pytesseract.image_to_string(proc, lang=lang, config=config)

    def pdf_to_texts(self, pdf_bytes: bytes, *, lang="eng", psm=3, oem=3, binarize=True, max_pages: Optional[int] = None) -> List[str]:
        if not _HAS_PDF2IMG:
            raise RuntimeError("pdf2image not installed or Poppler missing.")
        pages = convert_from_bytes(pdf_bytes, dpi=300)
        if max_pages and max_pages > 0:
            pages = pages[:max_pages]
        texts: List[str] = []
        for pg in pages:
            proc = self._binarize(pg) if binarize else pg.convert("RGB")
            config = f"--psm {psm} --oem {oem}"
            texts.append(pytesseract.image_to_string(proc, lang=lang, config=config))
        return texts
