"""
limpeza.py — Limpa o texto dos documentos antes do chunking.

Por que existe (a lição de "garbage in, garbage out"):
Os artigos da Wikipedia trazem fórmulas matemáticas em LaTeX que, ao serem
extraídas como texto puro, viram ruído — "{\\displaystyle O(N^{2})}", símbolos
soltos, e fórmulas quebradas em muitas linhas de uma palavra só ("Concat",
"heads", "W^ K"). Esse ruído polui os chunks, atrapalha a busca e aparece feio
na interface. Limpar a entrada melhora tudo o que vem depois.

A função limpar_texto() é aplicada a cada documento no loader.
"""

import re


def limpar_texto(texto: str) -> str:
    """Remove ruído de LaTeX/fórmulas e normaliza espaços, preservando o texto real."""

    # 1) Remove blocos {\displaystyle ...}, mesmo com aspas/apóstrofos/chaves
    #    aninhadas dentro. Aplicamos de forma iterativa até esgotar.
    padrao_disp = re.compile(r"\{\\displaystyle[^{}]*\}")
    anterior = None
    while anterior != texto:
        anterior = texto
        texto = padrao_disp.sub(" ", texto)

    # 2) Remove QUALQUER bloco entre chaves que contenha uma barra invertida
    #    (é marcação LaTeX residual), também iterativamente.
    padrao_latex = re.compile(r"\{[^{}]*\\[^{}]*\}")
    anterior = None
    while anterior != texto:
        anterior = texto
        texto = padrao_latex.sub(" ", texto)

    # 3) Remove comandos LaTeX soltos (\frac, \sum, \mathbf, \displaystyle...).
    texto = re.sub(r"\\[a-zA-Z]+", " ", texto)

    # 4) Remove chaves e cifrões que sobraram da notação.
    texto = texto.replace("{", " ").replace("}", " ").replace("$", " ")

    # 5) Filtra linhas que são resíduo de fórmula. Processa linha a linha.
    linhas_limpas = []
    for linha in texto.split("\n"):
        stripped = linha.strip()
        if not stripped:
            linhas_limpas.append("")
            continue

        # Normaliza marcação de subtítulo: "==== Título ====" -> "Título".
        m = re.match(r"^=+\s*(.+?)\s*=+$", stripped)
        if m:
            stripped = m.group(1).strip()
            linha = stripped

        letras = sum(c.isalpha() for c in stripped)

        # (a) Linha sem NENHUMA letra (ex.: "=", ")", símbolos soltos) -> descarta.
        if letras == 0:
            continue

        # (b) Linha com "^" é resíduo de fórmula (superscript). Em texto normal
        #     o circunflexo não aparece; então descartamos a linha inteira.
        if "^" in stripped:
            continue

        tem_pontuacao_frase = any(p in stripped for p in [". ", ", ", "; ", ": "]) or stripped.endswith(".")
        simbolos_mat = sum(c in "_=|()[]\\+*/<>" for c in stripped)

        # (c) Linha curta e sem pontuação de frase -> provável fragmento de fórmula.
        if len(stripped) <= 25 and not tem_pontuacao_frase:
            # mantém só se for texto limpo de verdade (várias letras, sem símbolos)
            if letras >= len(stripped) * 0.7 and simbolos_mat == 0 and " " in stripped:
                linhas_limpas.append(linha)
            continue

        # (d) Linha com alta densidade de símbolos matemáticos -> descarta.
        if simbolos_mat >= 4 and simbolos_mat > letras * 0.3:
            continue

        linhas_limpas.append(linha)

    texto = "\n".join(linhas_limpas)

    # 6) Normaliza espaços e quebras de linha excessivas.
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


if __name__ == "__main__":
    # Teste com os casos REAIS dos prints do usuário.
    casos = [
        # Caso exato do print mais recente (Transformer / Multi-Query Attention)
        """==== Multi-Query Attention ====
Multi-Query Attention changes the Multihead Attention mechanism. Whereas normally,
=
with Multi-Query Attention, there is just one
, thus:
=
MultiQueryAttention (Q,K,V)= Concat _ i [n_ heads ] ( Attention (XW_ i ^ Q ,XW^ K ,XW^ V ) )W^ O
This has a neutral effect on model quality and training speed, but increases inference speed. More generally, grouped-query attention (GQA) partitions attention heads into groups.""",
    ]
    for i, c in enumerate(casos, 1):
        print(f"═══ CASO {i} — DEPOIS DA LIMPEZA ═══")
        print(limpar_texto(c))
        print()