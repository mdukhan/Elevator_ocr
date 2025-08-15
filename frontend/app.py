import json
import requests
import streamlit as st

st.set_page_config(page_title="Elevator OCR", page_icon="🛗", layout="wide")
st.title("🛗 Elevator OCR (Frontend)")

API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:8000")

# ---------------- Sidebar (OCR + LLM knobs) ----------------
with st.sidebar:
    st.header("OCR Settings")
    lang = st.text_input("Language(s)", value="eng", help="e.g. 'eng' or 'eng+deu'")
    psm = st.selectbox("PSM", options=list(range(0, 14)), index=3)
    oem = st.selectbox("OEM", options=[0, 1, 2, 3], index=3)
    binarize = st.checkbox("Binarize (threshold)", value=True)
    max_pages = st.number_input("Max PDF pages (0=all)", min_value=0, value=0, step=1)

    st.divider()
    st.header("LLM Settings")
    model_pick = st.selectbox("Model", ["llama3.1", "mistral", "phi3"], index=0,
                              help="Runs locally via Ollama")
    default_schema = "Document { title, date, vendor, total, items: [ { name, qty, price } ] }"
    schema = st.text_area("Schema (describe desired JSON)", value=default_schema, height=120)

uploaded = st.file_uploader("Upload image or PDF", type=["png", "jpg", "jpeg", "pdf"])

# --------------- Helpers ---------------
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

def call_llm_structure(text: str, schema: str, model: str):
    r = requests.post(
        f"{API_BASE}/nlp/structure",
        data={"text": text, "schema": schema, "model": model},
        timeout=180,
    )
    r.raise_for_status()
    return r.json()

# Keep last OCR text in session so user can run LLM without re-uploading
if "ocr_text" in st.session_state is False:
    st.session_state["ocr_text"] = ""

# --------------- OCR Flow ---------------
ocr_text = None
if uploaded:
    ext = uploaded.name.lower().split(".")[-1]
    with st.spinner("Contacting OCR API..."):
        if ext == "pdf":
            r = post_file("/ocr/pdf", uploaded.read(), uploaded.name)
            if r.status_code // 100 != 2:
                st.error(f"OCR error {r.status_code}")
                st.code(r.text)
            else:
                data = r.json()
                pages, texts = data["pages"], data["texts"]
                full_text = "\n\n".join([f"--- Page {i+1} ---\n{t}" for i, t in enumerate(texts)])
                st.success(f"Processed {pages} page(s).")
                st.download_button("⬇️ Download .txt",
                                   full_text,
                                   file_name=uploaded.name.rsplit(".", 1)[0] + ".txt")
                ocr_text = full_text
        else:
            r = post_file("/ocr/image", uploaded.read(), uploaded.name)
            if r.status_code // 100 != 2:
                st.error(f"OCR error {r.status_code}")
                st.code(r.text)
            else:
                data = r.json()
                st.success("Image processed.")
                st.download_button("⬇️ Download .txt",
                                   data["text"],
                                   file_name=uploaded.name.rsplit(".", 1)[0] + ".txt")
                ocr_text = data["text"]

# If we got OCR text, persist for LLM
if ocr_text:
    st.session_state["ocr_text"] = ocr_text

# Always show the OCR text area (if available)
left, right = st.columns(2)
with left:
    st.subheader("OCR Output")
    st.text_area("Text", value=st.session_state.get("ocr_text", ""), height=520)

# --------------- LLM Structuring ---------------
with right:
    st.subheader("LLM JSON (Structured)")
    colA, colB = st.columns([1, 1])
    with colA:
        run_llm = st.button("Send OCR text to LLM")
    with colB:
        clear_llm = st.button("Clear LLM Output")

    if clear_llm:
        st.session_state.pop("llm_json", None)

    if run_llm:
        if not st.session_state.get("ocr_text"):
            st.warning("No OCR text available. Upload a file first.")
        else:
            with st.spinner(f"Calling local LLM ({model_pick})..."):
                try:
                    result = call_llm_structure(st.session_state["ocr_text"], schema, model_pick)
                    if result.get("ok"):
                        st.session_state["llm_json"] = result["data"]
                    else:
                        st.error(result.get("error", "Unknown LLM error"))
                except requests.RequestException as e:
                    st.error(f"LLM request failed: {e}")

    if "llm_json" in st.session_state:
        st.json(st.session_state["llm_json"])
        st.download_button(
            "⬇️ Download JSON",
            json.dumps(st.session_state["llm_json"], ensure_ascii=False, indent=2),
            file_name="structured.json",
            mime="application/json",
        )
