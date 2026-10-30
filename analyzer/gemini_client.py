"""
==========================================================
  Cliente da API Google Gemini (Triagem de IA)
==========================================================
"""

from __future__ import annotations

import asyncio
import logging
import re
from google import genai

from config.settings import GEMINI_MODEL, DESCARTE_SENTINELA
from core.models import DetalhesVaga, ResultadoTriagem
from .prompts import construir_system_prompt

log = logging.getLogger("agente_vagas.analyzer")


_TITULO_OBVIAMENTE_INCOMPATIVEL = (
    "atendente de restaurante",
    "atendente de lanchonete",
    "operador de caixa",
    "auxiliar de cozinha",
    "auxiliar de serviços gerais",
    "garçom",
    "garcon",
    "cozinheiro",
    "promotor de vendas",
    "consultor de vendas",
    "vendedor",
    "recepcionista",
    "motorista",
)


def _titulo_obviamente_incompativel(texto: str) -> str | None:
    """Retorna o motivo apenas quando o título indica cargo não técnico."""
    match = re.search(r"TÍTULO:\s*(.+)", texto, flags=re.IGNORECASE)
    if not match:
        return None

    titulo = " ".join(match.group(1).split()).lower()
    for termo in _TITULO_OBVIAMENTE_INCOMPATIVEL:
        if termo in titulo:
            return termo
    return None


class GeminiAnalyzer:
    """Responsável por avaliar a compatibilidade das vagas usando a API Gemini."""

    def __init__(self, api_key: str, curriculo: str, model: str = GEMINI_MODEL) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.system_prompt = construir_system_prompt(curriculo)

    async def analisar(self, vaga: DetalhesVaga) -> ResultadoTriagem:
        """
        Submete o texto da vaga ao Gemini e retorna o ResultadoTriagem estruturado.
        """
        log.info("   🤖 Avaliando com Gemini 3.6 Flash: %s", vaga.url)

        texto_truncado = vaga.texto_completo[:15_000]

        motivo_pre_filtro = _titulo_obviamente_incompativel(texto_truncado)
        if motivo_pre_filtro:
            log.info(
                "      ❌ Pré-filtro: cargo obviamente incompatível (%s)",
                motivo_pre_filtro,
            )
            return ResultadoTriagem(
                url=vaga.url,
                aprovada=False,
                relatorio=(
                    f"{DESCARTE_SENTINELA}: cargo incompatível "
                    f"({motivo_pre_filtro})"
                ),
            )

        user_prompt = (
            f"Texto extraído da página da vaga ({vaga.url}):\n\n"
            f"---\n{texto_truncado}\n---"
        )

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=user_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.2,
                    max_output_tokens=1024,
                ),
            )

            resultado_texto = (
                response.text.strip() if response.text else DESCARTE_SENTINELA
            )

            if DESCARTE_SENTINELA in resultado_texto:
                log.info("      ❌ Vaga descartada (incompatível ou mais antiga que 7 dias).")
                return ResultadoTriagem(
                    url=vaga.url,
                    aprovada=False,
                    relatorio=resultado_texto,
                )

            relatorio_final = resultado_texto + f"\nLINK DIRETO: {vaga.url}"
            log.info("      ✅ Vaga do dia APROVADA!")
            return ResultadoTriagem(
                url=vaga.url,
                aprovada=True,
                relatorio=relatorio_final,
            )

        except Exception as exc:
            log.error("      ✖ Erro na API Gemini para %s: %s", vaga.url, exc)
            return ResultadoTriagem(
                url=vaga.url,
                aprovada=False,
                relatorio=f"Erro na análise: {exc}",
            )
