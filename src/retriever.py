"""
retriever.py — Recupera os trechos mais relevantes para uma pergunta.

A decisão central desta fase (ver SPEC, seção 4): BUSCA HÍBRIDA.

Por que híbrida?
- Busca vetorial (semântica): entende o SIGNIFICADO da pergunta. Ótima para
  perguntas conceituais, mesmo quando as palavras não batem exatamente.
  Ponto fraco: às vezes erra em siglas, nomes próprios e termos exatos.
- Busca BM25 (palavra-chave): a clássica busca por termos exatos. Ótima para
  siglas ("BERT", "GPT"), nomes e números. Ponto fraco: não entende sinônimos.

Como combinamos: Reciprocal Rank Fusion (RRF).
Cada busca produz um ranking. O RRF dá a cada documento uma pontuação
1 / (k + posição) em cada lista e soma. Documentos bem colocados nas DUAS
listas sobem para o topo. É o mesmo método que o Azure AI Search usa para
busca híbrida — e implementá-lo aqui deixa claro o que acontece por baixo,
em vez de depender de uma caixa-preta.

Uso:
    from retriever import get_retriever
    retriever = get_retriever()
    docs = retriever.invoke("o que é aprendizado por reforço?")
"""

import sys
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document as LCDocument

sys.path.append(str(Path(__file__).resolve().parent))
import config
from chunker import fatiar_todos
from embedder import get_embedder


def _carregar_indice_vetorial():
    """Carrega o índice FAISS salvo em disco (criado pelo indexer.py)."""
    if not (config.INDEX_DIR / "index.faiss").exists():
        raise FileNotFoundError(
            "Índice não encontrado. Rode primeiro:  python src/indexer.py"
        )
    embedder = get_embedder()
    return FAISS.load_local(
        str(config.INDEX_DIR),
        embedder,
        allow_dangerous_deserialization=True,  # confiamos no índice que nós mesmos geramos
    )


def _reciprocal_rank_fusion(listas, k: int = 60):
    """
    Funde várias listas ranqueadas de documentos usando RRF.

    listas: lista de listas de Documentos (uma por buscador), cada uma já
            ordenada do mais para o menos relevante.
    k:      constante de amortecimento (60 é o valor clássico da literatura).

    Retorna uma única lista ordenada pela pontuação RRF combinada.
    """
    pontuacao = {}   # chave do documento -> pontuação acumulada
    guarda = {}      # chave do documento -> o próprio Documento

    for lista in listas:
        for posicao, doc in enumerate(lista):
            # Usamos o chunk_id como identidade; se faltar, caímos no texto.
            chave = doc.metadata.get("chunk_id", doc.page_content[:80])
            pontuacao[chave] = pontuacao.get(chave, 0.0) + 1.0 / (k + posicao)
            guarda[chave] = doc

    # Ordena as chaves da maior para a menor pontuação.
    ordenadas = sorted(pontuacao, key=pontuacao.get, reverse=True)
    return [guarda[chave] for chave in ordenadas]


class RetrieverHibrido:
    """Combina busca vetorial (FAISS) e por palavra-chave (BM25) via RRF."""

    def __init__(self, top_k: int):
        self.top_k = top_k
        # 1) Busca vetorial a partir do índice FAISS já construído.
        faiss = _carregar_indice_vetorial()
        # Recuperamos um pouco mais de cada busca (top_k*2) antes de fundir,
        # para dar material à fusão; no fim cortamos em top_k.
        self._vetorial = faiss.as_retriever(search_kwargs={"k": top_k * 2})

        # 2) Busca por palavra-chave (BM25) sobre os textos em memória.
        chunks = fatiar_todos()
        docs_lc = [LCDocument(page_content=c.texto, metadata=c.metadados) for c in chunks]
        self._bm25 = BM25Retriever.from_documents(docs_lc)
        self._bm25.k = top_k * 2

    def invoke(self, pergunta: str):
        """Recebe a pergunta, roda as duas buscas e devolve os top_k fundidos."""
        res_vetorial = self._vetorial.invoke(pergunta)
        res_bm25 = self._bm25.invoke(pergunta)
        fundidos = _reciprocal_rank_fusion([res_vetorial, res_bm25])
        return fundidos[: self.top_k]


def get_retriever(top_k: int = None) -> RetrieverHibrido:
    """Monta o retriever híbrido. top_k padrão vem do config."""
    return RetrieverHibrido(top_k or config.TOP_K)


if __name__ == "__main__":
    # Teste: python src/retriever.py
    print("Montando retriever híbrido (vetorial + BM25, fusão RRF)...")
    retriever = get_retriever()
    print("Pronto.\n")

    perguntas_exemplo = [
        "o que é rede neural?",
        "como funciona um llm?",
    ]
    for pergunta in perguntas_exemplo:
        print("=" * 64)
        print(f"PERGUNTA: {pergunta}")
        print("=" * 64)
        docs = retriever.invoke(pergunta)
        for i, d in enumerate(docs, 1):
            titulo = d.metadata.get("titulo", "?")
            trecho = d.page_content[:180].replace("\n", " ")
            print(f"\n[{i}] Fonte: {titulo}")
            print(f"    {trecho}...")
        print()