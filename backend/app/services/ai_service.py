import os
from groq import Groq
from dotenv import load_dotenv
import json
import re
import unicodedata

STOPWORDS_PT = {
    "a", "o", "e", "é", "de", "do", "da", "mas", "ou", "para", "um", "uma",
    "que", "com", "por", "sobre", "em", "na", "no", "nos", "nas",
    "se", "já", "não", "sim", "como", "também", "porque", "qual",
    "isso", "esse", "essa", "foi", "ser", "tem", "têm"
}

CUSTOM_STOPWORDS = {
    "obrigado", "obrigada", "att", "atenciosamente",
    "qualquer", "coisa", "favor", "por", "gentileza"
}

# --- Normalizar stopwords (remove acentos e evita falhas no preprocessamento) ---
def normalize(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")

STOPWORDS_PT = {normalize(p) for p in STOPWORDS_PT}
CUSTOM_STOPWORDS = {normalize(p) for p in CUSTOM_STOPWORDS}


def preprocess_email(text: str) -> str:
    text = text.strip().replace("\n", " ").replace("\r", "")

    # remove acentos
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    # Normalização básica
    text = re.sub(r"\s+", " ", text)
    text = text.lower()

    # remove assinaturas
    assinaturas = ["att", "atenciosamente", "obrigado", "grato", "sds"]
    for p in assinaturas:
        text = re.sub(rf"\b{p}\b", "", text)

    text = re.sub(r"[^a-z0-9,.;:?!@%/\-\(\) ]", "", text)

    # remove disclaimers comuns
    text = re.sub(r"confidencial.*$", "", text)

    palavras = text.split()
    palavras = [
        p for p in palavras
        if p not in STOPWORDS_PT and p not in CUSTOM_STOPWORDS
    ]

    return " ".join(palavras).strip()


load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


SYSTEM_PROMPT = """(mantido igual — não repeti aqui para economizar espaço)"""


def analyze_email_with_ai(email_text: str) -> str:
    email_text = preprocess_email(email_text)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": email_text}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


def validate_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.find("}") + 1
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end])
            except:
                raise ValueError("Resposta da IA está inválida e não foi possível corrigir")
        raise ValueError("Json invalido e não é possivel recuperar")
