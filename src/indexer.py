"""
indexer.py — Cria e salva o índice vetorial (FAISS) a partir dos chunks.

O que faz (ver SPEC, seções 4 e 5):
1. Carrega os documentos e os fatia em chunks (Fases 1).
2. Gera o embedding de cada chunk (Fase 2).
3. Guarda tudo num índice FAISS, que permite busca por similaridade rápida.
4. Salva o índice em disco (pasta index/) para reuso — você calcula os
   embeddings UMA vez e reutiliza em todas as consultas.

FAISS é a biblioteca da Meta para busca vetorial eficiente. Guardamos junto
os metadados de cada chunk, para conseguir CITAR a fonte depois.

Rode:  python src/indexer.py
"""

import sys
import time
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LCDocument

sys.path.append(str(Path(__file__).resolve().parent))
import config
from chunker import fatiar_todos
from embedder import get_embedder


def construir_indice():
    """Constrói o índice FAISS a partir de toda a base e salva em disco."""
    print("1/4 · Carregando e fatiando documentos...")
    chunks = fatiar_todos()
    print(f"      {len(chunks)} chunks prontos.")

    # O FAISS do LangChain trabalha com objetos Document (texto + metadados).
    # Convertemos nossos Chunks para esse formato.
    docs_lc = [
        LCDocument(page_content=c.texto, metadata=c.metadados)
        for c in chunks
    ]

    print("2/4 · Carregando modelo de embedding (demora na 1ª vez)...")
    embedder = get_embedder()

    print("3/4 · Gerando embeddings e construindo o índice FAISS...")
    print("      (esta é a etapa mais demorada — aguarde)")
    inicio = time.time()
    # FAISS.from_documents gera o embedding de cada chunk e monta o índice.
    indice = FAISS.from_documents(docs_lc, embedder)
    dur = time.time() - inicio
    print(f"      Índice construído em {dur:.1f}s.")

    print("4/4 · Salvando o índice em disco...")
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    indice.save_local(str(config.INDEX_DIR))
    print(f"      Índice salvo em: {config.INDEX_DIR}")

    print("\n✓ Indexação concluída. A base está pronta para busca.")
    return indice


if __name__ == "__main__":
    construir_indice()
