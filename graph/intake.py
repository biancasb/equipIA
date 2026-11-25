import json
from agents.base_agent import build_llm
from graph.requisitos_escores import REQUISITOS_ESCORES
from custo import contador

INTAKE_PROMPT = """Você avalia se um caso clínico tem dados suficientes para diagnóstico e cálculo de escores de risco.

Verifique se o caso contém:
- idade e sexo
- sintoma principal, início, duração, características (localização, irradiação, intensidade)
- sinais vitais completos: PA, FC, FR, SpO2, temperatura
- comorbidades e medicamentos em uso (ou confirmação de ausência)

REGRA CRÍTICA: se houver suspeita de síndrome coronariana aguda (dor torácica com características cardíacas, aperto, irradiação, sudorese),
o caso só é SUFICIENTE se o resultado de ECG e troponina estiverem descritos. Se não estiverem, marque como insuficiente e inclua essas perguntas.

Se qualquer pergunta for gerada, "suficiente" DEVE ser false. Nunca devolva perguntas com "suficiente": true.

Responda APENAS em JSON, sem texto adicional:
{"suficiente": true ou false, "perguntas": ["pergunta 1", "pergunta 2"]}
"""

def avaliar_suficiencia(caso: str) -> dict:
    llm = build_llm()

    # print("CASO TESTE ENVIADO:")
    # print(caso)
    # print("-" * 40)

    resposta = llm.invoke([
        ("system", INTAKE_PROMPT),
        ("human", caso),
    ])
    contador.registrar("Intake", resposta)
    
    texto = resposta.content.strip()
    inicio = texto.find("{")

    if inicio == -1:
        return {"suficiente": True, "perguntas": []}

    try:
        dados, _ = json.JSONDecoder().raw_decode(texto[inicio:])
    except json.JSONDecodeError:
        return {"suficiente": True, "perguntas": []}

    dados["suficiente"] = len(dados.get("perguntas", [])) == 0
    return dados

def avaliar_suficiencia_para_escores(caso: str, sindrome: str, ja_foi_perguntado: set = None) -> dict:
    requisitos = REQUISITOS_ESCORES.get(sindrome)
    if not requisitos:
        return avaliar_suficiencia(caso)

    ja_foi_perguntado = ja_foi_perguntado or set()
    perguntas_modelo = requisitos["perguntas_triagem"]

    possivel_perg = [(i, p) for i, p in enumerate(perguntas_modelo, start=1) if i not in ja_foi_perguntado]
    if not possivel_perg:
        return {"suficiente": True, "perguntas": [], "indices": []}

    lista_numerada = "\n".join(f"{i}. {p}" for i, p in possivel_perg)

    prompt = f"""Abaixo está uma lista numerada de informações clínicas. Diga quais delas AINDA NÃO estão respondidas no caso, mesmo que de forma indireta.

    {lista_numerada}

    Responda APENAS em JSON com os números pendentes: {{"pendentes": [1, 3]}} """

    llm = build_llm()
    resposta = llm.invoke([("system", prompt), ("human", caso)])
    contador.registrar("Intake", resposta)

    texto = resposta.content.strip()
    inicio = texto.find("{")

    if inicio == -1:
        return {"suficiente": True, "perguntas": [], "indices": []}
    try:
        dados, _ = json.JSONDecoder().raw_decode(texto[inicio:])
    except json.JSONDecodeError:
        return {"suficiente": True, "perguntas": [], "indices": []}

    indices_pendentes = [i for i in dados.get("pendentes", []) if 1 <= i <= len(perguntas_modelo)]
    perguntas_pendentes = [perguntas_modelo[i - 1] for i in indices_pendentes]

    return {
        "suficiente": len(perguntas_pendentes) == 0,
        "perguntas": perguntas_pendentes,
        "indices": indices_pendentes,
    }