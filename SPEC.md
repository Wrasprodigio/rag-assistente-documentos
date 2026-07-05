# Especificação Técnica — Assistente RAG para Documentos

> **Spec-Driven Development (SDD)** · Documento vivo · v1.0
> Este documento define **o quê** e **o porquê** antes do **como**. Nenhuma linha de código é escrita sem que a etapa correspondente esteja especificada aqui. Ele mora na raiz do repositório e é atualizado conforme o projeto evolui.

---

## 1. Visão geral

**Problema.** Encontrar uma informação específica dentro de uma base grande de documentos (PDFs, manuais, políticas) é lento e sujeito a erro. A busca por palavra-chave falha quando o usuário não usa os termos exatos do texto.

**Solução.** Um assistente que responde perguntas em linguagem natural sobre uma base de documentos, **sempre citando o trecho e o documento de origem** — para que a resposta seja verificável, não uma "alucinação".

**Por que RAG (Retrieval-Augmented Generation).** Em vez de confiar só no que o modelo "sabe", nós *recuperamos* os trechos relevantes da base e os entregamos ao LLM como contexto. Isso reduz alucinação, permite citar fontes e funciona com documentos que o modelo nunca viu.

**Público-alvo da demo.** Recrutadores técnicos e a comunidade — o projeto é vitrine de portfólio, então clareza e documentação valem tanto quanto o código.

---

## 2. Escopo

### Dentro do escopo (v1)
- Ingestão de documentos em PDF e TXT a partir de uma pasta local.
- Chunking (fatiamento) semântico do texto.
- Geração de embeddings e indexação em banco vetorial.
- Busca híbrida (vetorial + palavra-chave) sobre a base.
- Geração de resposta com LLM, **com citação da fonte**.
- Interface web simples (Streamlit) para fazer perguntas.
- Avaliação de qualidade das respostas (conjunto de perguntas-teste).

### Fora do escopo (v1 — candidatos a v2)
- Autenticação de usuários / multiusuário.
- Upload de documentos pela interface (v1 usa pasta local).
- Suporte a imagens dentro dos PDFs (OCR).
- Conversação multi-turno com memória (v1 é pergunta→resposta).
- Deploy em produção com alta disponibilidade.

> Definir o que **não** entra é tão importante quanto o que entra. Evita o projeto inchar e nunca terminar.

---

## 3. Requisitos

### Funcionais (o que o sistema faz)
| ID | Requisito |
|----|-----------|
| RF-01 | O sistema ingere todos os PDFs/TXTs de uma pasta configurável. |
| RF-02 | O sistema fatia cada documento em trechos (chunks) com sobreposição. |
| RF-03 | O sistema gera embeddings de cada chunk e os indexa. |
| RF-04 | O usuário faz uma pergunta em português e recebe uma resposta. |
| RF-05 | Toda resposta cita o(s) documento(s) e trecho(s) de origem. |
| RF-06 | Se a base não contém a resposta, o sistema diz isso — não inventa. |
| RF-07 | A interface permite ver os trechos recuperados que embasaram a resposta. |

### Não-funcionais (como o sistema se comporta)
| ID | Requisito |
|----|-----------|
| RNF-01 | Latência-alvo: resposta em até ~8 segundos por pergunta. |
| RNF-02 | Custo controlado: usar modelos de custo/benefício (ex.: gpt-4o-mini). |
| RNF-03 | Nenhum dado sensível ou chave de API versionado no Git. |
| RNF-04 | Código modular, testável, com README que permite rodar sem ajuda. |
| RNF-05 | Reprodutível: `requirements.txt` + `.env.example` + instruções. |

---

## 4. Arquitetura

Duas fases distintas — **indexação** (offline, roda uma vez) e **consulta** (online, a cada pergunta):

```
┌─────────────────── FASE 1: INDEXAÇÃO (offline) ───────────────────┐
│                                                                    │
│   Documentos ──▶ Loader ──▶ Chunking ──▶ Embeddings ──▶ Índice     │
│   (PDF/TXT)                 (trechos)    (vetores)     (vector DB)  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌─────────────────── FASE 2: CONSULTA (online) ─────────────────────┐
│                                                                    │
│   Pergunta ──▶ Busca híbrida ──▶ Trechos ──▶ LLM ──▶ Resposta      │
│               (no índice)       relevantes  (+prompt)  + citações   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Decisão de arquitetura — banco vetorial em duas versões:**
- **Local (dev):** FAISS ou ChromaDB — grátis, roda na sua máquina, ideal para desenvolver e testar.
- **Nuvem (produção/demo):** Azure AI Search — mostra domínio do ecossistema Azure no portfólio.

O código será escrito com uma **camada de abstração** para trocar um pelo outro sem reescrever a lógica. Começamos local (rápido e grátis), migramos para Azure ao final.

---

## 5. Especificação de componentes

| Componente | Responsabilidade | Entrada | Saída |
|------------|------------------|---------|-------|
| `loader` | Ler arquivos da pasta | caminho da pasta | texto bruto + metadados |
| `chunker` | Fatiar texto em trechos | texto | lista de chunks |
| `embedder` | Vetorizar chunks | chunks | vetores | (converte texto em vetor)
| `indexer` | Armazenar no banco vetorial | vetores + metadados | índice persistido |  (cria e salva o índice FAISS)
| `retriever` | Buscar trechos relevantes | pergunta | top-k trechos |
| `generator` | Montar prompt + chamar LLM | pergunta + trechos | resposta + citações |
| `app` | Interface web | interação do usuário | tela |
| `evaluator` | Medir qualidade | perguntas-teste | métricas |

Cada componente é um módulo Python isolado, testável de forma independente.

---

## 6. Dados

**Fonte para a demo.** Base de documentos **públicos** — sugestões: manuais técnicos abertos, documentação pública, artigos, ou um conjunto do Kaggle. **Nunca** dados internos ou sigilosos.

**Formato dos metadados por chunk:**
```json
{
  "chunk_id": "doc3_p12_c04",
  "texto": "conteúdo do trecho...",
  "documento": "manual_seguranca.pdf",
  "pagina": 12,
  "posicao": 4
}
```
Os metadados são o que permite a **citação** — sem `documento` e `pagina`, não há como referenciar a fonte.

---

## 7. Estratégia de avaliação

O que diferencia um projeto sênior: **medir**, não só construir.

- **Conjunto-teste:** 15–20 perguntas com resposta conhecida, escritas por nós a partir da base.
- **Métricas:**
  - *Precisão de recuperação* — o trecho certo apareceu entre os top-k? (mede o retriever)
  - *Fidelidade* — a resposta se apoia nos trechos, sem inventar? (mede o generator)
  - *Taxa de citação correta* — a fonte citada é a real?
  - *Latência média* e *custo médio* por pergunta.
- **Ferramenta:** avaliação manual estruturada na v1; opcional RAGAS na v2.

---

## 8. Estrutura do repositório

```
rag-assistente-documentos/
├── README.md                 # vitrine: problema, arquitetura, resultados, como rodar
├── SPEC.md                   # este documento
├── requirements.txt
├── .env.example              # nomes das variáveis, SEM valores
├── .gitignore
├── data/
│   └── documentos/           # PDFs de exemplo (públicos)
├── src/
│   ├── config.py             # configurações centralizadas
│   ├── loader.py
│   ├── chunker.py
│   ├── embedder.py
│   ├── indexer.py
│   ├── retriever.py
│   ├── generator.py
│   └── pipeline.py           # orquestra tudo
├── app.py                    # interface Streamlit
├── evaluation/
│   ├── perguntas_teste.json
│   └── avaliar.py
├── notebooks/
│   └── exploracao.ipynb      # experimentos
└── tests/
    └── test_chunker.py       # testes básicos
```

---

## 9. Roadmap — etapa por etapa

Cada fase é entregável e testável antes de seguir para a próxima. **Não pulamos etapas.**

| Fase | Objetivo | Entregável | O que você aprende |
|------|----------|------------|--------------------|
| **0** | Preparar ambiente | Repo criado, venv, dependências, chaves | Setup profissional de projeto |
| **1** | Ingestão + chunking | Documentos lidos e fatiados corretamente | Loaders, estratégias de chunking |
| **2** | Embeddings + índice local | Base indexada em FAISS/Chroma | Embeddings, banco vetorial |
| **3** | Retriever + busca híbrida | Trechos relevantes recuperados | Busca vetorial e híbrida |
| **4** | Generator + citações | Respostas com fonte citada | Prompt engineering, grounding |
| **5** | Interface Streamlit | Demo clicável funcionando | App de IA end-to-end |
| **6** | Avaliação | Métricas medidas e documentadas | Rigor de avaliação (nível sênior) |
| **7** | Migração para Azure | Índice no Azure AI Search + deploy | Ecossistema Azure em produção |
| **8** | Documentação final | README completo com diagramas e resultados | Comunicação técnica |

---

## 10. Riscos e mitigações

| Risco | Mitigação |
|-------|-----------|
| Custo de API surpreender | Começar local (grátis); usar modelo mini; medir custo desde a fase 4 |
| Chunking ruim degrada tudo | Testar 2–3 estratégias na fase 1 antes de seguir |
| Vazar chave de API no Git | `.gitignore` + `.env.example` configurados na fase 0 |
| Projeto não terminar | Escopo v1 enxuto; cada fase é entregável isolado |

---

## 11. Definição de "pronto" (v1)

O projeto v1 está completo quando:
- [ ] Um usuário roda `streamlit run app.py`, faz uma pergunta e recebe resposta com citação.
- [ ] O índice está no Azure AI Search.
- [ ] Existe avaliação com métricas documentadas no README.
- [ ] Qualquer pessoa consegue rodar seguindo só o README.
- [ ] Nenhum segredo está versionado.
- [ ] A demo está no ar (Streamlit Cloud / Azure).
