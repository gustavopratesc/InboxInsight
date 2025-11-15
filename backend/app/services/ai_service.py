import os
from groq import Groq
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

def normalize(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")

STOPWORDS_PT = {normalize(p) for p in STOPWORDS_PT}
CUSTOM_STOPWORDS = {normalize(p) for p in CUSTOM_STOPWORDS}


def preprocess_email(text: str) -> str:
    text = text.strip().replace("\n", " ").replace("\r", "")

    # remove acentos
    # CORREÇÃO: Corrigido o typo de 'unicodedadata' para 'unicodedata'
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




api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=api_key)

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

"""


def analyze_email_with_ai(email_text: str) -> str:

    
    # Chamada de pré-processamento única
    email_text_processed = preprocess_email(email_text)
    
    print("=== ENVIADO PARA IA ===")
    print(email_text_processed)
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": email_text_processed} # Envia o texto processado
        ],
        temperature=0.2
    )

    response_content = response.choices[0].message.content
    print("=== RESPOSTA DA IA ===", response_content)

    return response_content


def validate_json(text: str) -> dict:
    """
    Tenta parsear o JSON, corrigindo se a IA adicionar texto extra.
    """
    try:
        # Tenta parsear diretamente
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1 
        
        if start != -1 and end != -1 and end > start:
            json_text = text[start:end]
            try:
                # Tenta parsear o bloco extraído
                return json.loads(json_text)
            except json.JSONDecodeError:
                raise ValueError("Resposta da IA está inválida e não foi possível corrigir")
        
        
        raise ValueError("JSON invalido e não é possivel recuperar")