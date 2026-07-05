"""
loader.py — Lê os documentos da pasta e extrai metadados de origem.

Responsabilidade (ver SPEC, seção 5): pegar cada arquivo em data/documentos
e devolver seu texto + informações de origem (nome, título, URL da fonte).
Esses metadados são o que permite CITAR a fonte depois (RF-05 da spec).

Suporta .txt (nossos artigos da Wikipedia) e .pdf (para uso futuro).
"""

import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.append(str(Path(__file__).resolve().parent))
import config
from limpeza import limpar_texto


@dataclass
class Documento:
    """Um documento carregado, com seu texto e metadados de origem."""
    texto: str
    arquivo: str      # nome do arquivo, ex: "Machine_learning.txt"
    titulo: str       # título do artigo, ex: "Machine learning"
    fonte: str        # URL de origem, ex: "https://en.wikipedia.org/..."


def _extrair_cabecalho(conteudo: str):
    """
    Nossos .txt da Wikipedia começam com duas linhas:
        Título: ...
        Fonte: ...
        <linha em branco>
        <texto do artigo>
    Esta função separa esses metadados do corpo do texto.
    """
    titulo, fonte, corpo = "", "", conteudo
    linhas = conteudo.split("\n")
    if len(linhas) >= 2 and linhas[0].startswith("Título:"):
        titulo = linhas[0].replace("Título:", "").strip()
        fonte = linhas[1].replace("Fonte:", "").strip()
        # o corpo começa após a linha em branco que separa cabeçalho do texto
        corpo = "\n".join(linhas[3:]) if len(linhas) > 3 else ""
    return titulo, fonte, corpo


def _ler_txt(caminho: Path) -> Documento:
    conteudo = caminho.read_text(encoding="utf-8")
    titulo, fonte, corpo = _extrair_cabecalho(conteudo)
    # Limpa o ruído de LaTeX/fórmulas antes de qualquer processamento.
    corpo = limpar_texto(corpo)
    # Se não houver cabeçalho, usa o nome do arquivo como título.
    return Documento(
        texto=corpo.strip(),
        arquivo=caminho.name,
        titulo=titulo or caminho.stem,
        fonte=fonte or caminho.name,
    )


def _ler_pdf(caminho: Path) -> Documento:
    # Import local: só carrega o pypdf se realmente houver PDF.
    from pypdf import PdfReader
    reader = PdfReader(str(caminho))
    texto = "\n".join((pagina.extract_text() or "") for pagina in reader.pages)
    texto = limpar_texto(texto)
    return Documento(
        texto=texto.strip(),
        arquivo=caminho.name,
        titulo=caminho.stem,
        fonte=caminho.name,
    )


def carregar_documentos(pasta: Path = None) -> list[Documento]:
    """
    Lê todos os .txt e .pdf da pasta e devolve uma lista de Documentos.
    """
    pasta = pasta or config.DATA_DIR
    documentos = []
    # sorted() garante ordem previsível (bom para reprodutibilidade).
    for caminho in sorted(pasta.iterdir()):
        if caminho.suffix.lower() == ".txt":
            documentos.append(_ler_txt(caminho))
        elif caminho.suffix.lower() == ".pdf":
            documentos.append(_ler_pdf(caminho))
        # outros tipos de arquivo são ignorados
    return documentos


if __name__ == "__main__":
    # Teste rápido: python src/loader.py
    docs = carregar_documentos()
    print(f"Documentos carregados: {len(docs)}\n")
    for d in docs:
        print(f"  • {d.titulo}")
        print(f"    arquivo: {d.arquivo} | {len(d.texto):,} caracteres")
        print(f"    fonte:   {d.fonte}")