"""
generator.py — Gera a resposta final a partir da pergunta + trechos recuperados.

Esta é a peça central do RAG (ver SPEC, seção 5 e RF-05/RF-06):
pega os trechos que o retriever encontrou, monta um PROMPT rigoroso e pede
ao LLM uma resposta em português, baseada só nos trechos e com citação.

O prompt exige três coisas (o que faz o assistente ser confiável):
1. Responder APENAS com base nos trechos fornecidos (grounding).
2. CITAR o documento de origem de cada informação (RF-05).
3. Dizer "não encontrei na base" quando a resposta não estiver nos trechos,
   em vez de inventar (RF-06 — combate à alucinação).

Estratégia local → nuvem: usamos o Groq (grátis) agora; na Fase 7 trocamos
para Azure OpenAI. Como as duas APIs seguem o padrão OpenAI, o código muda
pouquíssimo — só a função get_llm().
"""

import sys
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

sys.path.append(str(Path(__file__).resolve().parent))
import config
from retriever import get_retriever


# ─── O PROMPT ─────────────────────────────────────────────────────
# Instrução de sistema: define o "caráter" e as regras do assistente.
SYSTEM_PROMPT = """Você é um assistente que responde perguntas sobre uma base de documentos.

Regras que você DEVE seguir:
1. Responda APENAS com base nos trechos fornecidos abaixo. Não use conhecimento próprio.
2. Sempre responda em português do Brasil, de forma clara e objetiva.
3. Ao final da resposta, cite as fontes usadas no formato: [Fonte: <título do documento>].
4. Se a resposta NÃO estiver nos trechos fornecidos, diga exatamente:
   "Não encontrei essa informação na base de documentos." — e não invente nada.
"""

# Modelo da mensagem do usuário: injeta os trechos e a pergunta.
USER_PROMPT = """Trechos recuperados da base:

{contexto}

---
Pergunta: {pergunta}

Responda seguindo as regras."""


def get_llm():
    """
    Devolve o modelo de chat conforme o MODO configurado.
    - local/groq: usa o Groq (grátis), via API compatível com OpenAI.
    - azure: usa Azure OpenAI (Fase 7).
    """
    if config.MODO == "azure":
        from langchain_openai import AzureChatOpenAI
        return AzureChatOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_deployment=config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            temperature=0,  # 0 = respostas mais factuais e estáveis
        )

    # Padrão: Groq (grátis). Usa o conector OpenAI apontando para a API do Groq.
    from langchain_openai import ChatOpenAI
    if not config.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY não encontrada. Crie o arquivo .env com sua chave "
            "(veja .env.example)."
        )
    return ChatOpenAI(
        api_key=config.GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",  # endpoint do Groq
        model=config.GROQ_MODEL,
        temperature=0,
    )


def _formatar_contexto(docs) -> str:
    """Transforma os trechos recuperados em texto para o prompt, com a fonte de cada um."""
    partes = []
    for i, d in enumerate(docs, 1):
        titulo = d.metadata.get("titulo", "desconhecido")
        partes.append(f"[Trecho {i} — Fonte: {titulo}]\n{d.page_content}")
    return "\n\n".join(partes)


def responder(pergunta: str, retriever=None, llm=None) -> dict:
    """
    Fluxo RAG completo de uma pergunta:
    recupera trechos -> monta prompt -> chama o LLM -> devolve resposta + fontes.

    Retorna um dict com a resposta e os trechos usados (para exibir na interface).
    """
    retriever = retriever or get_retriever()
    llm = llm or get_llm()

    # 1) Recupera os trechos relevantes (busca híbrida da Fase 3).
    docs = retriever.invoke(pergunta)

    # 2) Monta o prompt com os trechos como contexto.
    contexto = _formatar_contexto(docs)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ])

    # 3) Encadeia prompt -> LLM -> texto puro (LangChain Expression Language).
    chain = prompt | llm | StrOutputParser()
    resposta = chain.invoke({"contexto": contexto, "pergunta": pergunta})

    # Fontes únicas, para exibir separadamente na interface.
    fontes = []
    for d in docs:
        f = d.metadata.get("titulo", "?")
        if f not in fontes:
            fontes.append(f)

    return {"resposta": resposta, "fontes": fontes, "trechos": docs}


if __name__ == "__main__":
    # Teste: python src/generator.py
    perguntas = [
        "como funciona Machine LEANING?",
        "Quem foi o primeiro presidente do Brasil?",  # NÃO está na base — deve recusar
    ]
    for pergunta in perguntas:
        print("=" * 66)
        print(f"PERGUNTA: {pergunta}")
        print("=" * 66)
        r = responder(pergunta)
        print(r["resposta"])
        print(f"\n[Fontes recuperadas: {', '.join(r['fontes'])}]")
        print()
