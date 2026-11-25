"""Teste 2 - controles de triagem (roda SÓ a triagem, sem especialistas).

Roda cada caso de controle N vezes em cada modelo e grava analise/triagem_controles.csv.
Uso (na pasta do projeto, com o .venv ativo):
    python triagem_controles.py            (3 execuções por caso e modelo)
    python triagem_controles.py 5          (5 execuções)
O Ollama precisa estar aberto para o modelo local.
"""
import csv
import os
import sys

from dotenv import load_dotenv

load_dotenv()
from agents.clinico_geral import ClinicoGeralAgent  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3
PROVEDORES = ["ollama", "anthropic", "openai"]
VALIDOS = {"cardiologista", "pneumologista"}

# (nome, texto, síndrome esperada, especialistas esperados)
CONTROLES = [
    ("Controle 1 (Case 28, p. 95)",
     "Mulher, 30 anos, com dor no lado esquerdo do peito há 2 dias. A dor começou como um "
     "desconforto leve e intermitente e agora está constante e intensa. Não piora com esforço "
     "nem alivia com repouso, é bem localizada e vem com leve falta de ar ao tentar respirar "
     "fundo. Não fuma e não tem histórico familiar de doença cardiovascular.",
     "outro", "Clínico Geral"),
    ("Controle 2 (TEP, elaborado pela autora)",
     "Mulher, 45 anos, 8 dias após artroplastia de joelho, com cansaço que começou de repente "
     "e dor no peito ao respirar fundo. Apresenta taquicardia e leve inchaço na panturrilha "
     "esquerda.",
     "tromboembolismo_pulmonar", "Clínico Geral|Pneumologista"),
]

saida = os.path.join("analise", "triagem_controles.csv")
campos = ["caso", "provider", "execucao", "sindrome_esperada", "sindrome", "especialistas_esperados",
          "especialistas", "acerto_sindrome", "acerto_especialistas", "justificativa"]
with open(saida, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    for prov in PROVEDORES:
        os.environ["LLM_PROVIDER"] = prov
        try:
            agente = ClinicoGeralAgent()
        except Exception as e:
            print(f"[{prov}] não foi possível iniciar: {e}")
            continue
        for nome, texto, esperada, esp_esperados in CONTROLES:
            for i in range(1, N + 1):
                try:
                    t = agente.triagem(texto)
                except Exception as e:
                    print(f"[{prov}] {nome} #{i}: erro ({type(e).__name__}) - pulei")
                    continue
                sind = t.get("sindrome", "outro")
                esp = ["Clínico Geral"] + [e.capitalize() for e in t.get("especialistas", [])
                                            if e in VALIDOS]
                conj = lambda s: {x.strip().lower() for x in s.replace("|", ",").split(",") if x.strip()}
                a_s = float(sind == esperada)
                a_e = float(conj(",".join(esp)) == conj(esp_esperados))
                w.writerow({"caso": nome, "provider": prov, "execucao": i,
                            "sindrome_esperada": esperada, "sindrome": sind,
                            "especialistas_esperados": esp_esperados, "especialistas": "|".join(esp),
                            "acerto_sindrome": a_s, "acerto_especialistas": a_e,
                            "justificativa": t.get("justificativa", "")})
                f.flush()
                print(f"[{prov}] {nome} #{i}: {sind} | {'|'.join(esp)} -> "
                      f"{'OK' if a_s and a_e else 'diferente do esperado'}")
print(f"\nGravado em {saida}. Agora rode: cd analise && python matriz_confusao.py")
