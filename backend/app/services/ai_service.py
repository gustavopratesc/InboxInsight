import os
from groq import Groq
from dotenv import load_dotenv
import json
import re
import unicodedata
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer

STOPWORDS_PT = set(stopwords.words("portuguese"))
STEMMER = RSLPStemmer()

CUSTOM_STOPWORDS = {
    "obrigado", "obrigada", "att", "atenciosamente",
    "qualquer", "coisa", "favor", "por", "gentileza"
}


def preprocess_email(text: str) -> str:
    '''Pre processamento NLP para limpeza de dados do texto'''

    text = text.strip().replace("\n", " ").replace("\r", "")

    # remove acentos
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")

    text = re.sub(r"\s+", " ", text)

    text = text.lower()

    # remove assinaturas
    assinaturas = ["att", "atenciosamente", "obrigado", "grato", "sds"]
    for p in assinaturas:
        padrao = r"\b" + p + r"\b"
        text = re.sub(padrao, "", text)

    # remove caracteres especiais
    text = re.sub(r"[^a-zA-ZÀ-ÿ0-9,.;:?!@%/\-\(\) ]", "", text)

    # remove disclaimers comuns
    text = re.sub(r"confidencial.*$", "", text)

    palavras = text.split()
    palavras = [
        p for p in palavras
        if p not in STOPWORDS_PT and p not in CUSTOM_STOPWORDS
    ]

    return text.strip()

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
Você é um classificador avançado chamado InboxInsight. 
Sua missão é analisar e-mails e responder EXCLUSIVAMENTE em JSON válido.

NUNCA escreva nada fora do JSON.

Sua resposta deve seguir exatamente este formato:

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

Subcategoria deve ser uma das seguintes opções:

- Solicitação de Informação
- Pedido de Ação
- Atualização de Status
- Confirmação / Follow-up
- Reclamação / Problema
- Agradecimento
- Urgência / Prazo Crítico
- Alinhamento / Planejamento
- Reunião / Agendamento
- Outro

INSTRUÇÕES:
- Não explique nada.
- Não gere texto fora do JSON.
- Não use markdown.
- Não quebre a estrutura do JSON.

Regras para geração das respostas:

- reply_main: resposta natural, amigável e objetiva.
- reply_short: resposta extremamente curta (1 frase).
- reply_formal: resposta educada e profissional.
- reply_technical: resposta detalhada e orientada a processo, mencionando dados, sistemas ou etapas quando fizer sentido.

Sempre adapte a resposta ao conteúdo do e-mail recebido.
Cada resposta deve ser única e não pode ser apenas uma versão reescrita da outra.

Considere que todos os e-mails pertencem ao ambiente corporativo.
Considere que o remetente e o destinatário estão trabalhando juntos em um projeto ou atividade profissional.
Nunca gere respostas informais ou inadequadas.

Você deve sempre classificar o e-mail usando linguagem profissional.

Não invente dados ou informações que não estão no e-mail original.

Para classificar e-mails como PRODUTIVO ou IMPRODUTIVO, considere:

Indicadores de PRODUTIVO:
- presença de verbos de ação como: enviar, revisar, confirmar, agendar, atualizar.
- palavras corporativas como: reunião, projeto, prazo, anexo, documento.
- linguagem com objetivo claro ou solicitação.
- presença de datas, prazos ou itens mencionados.

Indicadores de IMPRODUTIVO:
- termos de spam como: promoção, grátis, clique aqui, ganhe, oferta.
- mensagens vagas sem objetivo: "bom dia", "beleza", "kkk".
- felicitações sem contexto profissional.
- conteúdo irrelevante ou que não exige ação.

Adicione no campo "explicacao" um resumo objetivo dos motivos que justificam a classificação.


"""

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

    json_output = response.choices[0].message.content

    return json_output

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
                raise ValueError('Resposta da IA está inválida e não foi possível corrigir')
        raise ValueError("Json invalido e não é possivel recuperar")
        