# backend/main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io

from services.ocr import OCRService            # ← class-based OCR
from services.llm_service import LLMService    # ← Ollama LLM client

app = FastAPI(title="Elevator OCR API", version="1.0.0")

# CORS: allow Streamlit on another port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "version": "api-1.0.0"}

# ------- Services -------
svc = OCRService()      # uses pdf2image for PDFs (needs Poppler installed)
llm = LLMService()      # uses Ollama (respects OLLAMA_* env vars)

# -------- LLM: structure to JSON --------
@app.post("/nlp/structure")
async def nlp_structure(
    text: str = Form(...),
    schema: str = Form(...),            # e.g. "Invoice {invoice_number, date, vendor, total, items:[{name,qty,price}]}"
    model: str = Form("", description="optional: llama3.1 | mistral | phi3"),
):
    try:
        data = await llm.structure_text(text, schema_description=schema, model=(model or None))
        return {"ok": True, "data": data}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

# -------- OCR: image --------
@app.post("/ocr/image")
async def ocr_image_endpoint(
    file: UploadFile = File(...),
    lang: str = Form("eng"),
    psm: int = Form(3),
    oem: int = Form(3),
    binarize: bool = Form(True),
    max_pages: int = Form(0),  # ignored for images; kept to match frontend payload
):
    try:
        data = await file.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        return JSONResponse({"error": f"Invalid image: {e}"}, status_code=400)

    try:
        text = svc.image_to_text(img, lang=lang, psm=psm, oem=oem, binarize=binarize)
        return {"text": text}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# -------- OCR: PDF --------
@app.post("/ocr/pdf")
async def ocr_pdf_endpoint(
    file: UploadFile = File(...),
    lang: str = Form("eng"),
    psm: int = Form(3),
    oem: int = Form(3),
    binarize: bool = Form(True),
    max_pages: int = Form(0),  # 0 = all pages
):
    try:
        pdf_bytes = await file.read()
    except Exception as e:
        return JSONResponse({"error": f"Invalid PDF upload: {e}"}, status_code=400)

    try:
        texts = svc.pdf_to_texts(
            pdf_bytes,
            lang=lang,
            psm=psm,
            oem=oem,
            binarize=binarize,
            max_pages=(max_pages if max_pages and max_pages > 0 else None),
        )
        pages = len(texts)
        return {"pages": pages, "texts": texts}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
