# InboxInsight – Classificador Inteligente de E-mails

O InboxInsight é uma plataforma completa para análise, categorização e resposta automática de e-mails utilizando IA generativa.
O sistema foi projetado para case da vaga estágio da AutoU - Digital Transformation with AI. A versão atual é limitada e comporta no máximo 10 e-mails curtos.

**Rodar 1º o back-end:**  
https://inboxinsight-x8w5.onrender.com

**Rodar 2º o front-end:**  
https://inbox-insight-virid.vercel.app

---

## A solução inclui

- Backend em FastAPI com processamento assíncrono  
- Frontend moderno em HTML/CSS/JS  
- Integração com Groq (LLaMA 3.1)  
- Suporte a múltiplos formatos: texto, e arquivos (TXT e PDF)  
- Exportação de resultados  
- Histórico local de consultas  
- Modo escuro/claro inspirado em layouts minimalistas como Lovable

---

## Tecnologias Utilizadas

### Back-end
- Python 3.10+
- FastAPI
- Uvicorn
- PyPDF2
- AsyncIO + Semaphore (controle de paralelismo)
- Groq API (LLaMA 3.1-8B Instant)

### Front-end
- HTML5  
- CSS3 (layout minimalista baseado no Lovable)  
- JavaScript Vanilla  
- LocalStorage para histórico  
- Upload inteligente de PDF/TXT  
- Split avançado de blocos de e-mail
- Lovable (Insipiração layout)

### Infraestrutura
- Backend hospedado no Render  
- Frontend hospedado na Vercel  
- IA executada via Groq Cloud  

### Suporte de Desenvolvimento
- GPT-5.1
- WindSurf (auto-complete)
- Lovable (inspiração para layout) - link: https://lovable.dev/projects/2451982b-45c6-4c09-95c1-ae559c1ea696?magic_link=mc_80ec30b1-d2d8-4c90-be96-7b2104dcf1f0
---

## Funcionalidades

### Classificação Inteligente
- Produtivo vs Improdutivo  
- Subcategoria (ex.: atualização, follow-up, urgência)  
- Sentimento  
- Explicação objetiva  

### Geração de Respostas
- Resposta principal  
- Resposta curta  
- Resposta formal  
- Resposta técnica  

### Processamento de Arquivos
- Leitura de PDFs com múltiplos e-mails  
- Leitura de TXT com vários blocos  
- Separação automática usando marcadores corporativos  
- Remoção de artefatos de PDF  

### Histórico
- Salvo localmente no navegador  
- Reexibição instantânea  
- Exportação para Excel (Para análise de emails indesejados)  

### UI
- Interface responsiva  
- Tema claro/escuro  
- Estilo minimalista inspirado em Lovable  

---

## Como utilizar

### Método 1 — Digitar e-mails
Cole ou escreva o e-mail na caixa de texto e clique em **Analisar**.

### Método 2 — Upload de TXT
Envie um arquivo `.txt` contendo vários e-mails separados por linhas ou assinaturas.  
O sistema identifica os blocos automaticamente.

### Método 3 — Upload de PDF
Envie PDFs contendo múltiplos e-mails ou comunicações internas.  
O sistema extrai cada bloco utilizando marcadores de finalização e limpeza avançada.

### Resultado exibido
- Categoria  
- Subcategoria  
- Sentimento  
- Explicação  
- Resposta principal e alternativas  
- Histórico persistido automaticamente  

---

## Limitações

### Sobre extração de PDF
- PDFs escaneados sem OCR não funcionam  
- PDFs com colunas ou tabelas podem gerar blocos desconexos  
- E-mails muito curtos podem ser descartados  
- E-mails com muitas quantidades e grandes podem gerar conflitos
- Arquivos PDFs e TXT possuem mais chances de falha de análise

### Sobre a IA
- Pode devolver JSON mal formatado  
- Correções automáticas são aplicadas, mas erros críticos viram “Erro”  
- E-mails sem conteúdo corporativo tendem a ser improdutivos  
- Modelo Groq 8B é rápido, porém menos contextual que modelos maiores  

### Sobre requisições
- Limite de 5 requisições simultâneas para evitar erro 429  
- Em volume alto, o processamento pode ficar mais lento  

---

## Autor

Desenvolvido por **Gustavo Prates Caetano**.  
Focado em back-end Python, FastAPI, IA aplicada e produtividade.

