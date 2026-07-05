"""
chunker.py — Fatia documentos em trechos (chunks) prontos para busca.

Por que fatiar (ver SPEC, seções 4 e 5):
- Um LLM não recebe um documento inteiro de uma vez; e mesmo que recebesse,
  seria caro e impreciso. Recuperamos só os TRECHOS relevantes de cada pergunta.

Como fatiamos bem (o que separa amador de sênior):
1. Corte que respeita a estrutura do texto: tentamos quebrar em parágrafos,
   depois frases, depois palavras — nunca no meio de uma palavra.
2. Sobreposição (overlap): cada chunk repete um pedaço do fim do anterior,
   para nenhuma ideia se perder na fronteira do corte.
3. Metadados: cada chunk sabe de qual documento e posição veio — é isso que
   permite CITAR a fonte na resposta (RF-05).

Usamos o RecursiveCharacterTextSplitter do LangChain, que implementa a
lógica de corte hierárquico descrita acima.
"""

import sys
from pathlib import Path
from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter

sys.path.append(str(Path(__file__).resolve().parent))
import config
from loader import Documento, carregar_documentos


@dataclass
class Chunk:
    """Um trecho de documento, com seu texto e metadados de citação."""
    texto: str
    metadados: dict = field(default_factory=dict)


# O splitter tenta cortar nesta ordem de separadores: primeiro em quebras de
# parágrafo, depois de linha, depois frase, depois espaço. Só corta "no meio"
# se não houver alternativa. É o "corte semântico" na prática.
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=config.CHUNK_SIZE,
    chunk_overlap=config.CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)


def fatiar_documento(doc: Documento) -> list[Chunk]:
    """Fatia um único documento em chunks, preservando os metadados de origem."""
    trechos = _splitter.split_text(doc.texto)
    chunks = []
    for i, trecho in enumerate(trechos):
        chunks.append(Chunk(
            texto=trecho,
            metadados={
                "arquivo": doc.arquivo,
                "titulo": doc.titulo,
                "fonte": doc.fonte,
                "posicao": i,                      # ordem do chunk no documento
                "chunk_id": f"{doc.arquivo}::{i}",  # identificador único
            },
        ))
    return chunks


def fatiar_todos(docs: list[Documento] = None) -> list[Chunk]:
    """Carrega (se preciso) e fatia todos os documentos da base."""
    docs = docs if docs is not None else carregar_documentos()
    todos = []
    for doc in docs:
        todos.extend(fatiar_documento(doc))
    return todos


if __name__ == "__main__":
    # Teste rápido: python src/chunker.py
    docs = carregar_documentos()
    chunks = fatiar_todos(docs)

    print(f"Documentos: {len(docs)}")
    print(f"Chunks gerados: {len(chunks)}")
    if docs:
        media = len(chunks) / len(docs)
        print(f"Média de chunks por documento: {media:.1f}\n")

    # Mostra um exemplo para você ver como fica um chunk.
    if chunks:
        exemplo = chunks[0]
        print("─" * 60)
        print("EXEMPLO DE CHUNK (o primeiro):")
        print("─" * 60)
        print("Metadados:", exemplo.metadados)
        print("\nTexto do chunk:")
        print(exemplo.texto[:400] + ("..." if len(exemplo.texto) > 400 else ""))
        print("─" * 60)
