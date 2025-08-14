import requests
import streamlit as st

st.set_page_config(page_title="Elevator OCR", page_icon="🛗", layout="wide")
st.title("🛗 Elevator OCR (Frontend)")

API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")

with st.sidebar:
    st.header("Settings")
    lang = st.text_input("Language(s)", value="eng", help="e.g. 'eng' or 'eng+deu'")
    psm = st.selectbox("PSM", options=list(range(0, 14)), index=3)
    oem = st.selectbox("OEM", options=[0, 1, 2, 3], index=3)
    binarize = st.checkbox("Binarize (threshold)", value=True)
    max_pages = st.number_input("Max PDF pages (0=all)", min_value=0, value=0, step=1)

uploaded = st.file_uploader("Upload image or PDF", type=["png","jpg","jpeg","pdf"])

def post_file(endpoint: str, file_bytes: bytes, filename: str):
    return requests.post(
        f"{API_BASE}{endpoint}",
        files={"file": (filename, file_bytes, "application/octet-stream")},
        data={
            "lang": lang,
            "psm": psm,
            "oem": oem,
            "binarize": str(binarize).lower(),
            "max_pages": max_pages,
        },
        timeout=120,
    )

if uploaded:
    ext = uploaded.name.lower().split(".")[-1]
    with st.spinner("Contacting OCR API..."):
        if ext == "pdf":
            r = post_file("/ocr/pdf", uploaded.read(), uploaded.name)
            r.raise_for_status()
            data = r.json()
            pages, texts = data["pages"], data["texts"]
            full_text = "\n\n".join([f"--- Page {i+1} ---\n{t}" for i, t in enumerate(texts)])
            st.success(f"Processed {pages} page(s).")
            st.download_button("⬇️ Download .txt", full_text, file_name=uploaded.name.rsplit(".",1)[0]+".txt")
            st.text_area("Text", value=full_text, height=520)
        else:
            r = post_file("/ocr/image", uploaded.read(), uploaded.name)
            r.raise_for_status()
            data = r.json()
            st.success("Image processed.")
            st.download_button("⬇️ Download .txt", data["text"], file_name=uploaded.name.rsplit(".",1)[0]+".txt")
            st.text_area("Text", value=data["text"], height=520)
