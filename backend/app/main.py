import asyncio
import re
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from PyPDF2 import PdfReader

from app.schemas import (
    EmailRequest,
    EmailResponse,
    BatchEmailRequest,
    BatchEmailResponse,
)
from app.services.ai_service import analyze_email_with_ai, validate_json


# Limite seguro de requisições simultâneas
SEMAPHORE = asyncio.Semaphore(5)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://inbox-insight-virid.vercel.app"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# SPLIT INTELIGENTE 
def split_emails_smart(text: str) -> List[str]:
    raw_parts = re.split(r"\n\s*\n{1,}", text)

    valid = []
    for block in raw_parts:
        block = block.strip()

        if len(block) < 20:
            continue

        if not re.search(r"[A-Za-z]", block):
            continue

        # e-mail válido costuma ter verbos de ação
        if not re.search(r"(enviar|segue|confirmar|agendar|revisar|favor|precisa|anexo)", block, re.IGNORECASE):
            if len(block) < 180:
                continue

        valid.append(block)

    if not valid:
        return [text.strip()]

    return valid


#  PROCESSAMENTO DE 1 E-MAIL
async def process_single_email(email_text: str) -> dict:
    if not email_text.strip():
        return None

    async with SEMAPHORE:
        try:
            loop = asyncio.get_event_loop()
            ai_response = await loop.run_in_executor(
                None, analyze_email_with_ai, email_text
            )
            data = validate_json(ai_response)
            data["email"] = email_text
            return data

        except Exception as e:
            return {
                "categoria": "Erro",
                "subcategoria": "-",
                "sentimento": "-",
                "reply_main": "",
                "reply_short": "",
                "reply_formal": "",
                "reply_technical": "",
                "explicacao": f"Falha ao processar IA: {str(e)}",
                "email": email_text
            }


@app.get("/")
def home():
    return {"message": "API OK!"}


# ENDPOINTS 

@app.post("/analyze", response_model=EmailResponse)
async def analyze_email(payload: EmailRequest):
    data = await process_single_email(payload.email_text)
    return data


@app.post("/analyze-batch-json", response_model=BatchEmailResponse)
async def analyze_batch_json(payload: BatchEmailRequest):
    tasks = [process_single_email(t) for t in payload.emails]
    results = await asyncio.gather(*tasks)
    return {"resultados": [r for r in results if r]}


@app.post("/analyze-batch-txt", response_model=BatchEmailResponse)
async def analyze_batch_txt(file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8", errors="ignore")
    blocks = split_emails_smart(content)

    tasks = [process_single_email(b) for b in blocks]
    results = await asyncio.gather(*tasks)
    return {"resultados": [r for r in results if r]}


@app.post("/analyze-pdf", response_model=BatchEmailResponse)
async def analyze_batch_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, detail="Arquivo não é PDF válido.")

    reader = PdfReader(io.BytesIO(await file.read()))

    text = ""
    for p in reader.pages:
        text += (p.extract_text() or "") + "\n\n"

    blocks = split_emails_smart(text)

    tasks = [process_single_email(b) for b in blocks]
    results = await asyncio.gather(*tasks)
    return {"resultados": [r for r in results if r]}
