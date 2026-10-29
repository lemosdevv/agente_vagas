"""
==========================================================
  Classe Base de Extrator de Portais (Base Extractor)
==========================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from playwright.async_api import Page


class BaseExtractor(ABC):
    """Contrato base para extratores de detalhes de vagas."""

    @abstractmethod
    async def extrair(self, page: Page) -> str | None:
        """
        Extrai as informações relevantes da página da vaga.
        Retorna uma string estruturada ou None se falhar.
        """
        raise NotImplementedError
