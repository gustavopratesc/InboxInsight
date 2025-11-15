from pydantic import BaseModel
from typing import List

class EmailRequest(BaseModel):
    email_text: str

class EmailResponse(BaseModel):
    categoria: str
    subcategoria: str
    sentimento: str
    explicacao: str
    reply_main: str
    reply_short: str
    reply_formal: str
    reply_technical: str

class BatchEmailRequest(BaseModel):
    emails: List[str]

class BatchEmailResponse(BaseModel):
    resultados: List[EmailResponse]
