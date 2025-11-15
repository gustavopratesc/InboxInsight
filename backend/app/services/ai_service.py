import os
import json
import re
import unicodedata
from groq import Groq



# Normalização básica

def preprocess_email(text: str) -> str:
    if not text:
        return ""

    # Remover caracteres invisíveis
    text = text.replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    # Normalização ASCII
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    text = text.strip()
    return text



# Remover assinaturas e rodapés *depois* do split

def clean_signatures(email: str) -> str:
    assinaturas = [
        r"\batenciosamente\b",
        r"\batt\b",
        r"\bcordialmente\b",
        r"\bobrigado\b",
        r"\bobrigada\b",
        r"\bgrato\b",
        r"\bgrata\b",
        r"\bmelhores cumprimentos\b",
        r"\babraços\b"
    ]

    for sig in assinaturas:
        email = re.sub(sig, "", email, flags=re.IGNORECASE)

    return email.strip()



#  Configuração do cliente Groq

API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=API_KEY)



#  System prompt para classificação

SYSTEM_PROMPT = """
Você é um classificador avançado chamado InboxInsight. 
Sua missão é analisar e-mails e responder EXCLUSIVAMENTE em JSON válido.

NUNCA gere texto fora de JSON.

{
  "categoria": "Produtivo ou Improdutivo",
  "subcategoria": "string",
  "sentimento": "positivo, neutro ou negativo",
  "explicacao": "string",
  "reply_main": "string",
  "reply_short": "string",
  "reply_formal": "string",
  "reply_technical": "string"
}
"""



#  Envia texto para a IA

def analyze_email_with_ai(email_text: str) -> str:
    print("\n=== EMAIL ORIGINAL ===")
    print(email_text)

    # Pré-processamento leve
    email_text_processed = preprocess_email(email_text)

    if len(email_text_processed) < 30:
        raise ValueError("Texto muito curto para análise")

    print("\n=== ENVIADO PARA IA ===")
    print(email_text_processed)

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": email_text_processed}
        ],
        temperature=0.2
    )

    result = response.choices[0].message.content
    print("\n=== RESPOSTA DA IA ===")
    print(result)

    return result



# Validar e corrigir JSON

def validate_json(text: str) -> dict:
    # 1) Tentativa direta
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    #  Tenta extrair o primeiro bloco { ... }
    start = text.find("{")
    end = text.rfind("}") + 1

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except:
            raise ValueError("JSON inválido — IA respondeu fora do formato esperado.")

    raise ValueError("JSON inválido — não foi possível recuperar nenhuma estrutura válida.")
