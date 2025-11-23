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
Você é um classificador corporativo avançado chamado InboxInsight.
Sua missão é analisar e-mails e responder EXCLUSIVAMENTE em JSON válido.

NUNCA escreva nada fora do JSON.
NUNCA use markdown.
NUNCA explique nada fora do JSON final.

A entrada pode estar:
- incompleta
- com quebras de linha bagunçadas
- com palavras quebradas por hífens
- com trechos curtos de PDF
- com ruídos como “Enviado do meu iPhone”, cabeçalhos e rodapés

Você deve RECONSTRUIR mentalmente o e-mail e classificá-lo da maneira mais fiel possível.

Um e-mail deve ser considerado válido mesmo que:
- contenha apenas 1–2 frases,
- não tenha formatação padrão,
- esteja sem assinatura,
- tenha sido extraído de PDF.

Só considere “texto inválido” se ele não contém nenhuma frase ou instrução compreensível.

-----------------------------------------------

FORMATO OBRIGATÓRIO DA RESPOSTA:

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

-----------------------------------------------

CRITÉRIOS PARA DEFINIR “PRODUTIVO”:
Considere PRODUTIVO quando houver:

1. Verbos de ação:
   enviar, revisar, confirmar, ajustar, resolver, verificar, atualizar,
   analisar, retornar, encaminhar, agendar.

2. Contexto corporativo:
   documento, projeto, prazo, reunião, acesso, relatório, demanda,
   aprovação, equipe, sistema, erro, entrega, suporte.

3. Qualquer frase que indique:
   - solicitação
   - expectativa de retorno
   - encaminhamento
   - alinhamento
   - dúvida técnica
   - instruções de trabalho

Um e-mail pode ser PRODUTIVO mesmo que seja CURTO.

Ex: 
"Segue o arquivo."  
"Pode revisar?"  
"Atualizei o documento."

-----------------------------------------------

CRITÉRIOS PARA DEFINIR “IMPRODUTIVO”:
Considere IMPRODUTIVO apenas se:

1. O texto contém:
   parabéns, promoções, spam, propagandas, tentativas de venda,
   conversas casuais, frases informais sem objetivo profissional.

2. É apenas uma saudação (“bom dia”, “boa tarde”).
3. Não existe NENHUMA ação, pedido, contexto ou informação relevante.

-----------------------------------------------

SUBCATEGORIAS PERMITIDAS:
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

-----------------------------------------------

INSTRUÇÕES PARA AS RESPOSTAS GERADAS:

reply_main:
- resposta completa e natural
- objetiva, educada e prática

reply_short:
- versão extremamente curta (1 frase)

reply_formal:
- tom profissional, respeitoso e corporativo

reply_technical:
- foque em processos, sistemas, etapas técnicas ou operacionais

-----------------------------------------------

IMPORTANTE:
Nunca rotule como improdutivo apenas porque o texto é curto.
Sempre tente interpretar o contexto real antes de decidir.

Se o e-mail contém convite para etapa, confirmação de recebimento, deadline, instruções ou aprovação, classifique como produtivo

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
