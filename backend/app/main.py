from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import EmailRequest, EmailResponse
from app.services.ai_service import analyze_email_with_ai, validate_json
from typing import List
from fastapi import UploadFile, File, HTTPException
from app.schemas import (
    EmailRequest,
    EmailResponse,
    BatchEmailRequest,
    BatchEmailResponse,
)
import io
from PyPDF2 import PdfReader


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"], # lista dominios que podem acessar API 
    allow_credentials=True, # permite cookies
    allow_methods=["*"], # libera get, post,, patch put, delete, update
    allow_headers=["*"], # libera envio do Json
)

def split_emails(raw_text: str) -> List[str]:
    """Divide os emails em ---"""

    blocos = raw_text.split("---")
    emails = [b.strip() for b in blocos if b.strip()]
    return emails
    

@app.get("/")
def read_root():
    return {"message": "API oK!"}

@app.post("/analyze", response_model=EmailResponse)
def analyze_email(payload: EmailRequest):
    
    email_text = payload.email_text

    try:
        # Chama a ia
        ai_response = analyze_email_with_ai(email_text)

        # Converte o texto string para dict
        data = validate_json(ai_response)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f'Erro ao processar IA {str(e)}'
            )

@app.post('/analyze-batch-json', response_model=BatchEmailResponse)
def analyze_batch_json(payload: BatchEmailRequest):
    responses = []

    for email_text in payload.emails:
        if not email_text.strip():
            continue
        try:
            ai_response = analyze_email_with_ai(email_text)
            data = validate_json(ai_response)
            responses.append(data)
        except Exception as e:
            responses.append({
                "categoria": "Erro",
                "subcategoria": "-",
                "sentimento": "-",
                "reply_main": "",
                "reply_short": "",
                "reply_formal": "",
                "reply_technical": "",
                "explicacao": f"Falha ao processar IA: {str(e)}"
            })

    return {"resultados": responses}

@app.post('/analyze-batch-txt', response_model=BatchEmailResponse)
async def analyze_multiple_txt(file: UploadFile = File(...)):
    '''
    recebe um arquivo .txt e retorna analises de varios emails separados por ---
    '''
    conteudo_bytes = await file.read()
    conteudo = conteudo_bytes.decode("utf-8", errors="ignore")

    emails = split_emails(conteudo)

    responses = []

    for email_text in emails:
        try:
            ai_response = analyze_email_with_ai(email_text)
            data = validate_json(ai_response)
            responses.append(data)
        except Exception as e:
            responses.append({
                "categoria": "Erro",
                "subcategoria": "-",
                "sentimento": "-",
                "reply_main": "",
                "reply_short": "",
                "reply_formal": "",
                "reply_technical": "",
                "explicacao": f"Falha ao processar IA: {str(e)}"
            })

    return {"resultados": responses}

@app.post('/analyze-pdf', response_model=BatchEmailResponse)
async def analyze_multiple_pdf(file: UploadFile = File(...)):
    '''
    recebe um arquivo .pdf e retorna analises de varios emails separados por  e retorna as analises de cada bloco
    '''
    if file.content_type != "application/pdf":
        return {"error": "O arquivo não é PDF válido!"}
    
    # lê os bytes do pdf
    pdf_bytes = await file.read()

    # carrega o pdf a partir dos bytes
    reader = PdfReader(io.BytesIO(pdf_bytes))

    # extrai texto pagina por pagina
    texto_completo = ""
    for pagina in reader.pages:
        extraido = pagina.extract_text() or ""
        texto_completo += "\n" + extraido

    emails = split_emails(texto_completo)

    response = []

    for email_text in emails:
        if not email_text.strip():
            continue
        try:
            ai_response = analyze_email_with_ai(email_text)
            data = validate_json(ai_response)
            response.append(data)
        except Exception as e:
            response.append({
                "categoria": "Erro",
                "subcategoria": "-",
                "sentimento": "-",
                "reply_main": "",
                "reply_short": "",
                "reply_formal": "",
                "reply_technical": "",
                "explicacao": f"Falha ao processar IA: {str(e)}"
            })

    return {"resultados": response}