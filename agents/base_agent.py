import os
from abc import ABC, abstractmethod
from langchain_core.language_models import BaseChatModel
from custo import contador


def build_llm(tempreature: float = 0.0) -> BaseChatModel:
        provider = os.getenv("LLM_PROVIDER", "ollama").lower()

        if provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=os.getenv("OLLAMA_MODEL", "llama3.2"),
                temperature=tempreature,
            )
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic # rever o pq import deu ruim
            return ChatAnthropic(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022"),
                temperature=tempreature,
            )
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=tempreature,
            )
        else: 
            raise ValueError(f"LLM_PROVIDER inválido: '{provider}'. Use 'ollama', 'anthropic' ou 'openai'.")

class BaseSpecialistAgent(ABC):
    def __init__(self):
        self.llm = build_llm()

    @property
    @abstractmethod
    def specialty(self) -> str:
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    def analyze(self, case_summary: str, opinioes_anteriores: list[dict] | None = None) -> str:
        contexto_opinioes = ""
        if opinioes_anteriores:
            contexto_opinioes = "\n\nOPINIÕES DOS OUTROS ESPECIALISTAS:\n" + "\n\n".join(
                f"[{op['especialista']}]\n{op['opiniao']}" for op in opinioes_anteriores
            )

        messages = [
            ("system", self.system_prompt),
            ("human", f"{case_summary}{contexto_opinioes}"),
        ]
        response = self.llm.invoke(messages)
        contador.registrar(self.specialty, response)
        return response.content