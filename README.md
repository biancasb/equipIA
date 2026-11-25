# EquipIA

Arquitetura multiagente de IA para apoio à decisão clínica em casos descritos em português.
Este repositório contém o código desenvolvido no Trabalho de Conclusão de Curso de Informática Biomédica da UFCSPA, orientado pelo Prof. Dr. Muriel Figueredo Franco.

## Sobre o projeto

O nome EquipIA vem da junção de equipe e IA, porque o sistema funciona como uma equipe de especialistas em que cada membro é um agente de inteligência artificial.

O caso clínico entra em texto livre e passa por quatro fases. Primeiro, o agente Clínico Geral faz a triagem, identifica a síndrome principal e escolhe quais especialistas vão participar. Depois, o sistema pergunta ao usuário os dados que faltam para os escores clínicos, em até duas rodadas. Em seguida, os agentes de Cardiologia e Pneumologia analisam o caso de forma independente. Por fim, o agente Farmacêutico Clínico revisa as condutas sugeridas, apontando interações, contraindicações e ajustes de dose.

Cada execução gera um registro com a opinião de cada agente, os tokens usados, o custo e o tempo de processamento.

## Tecnologias

- Python
- LangChain
- Claude Haiku 4.5 e GPT-4o-mini, acessados via API
- Llama 3.2, executado localmente via Ollama

## Como rodar

Clone o repositório e crie um ambiente virtual.

```bash
git clone LINK_DO_REPOSITORIO
cd NOME_DA_PASTA
python -m venv venv
source venv/bin/activate
```

No Windows, o comando para ativar o ambiente é `venv\Scripts\activate`.
Instale as dependências.

```bash
pip install -r requirements.txt
```

Copie o arquivo `.env.example` para `.env` e preencha com as suas chaves de API. O provedor do modelo também é escolhido nesse arquivo, então dá para trocar de modelo sem mexer no código.

```bash
cp .env.example .env
```

Para usar o Llama 3.2 localmente, instale o [Ollama](https://ollama.com) e baixe o modelo antes de rodar.

```bash
ollama pull llama3.2
```

Depois é só executar o sistema.

```bash
python main.py
```

## Avaliação

A avaliação usou dois casos clínicos adaptados do livro *100 Cases in Emergency Medicine and Critical Care*, um de dor torácica e outro de pneumonia com sinais de sepse. Cada caso foi executado dez vezes com cada um dos três modelos, somando 60 execuções. Foram medidos o acerto da triagem, a cobertura de um checklist clínico, o custo e o tempo de resposta. Os resultados completos estão no artigo do TCC.

## Publicações

- Bernardi, B. S. e Franco, M. F. Arquitetura Multiagente de IA para Apoio à Decisão Clínica: Uma Abordagem baseada em Especialidades Médicas. ERAMIA 2026.
- Bernardi, B. S. e Franco, M. F. EquipIA: Arquitetura Multiagente de IA para Apoio à Decisão Clínica. Submetido à REIC.


## Autora

Bianca Siega Bernardi, Informática Biomédica, UFCSPA.