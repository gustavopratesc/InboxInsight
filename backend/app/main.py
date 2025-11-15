import asyncio
import re
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from PyPDF2 import PdfReader

# Importe seus módulos
from app.schemas import (
    EmailRequest,
    EmailResponse,
    BatchEmailRequest,
    BatchEmailResponse,
)
from app.services.ai_service import analyze_email_with_ai, validate_json


# Define um semáforo para limitar as requisições paralelas.
# A Groq é rápida, mas o plano gratuito pode ter limites de requisições/segundo.
# limitar a 5 chamadas simultâneas para evitar erros "429 Too Many Requests".
SEMAPHORE = asyncio.Semaphore(5)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://inbox-insight-virid.vercel.app"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def split_emails_smart(text: str) -> List[str]:
    """
    Divide o texto usando a mesma lógica Regex "smart" do frontend.
    Separa por múltiplas quebras de linha e filtra blocos pequenos.
    """
    if len(text) < 2000 and "\n\n" not in text: # Otimização simples
         return [text.strip()]

    parts = re.split(r"\n\s*\n{2,}", text)
    
    # Filtra partes que são muito curtas (assinaturas, rodapés, etc.)
    valid_parts = [p.strip() for p in parts if len(p.strip()) > 50]
    
    if len(valid_parts) > 1:
        return valid_parts
    else:
        # Se a divisão falhar, retorna o texto inteiro como um único item
        return [text.strip()]


@app.get("/")
def read_root():
    return {"message": "API oK!"}

async def process_single_email(email_text: str) -> dict:
    """
    Processa um único e-mail de forma assíncrona e trata exceções.
    """
    if not email_text.strip():
        return None # Ignora e-mails vazios

    
    # Agora, o loop await só executará 5 tarefas de process_single_email 
    # por vez, graças ao semáforo.
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
                "reply_main": "Não foi possível gerar resposta.",
                "reply_short": "Falha ao processar.",
                "reply_formal": "Não foi possível concluir a análise deste e-mail.",
                "reply_technical": "O processamento deste texto falhou devido a formato inválido ou resposta incorreta da IA.",
                "explicacao": f"Falha ao processar IA: {str(e)}",
                "email": email_text  # 
            }


@app.post("/analyze", response_model=EmailResponse)
async def analyze_email(payload: EmailRequest):
    email_text = payload.email_text
    try:
        data = await process_single_email(email_text)
        if data["categoria"] == "Erro":
            raise HTTPException(status_code=500, detail=data["explicacao"])
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Erro ao processar IA {str(e)}'
        )


@app.post('/analyze-batch-json', response_model=BatchEmailResponse)
async def analyze_batch_json(payload: BatchEmailRequest):
    
    tasks = [process_single_email(email) for email in payload.emails if email.strip()]
    results = await asyncio.gather(*tasks)
    responses = [r for r in results if r]
    return {"resultados": responses}


@app.post('/analyze-batch-txt', response_model=BatchEmailResponse)
async def analyze_multiple_txt(file: UploadFile = File(...)):
    conteudo_bytes = await file.read()
    conteudo = conteudo_bytes.decode("utf-8", errors="ignore")

    emails = split_emails_smart(conteudo)

    tasks = [process_single_email(email) for email in emails]
    results = await asyncio.gather(*tasks)
    responses = [r for r in results if r] # Filtra nulos
    return {"resultados": responses}


@app.post('/analyze-pdf', response_model=BatchEmailResponse)
async def analyze_multiple_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="O arquivo não é PDF válido!")
    
    pdf_bytes = await file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))

    texto_completo = ""
    for i, pagina in enumerate(reader.pages):
        extraido = pagina.extract_text() or ""
        texto_completo += extraido
        if i < len(reader.pages) - 1:
            texto_completo += "\n\n--PAGE_BREAK--\n\n"

    emails = split_emails_smart(texto_completo)

    tasks = [process_single_email(email) for email in emails]
    results = await asyncio.gather(*tasks)
    responses = [r for r in results if r] # Filtra nulos

    return {"resultados": responses}