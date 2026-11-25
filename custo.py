from dataclasses import dataclass, field
import requests


PRECO_POR_MILHAO = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-5": (3.00, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
}


@dataclass
class ContadorUso:
    chamadas: list = field(default_factory=list)

    def registrar(self, origem: str, resposta):
        uso = getattr(resposta, "usage_metadata", None)
        if not uso:
            return

        meta = getattr(resposta, "response_metadata", {}) or {}
        modelo = meta.get("model") or meta.get("model_name") or "desconhecido"
        self.chamadas.append({
            "origem": origem,
            "modelo": modelo,
            "entrada": uso.get("input_tokens", 0),
            "saida": uso.get("output_tokens", 0),
        })

    def calcular_custo(self) -> float:
        custo_usd = 0.0
        for c in self.chamadas:
            precos = next(
                (p for nome, p in PRECO_POR_MILHAO.items() if c["modelo"].startswith(nome)),
                None,
            )
            if not precos:
                continue  # sem preço cadastrado (ex: Ollama)
            preco_entrada, preco_saida = precos
            custo_usd += c["entrada"] / 1_000_000 * preco_entrada
            custo_usd += c["saida"] / 1_000_000 * preco_saida
        return custo_usd * COTACAO_DOLAR_REAL

    def relatorio(self) -> None:
        total_entrada = sum(c["entrada"] for c in self.chamadas)
        total_saida = sum(c["saida"] for c in self.chamadas)

        print(f"\n{'=' * 60}\nUso de Token\n{'=' * 60}")
        for c in self.chamadas:
            print(f"- {c['origem']} ({c['modelo']}): {c['entrada']} entrada + {c['saida']} saída")

        print(f"\nTotal: {total_entrada} entrada, {total_saida} saída, {total_entrada + total_saida} no geral")
        print(f"Custo estimado: R$ {self.calcular_custo():.4f}")


def obter_cotacao_dolar(padrao: float = 5.0) -> float:
    try:
        resposta = requests.get(
            "https://economia.awesomeapi.com.br/json/last/USD-BRL",
            timeout=5,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        return float(dados["USDBRL"]["bid"])
    except Exception as erro:
        print(f"Aviso: não foi possível ter a cotação atual ({erro}). Usando valor padrão: R$ {padrao}")
        return padrao


COTACAO_DOLAR_REAL = obter_cotacao_dolar()

contador = ContadorUso()