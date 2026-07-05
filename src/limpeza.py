"""
limpeza.py — Limpa o texto dos documentos antes do chunking.

Por que existe (a lição de "garbage in, garbage out"):
Os artigos da Wikipedia trazem fórmulas matemáticas em LaTeX que, ao serem
extraídas como texto puro, viram ruído — coisas como "{\\displaystyle O(N^{2})}"
ou símbolos soltos. Esse ruído polui os chunks, atrapalha a busca e aparece
feio na interface. Limpar a entrada melhora tudo o que vem depois.

A função limpar_texto() é aplicada a cada documento no loader.
"""

import re


def limpar_texto(texto: str) -> str:
    """Remove ruído de LaTeX e normaliza espaços, preservando o texto real."""

    # 1) Remove blocos {\displaystyle ...} — a marcação de fórmula da Wikipedia.
    #    O conteúdo entre chaves pode ter chaves aninhadas; removemos de forma
    #    iterativa até não haver mais ocorrências.
    padrao_displaystyle = re.compile(r"\{\\displaystyle[^{}]*\}")
    anterior = None
    while anterior != texto:
        anterior = texto
        texto = padrao_displaystyle.sub(" ", texto)

    # 2) Remove comandos LaTeX residuais como \frac, \sum, \mathbf, etc.
    texto = re.sub(r"\\[a-zA-Z]+", " ", texto)

    # 3) Remove chaves e cifrões soltos que sobram da notação.
    texto = texto.replace("{", " ").replace("}", " ").replace("$", " ")

    # 4) Remove linhas que sobraram só com fragmentos de fórmula
    #    (poucos caracteres, muitos símbolos/dígitos isolados).
    linhas_limpas = []
    for linha in texto.split("\n"):
        stripped = linha.strip()
        if not stripped:
            linhas_limpas.append("")
            continue
        # Conta letras de verdade na linha.
        letras = sum(c.isalpha() for c in stripped)
        # Se a linha é curta e quase não tem letras, é provável resíduo de fórmula.
        if len(stripped) <= 3 and letras <= 1:
            continue
        linhas_limpas.append(linha)
    texto = "\n".join(linhas_limpas)

    # 5) Normaliza espaços múltiplos e quebras de linha excessivas.
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


if __name__ == "__main__":
    # Teste: python src/limpeza.py
    sujo = """The standard attention graph scales as
O
(
    N
        2
)
{\\displaystyle O(N^{2})}
where
N
{\\displaystyle N}
is the number of tokens in a sequence. Reformer (2020) reduces the load."""

    print("ANTES:")
    print(sujo)
    print("\n" + "═" * 50 + "\n")
    print("DEPOIS:")
    print(limpar_texto(sujo))
