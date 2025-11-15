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
from app.services.ai_service import preprocess_email, clean_signatures


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

    END_MARKERS = [
        r"\batenciosamente\b",
        r"\batt\b",
        r"\bobrigado\b",
        r"\bobrigada\b",
        r"\bgrato\b",
        r"\bcordialmente\b",
        r"\babraços\b",
        r"\benviado do meu iphone\b",
        r"--+",
        r"—+",
        r"___+"
    ]

    # Quebra em linhas
    linhas = text.split("\n")

    emails = []
    buffer = []

    for linha in linhas:
        clean = linha.strip()

        # Ignora linha vazia sozinha
        if clean == "":
            buffer.append("")
            continue

        buffer.append(clean)

        # CONFERE SE É MARCADOR DE FINAL DE EMAIL
        for marker in END_MARKERS:
            if re.search(marker, clean, flags=re.IGNORECASE):
                bloco = "\n".join(buffer).strip()
                if len(bloco) > 40:  # evita lixo
                    emails.append(bloco)
                buffer = []
                break

    # Último bloco, se sobrou algo
    if buffer:
        bloco_final = "\n".join(buffer).strip()
        if len(bloco_final) > 40:
            emails.append(bloco_final)

    return emails if emails else [text.strip()]



#  PROCESSAMENTO DE 1 E-MAIL
async def process_single_email(email_text: str) -> dict:
    if not email_text.strip():
        return None

    email_text = clean_signatures(email_text)
    email_text = preprocess_email(email_text)

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
