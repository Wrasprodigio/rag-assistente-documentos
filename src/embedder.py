"""
embedder.py — Converte texto em vetores (embeddings).

O que é um embedding (ver SPEC, seção 4):
Um vetor de números que representa o SIGNIFICADO de um texto. Textos parecidos
geram vetores próximos; textos diferentes, vetores distantes. É isso que
permite buscar por significado, não por palavra exata.

Estratégia local → nuvem (decisão da spec):
- MODO "local": usa sentence-transformers, roda na sua máquina, grátis.
- MODO "azure": usa Azure OpenAI embeddings (implementado na Fase 7).
Escrevemos com uma função única `get_embedder()` para trocar sem reescrever
o resto do código.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
import config


def get_embedder():
    """
    Devolve o objeto de embeddings conforme o MODO configurado.
    O objeto segue a interface do LangChain (métodos embed_documents e
    embed_query), então o resto do pipeline não precisa saber qual é.
    """
    if config.MODO == "azure":
        # Implementado na Fase 7. Requer credenciais no .env.
        from langchain_openai import AzureOpenAIEmbeddings
        return AzureOpenAIEmbeddings(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version=config.AZURE_OPENAI_API_VERSION,
            azure_deployment=config.AZURE_OPENAI_EMBED_DEPLOYMENT,
        )

    # MODO local (padrão): modelo multilíngue leve, roda na CPU.
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=config.EMBED_MODEL_LOCAL,
        encode_kwargs={"normalize_embeddings": True},  # ajuda na busca por similaridade
    )


if __name__ == "__main__":
    # Teste rápido: python src/embedder.py
    # Mostra que dois textos parecidos geram vetores próximos, e um texto
    # diferente gera um vetor distante.
    import numpy as np

    print("Carregando modelo de embedding (pode demorar na 1ª vez)...")
    emb = get_embedder()

    textos = [
        "Aprendizado de máquina usa dados para treinar modelos.",
        "Machine learning treina modelos a partir de dados.",   # parecido com o 1º
        "A receita de bolo leva farinha, ovos e açúcar.",       # diferente
    ]
    vetores = emb.embed_documents(textos)
    v = np.array(vetores)

    def similaridade(a, b):
        # Cosseno entre dois vetores (1 = idêntico, 0 = sem relação).
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    print(f"\nDimensões de cada vetor: {v.shape[1]}")
    print(f"Similaridade (frase 1 vs 2, parecidas): {similaridade(v[0], v[1]):.3f}")
    print(f"Similaridade (frase 1 vs 3, diferentes): {similaridade(v[0], v[2]):.3f}")
    print("\nEsperado: o 1º número (parecidas) bem maior que o 2º (diferentes).")
