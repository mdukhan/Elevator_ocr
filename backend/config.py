# backend/config.py
import os

# --- Tesseract installation path (Windows) ---
# If Tesseract is in PATH, set this to None.
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# If your language files are not in the default tessdata folder, set this:
# Example: r"C:\Program Files\Tesseract-OCR\tessdata"
TESSDATA_PREFIX = None  # or r"C:\Program Files\Tesseract-OCR\tessdata"

# --- OCR defaults ---
# Default to German. You can switch at request time with ?lang=deu+eng
DEFAULT_LANG = "deu"

# OCR engine and page segmentation:
# OEM 3 = default LSTM; PSM 6 = assume a uniform block of text
DEFAULT_CONFIG = r"--oem 3 --psm 6"

# For pages with multiple columns, try: "--oem 3 --psm 4"
# For sparse text: "--oem 3 --psm 11"
