"""
config.py — Configuração centralizada do projeto.

Por que um arquivo só de config?
- Um único lugar para mudar caminhos, modelos e parâmetros.
- Carrega as variáveis do .env de forma segura (chaves nunca no código).
- Todos os outros módulos importam daqui, então ajustes ficam fáceis.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env (se existir) para o ambiente.
load_dotenv()

# ─── Caminhos do projeto ──────────────────────────────────────────
# BASE_DIR aponta para a raiz do projeto, independente de onde o script rodar.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "documentos"   # onde ficam os documentos
INDEX_DIR = BASE_DIR / "index"                # onde o índice vetorial é salvo

# ─── Parâmetros de chunking (Fase 1) ──────────────────────────────
# CHUNK_SIZE: tamanho de cada trecho em caracteres.
# CHUNK_OVERLAP: sobreposição entre trechos vizinhos, para não cortar
#   uma ideia no meio e perder contexto na fronteira.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# ─── Parâmetros de recuperação (Fase 3) ───────────────────────────
TOP_K = 4   # quantos trechos recuperar para embasar cada resposta

# ─── Modo de operação ─────────────────────────────────────────────
# "local" usa modelos grátis na sua máquina; "azure" usa os serviços Azure.
MODO = os.getenv("MODO", "local")

# ─── Modelo de embedding local (Fase 2) ───────────────────────────
# Modelo multilíngue leve e gratuito, roda na CPU. Bom para português.
EMBED_MODEL_LOCAL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ─── LLM: Groq (gratuito, para desenvolvimento — Fases 4/5) ───────
# API compatível com o padrão OpenAI, então o código fica quase igual
# ao do Azure. Chave lida do .env (nunca versionada).
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ─── Credenciais Azure (lidas do .env; só necessárias nas Fases 4/7) ─
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
AZURE_OPENAI_EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "rag-documentos")


def resumo():
    """Imprime um resumo da configuração atual — útil para conferir o setup."""
    print("─" * 50)
    print("Configuração do Assistente RAG")
    print("─" * 50)
    print(f"Modo............: {MODO}")
    print(f"Pasta de dados..: {DATA_DIR}")
    print(f"Pasta do índice.: {INDEX_DIR}")
    print(f"Chunk size......: {CHUNK_SIZE} (overlap {CHUNK_OVERLAP})")
    print(f"Top-K...........: {TOP_K}")
    print(f"Embedding local.: {EMBED_MODEL_LOCAL}")
    print("─" * 50)


if __name__ == "__main__":
    # Rode `python src/config.py` para verificar se está tudo certo.
    resumo()