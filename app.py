"""
app.py — Interface web do Assistente RAG (Streamlit).

Transforma o pipeline (retriever + generator) numa página clicável:
- caixa para digitar a pergunta;
- resposta formatada, com as fontes citadas;
- painel que revela os TRECHOS recuperados (RF-07 da spec: transparência —
  o usuário pode conferir em que trechos a resposta se baseou).

Rode com:  streamlit run app.py
(NÃO use "python app.py" — Streamlit tem seu próprio comando.)
"""

import sys
from pathlib import Path

import streamlit as st

# Permite importar os módulos de src/
sys.path.append(str(Path(__file__).resolve().parent / "src"))
from generator import responder, get_llm
from retriever import get_retriever


# ─── Configuração da página ───────────────────────────────────────
st.set_page_config(
    page_title="Assistente RAG — IA",
    page_icon="🔎",
    layout="wide",
)


# ─── Carregamento pesado, feito UMA vez e reaproveitado ───────────
# @st.cache_resource guarda o retriever e o llm na memória entre perguntas,
# para não recarregar o índice e o modelo a cada interação (seria lento).
@st.cache_resource(show_spinner="Carregando o índice e o modelo...")
def carregar_motor():
    retriever = get_retriever()
    llm = get_llm()
    return retriever, llm


# ─── Cabeçalho ────────────────────────────────────────────────────
st.title("🔎 Assistente RAG para Documentos")
st.caption(
    "Faça perguntas sobre uma base de artigos de IA (Wikipedia). "
    "As respostas se baseiam apenas nos documentos e citam a fonte."
)

# Barra lateral com informações do projeto.
with st.sidebar:
    st.header("Sobre o projeto")
    st.markdown(
        "- **Busca híbrida**: vetorial (FAISS) + palavra-chave (BM25), fundidas por RRF.\n"
        "- **Base**: 10 artigos da Wikipedia sobre Inteligência Artificial.\n"
        "- **Anti-alucinação**: se a resposta não está na base, o assistente avisa.\n"
        "- **Fontes citadas**: toda resposta indica de onde veio."
    )
    st.divider()
    st.markdown("Exemplos de perguntas:")
    st.markdown(
        "- O que é aprendizado por reforço?\n"
        "- Como funciona a arquitetura Transformer?\n"
        "- Qual a diferença entre IA e machine learning?"
    )


# ─── Motor carregado ──────────────────────────────────────────────
try:
    retriever, llm = carregar_motor()
except Exception as e:
    st.error(
        "Não foi possível iniciar o assistente. Verifique se o índice foi criado "
        "(`python src/indexer.py`) e se a chave da API está no arquivo `.env`.\n\n"
        f"Detalhe técnico: {e}"
    )
    st.stop()


# ─── Caixa de pergunta ────────────────────────────────────────────
pergunta = st.text_input(
    "Sua pergunta:",
    placeholder="Ex.: O que é uma rede neural?",
)

if pergunta:
    with st.spinner("Buscando nos documentos e gerando a resposta..."):
        resultado = responder(pergunta, retriever=retriever, llm=llm)

    # Resposta principal.
    st.markdown("### Resposta")
    st.write(resultado["resposta"])

    # Fontes citadas.
    if resultado["fontes"]:
        st.markdown("**Fontes consultadas:** " + ", ".join(
            f"`{f}`" for f in resultado["fontes"]
        ))

    # Painel expansível com os trechos recuperados (transparência).
    with st.expander("🔍 Ver os trechos recuperados que embasaram a resposta"):
        for i, doc in enumerate(resultado["trechos"], 1):
            titulo = doc.metadata.get("titulo", "?")
            st.markdown(f"**Trecho {i} — {titulo}**")
            st.caption(doc.page_content)
            st.divider()
