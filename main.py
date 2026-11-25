import os
import time
from dotenv import load_dotenv
load_dotenv()

from custo import contador
from resultados import salvar_resultado, proximo_numero
from graph.requisitos_escores import REQUISITOS_ESCORES
from graph.triagem_config import SINDROMES_TRIAGEM
from graph.intake import avaliar_suficiencia_para_escores
from agents.clinico_geral import ClinicoGeralAgent
from agents.cardiologista import CardiologistaAgent
from agents.pneumologista import PneumologistaAgent
from agents.farmaceutico import FarmaceuticoAgent

#especialistas que a triagem pode escolher (guarda a classe, não a instância)
REGISTRO_ESPECIALISTAS = {
    "cardiologista": CardiologistaAgent,
    "pneumologista": PneumologistaAgent,
}


def formatar_tempo(segundos: float) -> str:
    segundos = round(segundos)
    if segundos < 60:
        return f"{segundos}s"
    minutos, resto = divmod(segundos, 60)
    return f"{minutos}min{resto:02d}s"


def ler_caso_do_usuario() -> str:
    return input("Digite o caso clínico e aperte Enter:\n\n").strip()


numero_teste = proximo_numero()
print(f"Caso nº {numero_teste}\n")
caso = ler_caso_do_usuario()

inicio = time.perf_counter()
tempo_espera_usuario = 0.0

#1 triagem
clinico_geral = ClinicoGeralAgent()
triagem = clinico_geral.triagem(caso)
sindrome = triagem["sindrome"]
print(f"\nSíndrome identificada: {sindrome} — {triagem.get('justificativa', '')}")

requisitos = REQUISITOS_ESCORES.get(sindrome)
if requisitos and requisitos.get("exames_complementares"):
    print(f"\nExames que os especialistas vão considerar, se disponível: {', '.join(requisitos['exames_complementares'])}")
    print("(não são perguntados agora - isso é papel da equipe médica, não do paciente)\n")

#perguntas complementares
max_rodadas = 2
rodada = 0
ja_foi_perguntado = set()

while rodada < max_rodadas:
    avaliacao = avaliar_suficiencia_para_escores(caso, sindrome, ja_foi_perguntado)
    if avaliacao["suficiente"]:
        break

    rodada += 1
    print(f"\nRodada {rodada} — preciso de mais informações:\n")

    respostas = []
    # for indice, pergunta in zip(avaliacao["indices"], avaliacao["perguntas"]):
    #     t0 = time.perf_counter()
    #     resposta = input(f"{pergunta} ")
    #     tempo_espera_usuario += time.perf_counter() - t0
    #     respostas.append(f"{pergunta} {resposta}")
    #     ja_foi_perguntado.add(indice)

    indices = avaliacao.get("indices") or [None] * len(avaliacao["perguntas"])
    respostas = []
    for indice, pergunta in zip(indices, avaliacao["perguntas"]):
        t0 = time.perf_counter()
        resposta = os.getenv("RESPOSTA_AUTOMATICA") or input(f"{pergunta} ")
        tempo_espera_usuario += time.perf_counter() - t0
        respostas.append(f"{pergunta} {resposta}")
        if indice is not None:
            ja_foi_perguntado.add(indice)

    caso += "\nInformações complementares:\n" + "\n".join(respostas)

print("\nCaso final considerado:\n", caso)

#especialistas selecionados pela triagem
agentes = [clinico_geral]
for chave in triagem.get("especialistas", []):
    classe = REGISTRO_ESPECIALISTAS.get(chave)
    if classe:
        agentes.append(classe())

print(f"\nEspecialistas acionados: {[a.specialty for a in agentes]}\n")

opinioes = []
for agente in agentes:
    print(f"\n{'=' * 60}\n{agente.specialty}\n{'=' * 60}")
    resultado = agente.analyze(caso)
    print(resultado)
    opinioes.append({"especialista": agente.specialty, "opiniao": resultado})

#farmacêutico (sempre roda, vê as opiniões dos outros)
farmaceutico = FarmaceuticoAgent()
print(f"\n{'=' * 60}\n{farmaceutico.specialty}\n{'=' * 60}")
resposta_farmaceutico = farmaceutico.analyze(caso, opinioes)
print(resposta_farmaceutico)

#tempo
tempo_total = time.perf_counter() - inicio
tempo_processamento = tempo_total - tempo_espera_usuario

#custo e tokens
contador.relatorio()
print(f"\nTempo total: {formatar_tempo(tempo_total)}")
print(f"Tempo de processamento (sem espera do usuário): {formatar_tempo(tempo_processamento)}")

#salvar resultado
provider = os.getenv("LLM_PROVIDER", "ollama").lower()
tokens_entrada = sum(c["entrada"] for c in contador.chamadas)
tokens_saida = sum(c["saida"] for c in contador.chamadas)
modelo = contador.chamadas[0]["modelo"] if contador.chamadas else "desconhecido"


conteudo = f"""numero_teste: {numero_teste}
provider: {provider}
modelo: {modelo}
sindrome: {sindrome}
especialistas: {', '.join(a.specialty for a in agentes)}
tokens_entrada: {tokens_entrada}
tokens_saida: {tokens_saida}
custo_brl: {contador.calcular_custo():.4f}
tempo_total_s: {tempo_total:.1f}
tempo_processamento_s: {tempo_processamento:.1f}
tempo_legivel: {formatar_tempo(tempo_processamento)}

=== CASO ===
{caso}

=== OPINIÕES ===
"""
for op in opinioes:
    conteudo += f"\n[{op['especialista']}]\n{op['opiniao']}\n"

conteudo += f"\n[Farmacêutico Clínico]\n{resposta_farmaceutico}\n"

caminho = salvar_resultado(provider, conteudo, numero_teste)
print(f"\nResultado salvo em: {caminho}")