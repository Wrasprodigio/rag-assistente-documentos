"""
baixar_documentos.py — Monta a base pública de documentos.

O que faz: baixa uma lista de artigos da Wikipedia sobre Inteligência
Artificial e salva cada um como um arquivo .txt na pasta data/documentos.

Por que Wikipedia: conteúdo público (licença livre), rico e variado —
e tem um charme no portfólio: um assistente de IA que responde sobre IA.

Robustez: a API da Wikipedia às vezes recusa requisições muito rápidas em
sequência (rate limiting). Por isso o script (1) faz uma pausa entre cada
download e (2) tenta de novo automaticamente quando um artigo falha.

Rode uma vez:  python src/baixar_documentos.py
"""

import sys
import time
from pathlib import Path

import wikipedia

# Permite importar o config mesmo rodando de dentro de src/
sys.path.append(str(Path(__file__).resolve().parent))
import config

# Artigos que formam nossa base. Variados de propósito: conceitos,
# técnicas e história — dá boas perguntas para testar o assistente.
ARTIGOS = [
    "Artificial intelligence",
    "Machine learning",
    "Deep learning",
    "Natural language processing",
    "Large language model",
    "Neural network (machine learning)",
    "Computer vision",
    "Reinforcement learning",
    "Transformer (deep learning architecture)",
    "Generative artificial intelligence",
]

# Quantas vezes tentar cada artigo antes de desistir, e quanto esperar.
MAX_TENTATIVAS = 4
PAUSA_ENTRE_ARTIGOS = 1.5   # segundos entre um artigo e outro
PAUSA_APOS_FALHA = 3.0      # segundos de espera antes de tentar de novo


def baixar_um(titulo):
    """Baixa um artigo, com novas tentativas em caso de falha temporária."""
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            # auto_suggest=False evita que o título seja "corrigido" para outro artigo.
            pagina = wikipedia.page(titulo, auto_suggest=False)
            nome = titulo.replace(" ", "_").replace("/", "-") + ".txt"
            destino = config.DATA_DIR / nome
            # Guardamos título e URL no topo — viram metadados de citação depois.
            conteudo = f"Título: {pagina.title}\nFonte: {pagina.url}\n\n{pagina.content}"
            destino.write_text(conteudo, encoding="utf-8")
            return True, len(pagina.content)
        except Exception as e:
            # Se ainda há tentativas, espera e tenta de novo.
            if tentativa < MAX_TENTATIVAS:
                time.sleep(PAUSA_APOS_FALHA)
            else:
                return False, str(e)


def baixar():
    wikipedia.set_lang("en")
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Baixando {len(ARTIGOS)} artigos para {config.DATA_DIR}\n")
    ok = 0
    for titulo in ARTIGOS:
        sucesso, info = baixar_um(titulo)
        if sucesso:
            print(f"  \u2713 {titulo}  ({info:,} caracteres)")
            ok += 1
        else:
            print(f"  \u2717 {titulo}  \u2014 erro: {info}")
        time.sleep(PAUSA_ENTRE_ARTIGOS)  # pausa educada entre downloads

    print(f"\nConcluído: {ok}/{len(ARTIGOS)} artigos salvos em data/documentos/")
    if ok < len(ARTIGOS):
        print("Dica: rode o script de novo \u2014 os que faltaram costumam vir na 2\u00aa rodada.")


if __name__ == "__main__":
    baixar()