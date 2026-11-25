import json
from agents.base_agent import BaseSpecialistAgent
from custo import contador

class ClinicoGeralAgent(BaseSpecialistAgent):
    @property
    def specialty(self) -> str:
        return "Clínico Geral"

    @property
    def system_prompt(self) -> str:
        return """Você atua como clínico geral em pronto-socorro. É o primeiro a avaliar o caso — sua análise define quais especialistas entram e com que urgência.

Antes de responder, siga este raciocínio:
1. Qual síndrome clínica principal define o caso (ex: síndrome coronariana aguda, abdome agudo, síndrome febril)?
2. Quais causas fatais precisam ser descartadas primeiro?
3. Dado o perfil do paciente, quais causas são mais prováveis?
4. Os sinais vitais indicam instabilidade?
5. Que dados críticos estão faltando pra uma decisão seguindo com segurança?

Checar explicitamente presença ou ausência de:
- instabilidade hemodinâmica (choque, hipotensão, taquicardia)
- comprometimento de via aérea ou respiração, SpO2 < 90%
- dor torácica com características de síndrome coronariana aguda
- febre com rigidez de nuca
- sangramento ativo significativo

Aplicar escore quando o quadro indicar:
- qSOFA (sepse): FR ≥ 22, alteração cognitiva, PAS ≤ 100 — ≥ 2 pontos = alto risco
- CURB-65 (pneumonia): confusão, ureia, FR, PA, idade ≥ 65
- Wells (TEP): clínica, FC, imobilização, neoplasia, TVP prévia, hemoptise, diagnóstico alternativo
- HEART score (dor torácica): história, ECG, idade, fatores de risco, troponina

Estruture a resposta assim:

Red flags identificados
Presentes e ausentes, explicitamente.

Síndrome clínica principal
Qual e por que.

Diagnóstico diferencial
Ordenado por probabilidade (alta/média/baixa), com evidências a favor e contra de cada hipótese.

Dados críticos ausentes
O que falta pra decidir com segurança.

Exames prioritários
Quais, por quê, o que se espera encontrar.

Urgência e disposição
Emergência, urgência ou eletivo — com o critério que embasou essa classificação.

Especialistas necessários
Quais, e o motivo específico de cada indicação."""

    def triagem(self, caso: str) -> dict:
            prompt = """Você é um clínico geral fazendo a triagem inicial de um caso.

    Classifique o caso em UMA síndrome principal, usando estas pistas:
    - sindrome_coronariana: dor torácica em aperto/opressão, pode irradiar para braço/mandíbula/costas, sudorese, fatores de risco cardiovascular
    - tromboembolismo_pulmonar: falta de ar súbita, dor que piora ao respirar, taquicardia, fator de risco para TVP
    - pneumonia: febre, tosse, expectoração
    - outro: não se encaixa claramente em nenhuma acima

    Indique também quais especialistas devem ser acionados, entre: cardiologista, pneumologista.

    Responda APENAS em JSON:
    {"sindrome": "chave", "especialistas": ["especialista1"], "justificativa": "uma frase"}
    """
            resposta = self.llm.invoke([
                ("system", prompt),
                ("human", caso),
            ])
            contador.registrar("Triagem (Clínico Geral)", resposta)
            texto = resposta.content.strip()
            inicio = texto.find("{")
            if inicio == -1:
                return {"sindrome": "outro", "especialistas": [], "justificativa": ""}
            try:
                dados, _ = json.JSONDecoder().raw_decode(texto[inicio:])
                return dados
            except json.JSONDecodeError:
                return {"sindrome": "outro", "especialistas": [], "justificativa": ""}

    def triagem_dinamica(self, caso: str, sindromes: dict, especialistas: list) -> dict:
        lista = "\n".join(f"- {chave}: {pistas}" for chave, pistas in sindromes.items())
        prompt = f"""Você é um clínico geral fazendo a triagem inicial de um caso.

Classifique o caso em UMA síndrome principal, usando estas pistas:
{lista}
- outro: não se encaixa claramente em nenhuma acima

Indique também quais especialistas devem ser acionados, entre: {", ".join(especialistas)}.
Responda APENAS em JSON:
{{"sindrome": "chave", "especialistas": ["especialista1"], "justificativa": "uma frase"}}
"""
        resposta = self.llm.invoke([
            ("system", prompt),
            ("human", caso),
        ])
        contador.registrar("Triagem (Clínico Geral)", resposta)
        texto = resposta.content.strip()
        inicio = texto.find("{")
        padrao = {"sindrome": "outro", "especialistas": [], "justificativa": ""}
        if inicio == -1:
            return padrao
        try:
            dados, _ = json.JSONDecoder().raw_decode(texto[inicio:])
        except json.JSONDecodeError:
            return padrao
        if dados.get("sindrome") not in sindromes:
            dados["sindrome"] = "outro"
        return dados