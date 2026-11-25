import glob
import os
import re
import sys
import time

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
from custo import contador  # noqa: E402
from agents.clinico_geral import ClinicoGeralAgent  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
PROVEDORES = ["ollama", "anthropic", "openai"]
gab = pd.read_csv(os.path.join("analise", "gabarito.csv"))
caso_de = dict(zip(gab["numero_teste"], gab["caso"]))


def caso_final(provider, caso):
    """Texto do caso (com informações complementares) da 1ª execução multiagente."""
    arqs = sorted(glob.glob(os.path.join("resultado_modelos", provider, "teste*.txt")),
                  key=lambda a: int(re.search(r"teste(\d+)", a).group(1)))
    for a in arqs:
        if caso_de.get(int(re.search(r"teste(\d+)", a).group(1))) == caso:
            txt = open(a, encoding="utf-8").read()
            return txt.split("=== CASO ===")[1].split("=== OPINI")[0].strip()
    return None


for prov in PROVEDORES:
    os.environ["LLM_PROVIDER"] = prov
    for caso in ["Caso 1", "Caso 2"]:
        texto = caso_final(prov, caso)
        if not texto:
            print(f"[{prov}] sem execução multiagente de {caso} - pulei")
            continue
        pasta = os.path.join("resultado_baseline", prov)
        os.makedirs(pasta, exist_ok=True)
        slug = caso.replace(" ", "").lower()
        ja = len(glob.glob(os.path.join(pasta, f"baseline_{slug}_*.txt")))
        for i in range(ja + 1, ja + N + 1):
            try:
                contador.chamadas.clear()
                t0 = time.perf_counter()
                resposta = ClinicoGeralAgent().analyze(texto)
                seg = time.perf_counter() - t0
            except Exception as e:
                print(f"[{prov}] {caso} #{i}: erro ({type(e).__name__}) - pulei")
                continue
            ent = sum(c["entrada"] for c in contador.chamadas)
            sai = sum(c["saida"] for c in contador.chamadas)
            modelo = contador.chamadas[0]["modelo"] if contador.chamadas else "desconhecido"
            conteudo = (f"numero_teste: baseline_{slug}_{i}\nprovider: {prov}\nmodelo: {modelo}\n"
                        f"caso: {caso}\nmodo: agente_unico\ntokens_entrada: {ent}\ntokens_saida: {sai}\n"
                        f"custo_brl: {contador.calcular_custo():.4f}\ntempo_s: {seg:.1f}\n\n"
                        f"=== CASO ===\n{texto}\n\n=== OPINIÕES ===\n\n"
                        f"[Clínico Geral (agente único)]\n{resposta}\n")
            caminho = os.path.join(pasta, f"baseline_{slug}_{i}.txt")
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(conteudo)
            print(f"[{prov}] {caso} #{i}: salvo em {caminho} ({seg:.0f}s)")
