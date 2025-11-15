import os
import json
import re
import unicodedata
from groq import Groq


#  STOPWORDS
STOPWORDS_PT = {
    "a","o","e","é","de","do","da","mas","ou","para","um","uma","que","com","por",
    "sobre","em","na","no","nos","nas","se","já","não","sim","como","também",
    "porque","qual","isso","esse","essa","foi","ser","tem","têm"
}

CUSTOM_STOPWORDS = {
    "obrigado","obrigada","att","atenciosamente","favor","gentileza"
}

def normalize(s):
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode("utf-8")


STOPWORDS_PT = {normalize(p) for p in STOPWORDS_PT}
CUSTOM_STOPWORDS = {normalize(p) for p in CUSTOM_STOPWORDS}


# PRÉ-PROCESSAMENTO ROBUSTO 
def preprocess_email(text: str) -> str:
    if not text:
        return ""

    # remover BOM e espaçamentos invisíveis
    text = text.replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    # Normalização leve
    text = unicodedata.normalize("NFKD", text).encode("ascii","ignore").decode("utf-8")
    text = text.strip()

    # remover assinaturas repetitivas
    assinaturas = ["att","atenciosamente","obrigado","grato"]
    for p in assinaturas:
        text = re.sub(rf"\b{p}\b","", text, flags=re.IGNORECASE)

    return text.strip()



# CLIENT GROQ 
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


SYSTEM_PROMPT = """
Você é o classificador InboxInsight. Responda APENAS com JSON válido.

Formato obrigatório:
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

Regras para geração das respostas:

- reply_main: resposta natural, amigável e objetiva.
- reply_short: resposta extremamente curta (1 frase).
- reply_formal: resposta educada e profissional.
- reply_technical: resposta detalhada e orientada a processo, mencionando dados, sistemas ou etapas quando fizer sentido.

Sempre adapte a resposta ao conteúdo do e-mail recebido.
Cada resposta deve ser única e não pode ser apenas uma versão reescrita da outra.

Considere que todos os e-mails pertencem ao ambiente corporativo.
Considere que o remtente e o destinatário estão trabalhando juntos em um projeto ou atividade profissional.
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

NUNCA gere texto fora do JSON.
"""


# CHAMADA PRINCIPAL
def analyze_email_with_ai(email_text: str) -> str:
    processed = preprocess_email(email_text)

    # protege contra blocos inválidos
    if len(processed) < 25:
        return json.dumps({
            "categoria": "Erro",
            "subcategoria": "-",
            "sentimento": "-",
            "explicacao": "Bloco ignorado: texto muito curto.",
            "reply_main": "",
            "reply_short": "",
            "reply_formal": "",
            "reply_technical": ""
        })

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": processed}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


# VALIDA JSON 
def validate_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end])
            except:
                pass

        raise ValueError("JSON inválido e não foi possível corrigir")
