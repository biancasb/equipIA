import os


def _pasta_base() -> str:
    return os.getenv("RESULTADOS_DIR", "resultado_modelos")


def proximo_numero() -> int:
    pasta_base = _pasta_base()
    maior = 0
    if os.path.isdir(pasta_base):
        for _, _, arquivos in os.walk(pasta_base):
            for nome in arquivos:
                if nome.startswith("teste") and nome.endswith(".txt"):
                    parte = nome[5:-4]
                    if parte.isdigit():
                        maior = max(maior, int(parte))
    return maior + 1


def salvar_resultado(provider: str, conteudo: str, numero: int | None = None) -> str:
    pasta = os.path.join(_pasta_base(), provider)
    os.makedirs(pasta, exist_ok=True)

    if numero is None:
        numero = proximo_numero()
    caminho = os.path.join(pasta, f"teste{numero}.txt")

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)
    return caminho