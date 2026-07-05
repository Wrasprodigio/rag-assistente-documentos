"""
app.py — Interface web do Assistente RAG (Streamlit).

Design profissional (tema ESCURO): cabeçalho com degradê e textura, perguntas
de exemplo como cards, resposta em cartão destacado, fontes como etiquetas.
Identidade visual índigo -> teal (alinhada ao portfólio).

Rode com:  streamlit run app.py
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent / "src"))
from generator import responder, get_llm
from retriever import get_retriever


st.set_page_config(
    page_title="Assistente RAG · IA",
    page_icon="🔎",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ─── CSS: identidade índigo -> teal, TEMA ESCURO ──────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
.stApp { background: #16181F; }
.block-container { padding-top: 0 !important; max-width: 820px; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Hero (mantido — já é escuro) ── */
.hero {
    position: relative; margin: 0 0 26px;
    background: linear-gradient(135deg,#1E1B4B 0%,#2A2580 45%,#0B6E64 130%);
    padding: 40px 42px 34px; border-radius: 18px; overflow: hidden; color: #fff;
    box-shadow: 0 30px 60px -34px rgba(0,0,0,.7);
}
.hero::before {
    content:""; position:absolute; inset:0; opacity:.5;
    background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,.16) 1px, transparent 0);
    background-size: 22px 22px;
}
.hero::after {
    content:""; position:absolute; right:-70px; top:-70px; width:280px; height:280px;
    border-radius:50%; background: radial-gradient(circle,rgba(15,166,151,.45),transparent 70%); filter: blur(24px);
}
.hero-in { position: relative; }
.badge {
    display:inline-flex; align-items:center; gap:7px; font-family:'IBM Plex Mono',monospace;
    font-size:.7rem; letter-spacing:.12em; text-transform:uppercase;
    background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.25);
    padding:6px 13px; border-radius:99px; margin-bottom:16px;
}
.badge .pulse { width:7px;height:7px;border-radius:50%;background:#3DE6C4;
    box-shadow:0 0 0 0 rgba(61,230,196,.6); animation:pulse 2s infinite; }
@keyframes pulse { 70%{box-shadow:0 0 0 8px rgba(61,230,196,0)} }
.hero h1 { font-size:2.5rem; font-weight:800; letter-spacing:-.03em; line-height:1.05; margin-bottom:12px; }
.hero h1 .g { background:linear-gradient(90deg,#A9B4FF,#5FE9D0);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.hero p { color:#C4C9E8; font-size:1.04rem; max-width:52ch; line-height:1.55; }
.hero .chips { display:flex; gap:8px; flex-wrap:wrap; margin-top:20px; }
.hero .chip { font-family:'IBM Plex Mono',monospace; font-size:.68rem; letter-spacing:.05em; color:#DCE0F5;
    background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.16); padding:5px 11px; border-radius:7px; }

/* ── Rótulo de seção ── */
.seclabel { font-family:'IBM Plex Mono',monospace; font-size:.74rem; letter-spacing:.14em; text-transform:uppercase;
    color:#8B84FF; font-weight:600; margin:4px 0 14px; display:flex; align-items:center; gap:9px; }
.seclabel::before { content:""; width:20px; height:2px; background:linear-gradient(90deg,#6B63E8,#0FA697); border-radius:2px; }

/* ── Botões de exemplo estilizados como cards (escuros) ── */
div[data-testid="column"] .stButton button {
    width:100%; text-align:left; background:#1E2230 !important; border:1px solid #333A4D !important;
    border-radius:14px; padding:15px 18px; min-height:60px; transition:all .18s ease;
}
div[data-testid="column"] .stButton button div[data-testid="stMarkdownContainer"] p {
    color:#EDEFF7 !important; font-size:.92rem !important; font-weight:600 !important;
    text-align:left !important; line-height:1.35 !important; margin:0 !important;
}
div[data-testid="column"] .stButton button:hover {
    border-color:#8B84FF !important; background:#252A3A !important; transform:translateY(-2px);
    box-shadow:0 14px 30px -16px rgba(107,99,232,.6);
}
div[data-testid="column"] .stButton button:hover div[data-testid="stMarkdownContainer"] p {
    color:#B9C0FF !important;
}

/* ── Campo de texto (escuro, bem visível) ── */
.stTextInput > div > div > input {
    background:#1E2230; border:2px solid #3A4056; border-radius:12px; padding:16px 18px; font-size:1.02rem;
    color:#E7E9F2; box-shadow:0 2px 10px -4px rgba(0,0,0,.4);
}
.stTextInput > div > div > input:focus { border-color:#6B63E8; box-shadow:0 0 0 4px rgba(107,99,232,.22); }
.stTextInput > div > div > input::placeholder { color:#6B7286; }

/* ── Botão "Perguntar" (degradê índigo->teal) ── */
.stForm .stButton > button, div[data-testid="stFormSubmitButton"] > button {
    background:linear-gradient(135deg,#6B63E8,#0FA697); color:#fff; border:none; border-radius:12px;
    padding:16px 8px; font-size:1rem; font-weight:700; width:100%; min-height:56px;
    box-shadow:0 10px 24px -10px rgba(107,99,232,.6); transition:all .16s;
}
.stForm .stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    transform:translateY(-2px); box-shadow:0 14px 30px -10px rgba(107,99,232,.75); color:#fff;
}
/* rótulo de campo */
.campo-label { font-weight:700; font-size:1rem; color:#E7E9F2; margin:2px 0 10px; }

/* ── Cartão de resposta (escuro) ── */
.answer { margin-top:8px; background:#1E2230; border:1px solid #333A4D; border-radius:16px; overflow:hidden;
    box-shadow:0 20px 50px -30px rgba(0,0,0,.7); }
.answer-head { background:linear-gradient(135deg,rgba(107,99,232,.14),rgba(15,166,151,.14));
    padding:13px 22px; border-bottom:1px solid #262A38; font-family:'IBM Plex Mono',monospace;
    font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; color:#A9B4FF; font-weight:600; }
.answer-body { padding:22px 24px; font-size:1.05rem; line-height:1.7; color:#E7E9F2; }
.answer-src { padding:0 24px 20px; display:flex; gap:7px; flex-wrap:wrap; align-items:center; }
.srclabel { font-size:.82rem; color:#9198AC; font-weight:600; margin-right:4px; }
.tag { background:rgba(15,166,151,.16); color:#4FD6C4; border:1px solid rgba(15,166,151,.4);
    border-radius:99px; padding:4px 13px; font-size:.78rem; font-weight:600; }

/* ── Sidebar escura ── */
section[data-testid="stSidebar"] { background:#141620; border-right:1px solid #262A38; }

/* ── Expander (trechos) no escuro ── */
div[data-testid="stExpander"] { background:#1E2230; border:1px solid #333A4D; border-radius:12px; }
div[data-testid="stExpander"] summary { color:#C4C9E8 !important; }
div[data-testid="stExpander"] summary:hover { color:#A9B4FF !important; }
div[data-testid="stExpander"] p, div[data-testid="stExpander"] div,
div[data-testid="stExpander"] span, div[data-testid="stExpander"] label { color:#D2D6E4 !important; }
div[data-testid="stExpander"] strong { color:#EDEFF7 !important; }
/* Caption (trechos) mais legível */
div[data-testid="stCaptionContainer"], div[data-testid="stCaptionContainer"] p { color:#AEB4C6 !important; }
/* Texto geral da sidebar e do corpo mais claro */
section[data-testid="stSidebar"] * { color:#D2D6E4; }
section[data-testid="stSidebar"] strong { color:#EDEFF7; }
</style>
""", unsafe_allow_html=True)


# ─── Carregamento pesado, uma vez só ──────────────────────────────
@st.cache_resource(show_spinner="Preparando o assistente (primeira carga pode demorar)...")
def carregar_motor():
    import config
    if not (config.INDEX_DIR / "index.faiss").exists():
        from indexer import construir_indice
        construir_indice()
    return get_retriever(), get_llm()


# ─── Barra lateral (detalhes técnicos) ────────────────────────────
with st.sidebar:
    st.markdown("### Sobre o projeto")
    st.markdown(
        "Assistente **RAG** que responde sobre uma base de documentos "
        "citando a fonte, e que admite quando não sabe."
    )
    st.markdown("**Pipeline:**")
    st.markdown(
        "- Busca híbrida: FAISS (semântica) + BM25 (palavra-chave), fundidas por RRF\n"
        "- Geração fundamentada com LLM (Groq)\n"
        "- Citação de fontes e trechos visíveis"
    )
    st.markdown("**Base de conhecimento (10 artigos da Wikipedia):**")
    st.markdown(
        "1. Artificial intelligence\n"
        "2. Machine learning\n"
        "3. Deep learning\n"
        "4. Natural language processing\n"
        "5. Large language model\n"
        "6. Neural network (machine learning)\n"
        "7. Computer vision\n"
        "8. Reinforcement learning\n"
        "9. Transformer (deep learning architecture)\n"
        "10. Generative artificial intelligence"
    )
    st.divider()
    st.caption("Python · LangChain · FAISS · Groq")


# ─── Hero ─────────────────────────────────────────────────────────
st.markdown("""
<div class="hero"><div class="hero-in">
  <div class="badge"><span class="pulse"></span> Retrieval-Augmented Generation</div>
  <h1>Assistente <span class="g">RAG</span> para Documentos</h1>
  <p>Pergunte sobre Inteligência Artificial. As respostas se baseiam apenas nos documentos e sempre citam a fonte.</p>
  <div class="chips">
    <span class="chip">Busca híbrida</span><span class="chip">FAISS + BM25</span>
    <span class="chip">Groq LLM</span><span class="chip">Anti-alucinação</span>
  </div>
</div></div>
""", unsafe_allow_html=True)


# ─── Motor ────────────────────────────────────────────────────────
try:
    retriever, llm = carregar_motor()
except Exception as e:
    st.error("Não foi possível iniciar o assistente. Verifique a chave da API.\n\n" + str(e))
    st.stop()


# ─── Perguntas de exemplo (cards clicáveis) ───────────────────────
EXEMPLOS = [
    "🧠  O que é aprendizado por reforço?",
    "⚡  Como funciona a arquitetura Transformer?",
    "🔀  Qual a diferença entre IA e machine learning?",
    "🕸️  O que são redes neurais?",
]

if "pergunta_atual" not in st.session_state:
    st.session_state.pergunta_atual = ""

st.markdown('<div class="seclabel">Experimente uma pergunta</div>', unsafe_allow_html=True)
cols = st.columns(2)
for i, ex in enumerate(EXEMPLOS):
    if cols[i % 2].button(ex, key=f"ex_{i}", use_container_width=True):
        st.session_state.pergunta_atual = ex.split("  ", 1)[-1]

st.markdown('<div class="campo-label">💬 Faça sua pergunta</div>', unsafe_allow_html=True)
with st.form("form_pergunta", clear_on_submit=False):
    c1, c2 = st.columns([5, 1])
    texto = c1.text_input(
        "pergunta", value=st.session_state.pergunta_atual,
        placeholder="Ex.: O que é uma rede neural?  (ou clique num exemplo acima)",
        label_visibility="collapsed",
    )
    enviado = c2.form_submit_button("Perguntar →")

pergunta = texto if (enviado or texto) else ""


# ─── Resposta ─────────────────────────────────────────────────────
if pergunta:
    with st.spinner("Buscando nos documentos e gerando a resposta..."):
        resultado = responder(pergunta, retriever=retriever, llm=llm)

    tags = "".join(f'<span class="tag">{f}</span>' for f in resultado["fontes"])
    st.markdown(f"""
    <div class="answer">
      <div class="answer-head">✦ Resposta</div>
      <div class="answer-body">{resultado["resposta"]}</div>
      <div class="answer-src"><span class="srclabel">Fontes:</span>{tags}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 Ver os trechos que embasaram a resposta"):
        for i, doc in enumerate(resultado["trechos"], 1):
            titulo = doc.metadata.get("titulo", "?")
            st.markdown(f"**Trecho {i} — {titulo}**")
            st.caption(doc.page_content)
            if i < len(resultado["trechos"]):
                st.divider()