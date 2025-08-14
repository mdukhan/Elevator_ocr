from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io

from services.ocr import OCRService

app = FastAPI(title="Elevator OCR API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

service = OCRService()  # auto-detect Tesseract path

class OCRImageResponse(BaseModel):
    text: str

class OCRPDFResponse(BaseModel):
    pages: int
    texts: list[str]

@app.get("/healthz")
async def health():
    return {"status": "ok"}

@app.post("/ocr/image", response_model=OCRImageResponse)
async def ocr_image(
    file: UploadFile = File(...),
    lang: str = Form("eng"),
    psm: int = Form(3),
    oem: int = Form(3),
    binarize: bool = Form(True),
):
    data = await file.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    text = service.image_to_text(img, lang=lang, psm=psm, oem=oem, binarize=binarize)
    return {"text": text}

@app.post("/ocr/pdf", response_model=OCRPDFResponse)
async def ocr_pdf(
    file: UploadFile = File(...),
    lang: str = Form("eng"),
    psm: int = Form(3),
    oem: int = Form(3),
    binarize: bool = Form(True),
    max_pages: int = Form(0),
):
    data = await file.read()
    texts = service.pdf_to_texts(data, lang=lang, psm=psm, oem=oem, binarize=binarize, max_pages=(max_pages or None))
    return {"pages": len(texts), "texts": texts}
