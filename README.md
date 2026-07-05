# 🔎 Assistente RAG para Documentos

> Assistente de perguntas e respostas sobre uma base de documentos, com **busca híbrida**, **citação de fontes** e **combate à alucinação**. Construído com Python, LangChain, FAISS e Groq.

**🌐 Demo ao vivo:** [rag-assistente-documentos.streamlit.app](https://rag-assistente-documentos.streamlit.app)

<!-- EDITE: substitua pelo caminho de um print/GIF da sua interface, ex: docs/demo.png -->
<img width="1197" height="629" alt="Screenshot 2026-07-05 110824" src="https://github.com/user-attachments/assets/2e7140de-e045-45a3-b417-c905967aa89f" />


---

## 📌 O problema

Encontrar uma informação específica dentro de uma base grande de documentos é lento e sujeito a erro. A busca por palavra-chave tradicional falha quando o usuário não usa os termos exatos do texto — e modelos de linguagem, sozinhos, "alucinam": inventam respostas que parecem plausíveis mas são falsas.

## 💡 A solução

Um assistente baseado em **RAG (Retrieval-Augmented Generation)**: em vez de confiar só no conhecimento interno do modelo, o sistema **recupera** os trechos relevantes da base de documentos e os entrega ao LLM como contexto. Isso permite respostas **fundamentadas**, com **citação da fonte** e a capacidade de **admitir quando a informação não está na base** — em vez de inventar.

A base de conhecimento da demo são **10 artigos da Wikipedia sobre Inteligência Artificial** (conteúdo público) — ou seja, um assistente de IA que responde sobre IA.

## 🏗️ Arquitetura

O sistema tem duas fases: **indexação** (offline, roda uma vez) e **consulta** (online, a cada pergunta).

```
FASE 1 — INDEXAÇÃO (offline)
  Documentos → Limpeza → Chunking → Embeddings → Índice vetorial (FAISS)

FASE 2 — CONSULTA (online)
  Pergunta → Busca híbrida (FAISS + BM25 via RRF) → Trechos → LLM → Resposta + citações
```

<!-- EDITE: opcional — adicione um diagrama visual em docs/arquitetura.png (ferramenta grátis: draw.io ou Excalidraw) -->

## ✨ Destaques técnicos

- **Busca híbrida com Reciprocal Rank Fusion (RRF):** combina busca semântica (FAISS, por significado) e busca por palavra-chave (BM25, por termos exatos). A fusão RRF foi **implementada do zero** — o mesmo algoritmo usado pelo Azure AI Search.
- **Embeddings multilíngues:** o modelo permite perguntar em português e recuperar conteúdo em inglês, casando significados entre idiomas.
- **Combate à alucinação:** o prompt instrui o modelo a responder apenas com base nos trechos recuperados e a dizer explicitamente quando não sabe.
- **Citação de fontes e transparência:** toda resposta indica de qual documento veio, e o usuário pode inspecionar os trechos exatos que a embasaram.
- **Limpeza de dados:** etapa dedicada que remove ruído de fórmulas LaTeX extraídas da Wikipedia, melhorando a qualidade da recuperação.
- **Arquitetura preparada para nuvem:** abstração que permite alternar entre modelos locais (grátis) e serviços Azure sem reescrever a lógica.

## 🧰 Stack

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.12 |
| Orquestração RAG | LangChain |
| Busca vetorial | FAISS |
| Busca por palavra-chave | BM25 (rank-bm25) |
| Embeddings | Sentence Transformers (multilíngue) |
| LLM | Groq (Llama 3.3 70B) |
| Interface | Streamlit |
| Deploy | Streamlit Community Cloud |

## 🚀 Como rodar localmente

```bash
# 1. Clone o repositório
git clone https://github.com/Wrasprodigio/rag-assistente-documentos.git
cd rag-assistente-documentos

# 2. Crie o ambiente virtual (Python 3.12)
py -3.12 -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure a chave de API
copy .env.example .env         # Windows  (cp no macOS/Linux)
# edite o .env e adicione sua chave do Groq:
#   GROQ_API_KEY=sua_chave_aqui

# 5. Baixe a base de documentos
python src/baixar_documentos.py

# 6. Construa o índice vetorial
python src/indexer.py

# 7. Rode a interface
streamlit run app.py
```

> A chave gratuita do Groq pode ser criada em [console.groq.com/keys](https://console.groq.com/keys).

## 📁 Estrutura do projeto

```
rag-assistente-documentos/
├── app.py                  # interface web (Streamlit)
├── requirements.txt        # dependências
├── runtime.txt             # versão do Python para o deploy
├── SPEC.md                 # especificação técnica (Spec-Driven Development)
├── .streamlit/
│   └── config.toml         # tema visual
├── data/documentos/        # base de documentos (.txt)
└── src/
    ├── config.py           # configuração centralizada
    ├── baixar_documentos.py# baixa os artigos da Wikipedia
    ├── loader.py           # leitura + limpeza de documentos
    ├── limpeza.py          # remoção de ruído (LaTeX/fórmulas)
    ├── chunker.py          # fatiamento em trechos
    ├── embedder.py         # geração de embeddings
    ├── indexer.py          # construção do índice FAISS
    ├── retriever.py        # busca híbrida (FAISS + BM25 + RRF)
    └── generator.py        # montagem do prompt + chamada ao LLM
```

## 🗺️ Próximos passos

- [ ] Avaliação quantitativa: métricas de precisão de recuperação e fidelidade das respostas
- [ ] Migração para Azure OpenAI + Azure AI Search (versão de produção)
- [ ] Suporte a upload de documentos pela interface
- [ ] Conversação multi-turno com memória

## 🔒 Nota sobre dados

Este projeto usa exclusivamente **dados públicos** (artigos da Wikipedia sob licença livre). Nenhuma chave de API ou dado sensível é versionado no repositório.

---

<!-- EDITE: seus links reais -->
Desenvolvido por **Willyam Rodrigo** · [Portfólio](https://seu-usuario.github.io) · [LinkedIn](https://www.linkedin.com/in/willyam-rodrigo/)
