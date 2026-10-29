"""
==========================================================
  Modelos de Dados do Domínio (Core Models)
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VagaDescoberta:
    """Representa um link de vaga encontrado em uma busca."""
    url: str
    portal: str
    url_busca_origem: str
    descoberta_em: datetime = field(default_factory=datetime.now)


@dataclass
class DetalhesVaga:
    """Informações textuais brutas extraídas da página da vaga."""
    url: str
    portal: str
    texto_completo: str
    titulo: str | None = None
    empresa: str | None = None
    localizacao: str | None = None
    publicada: str | None = None


@dataclass
class ResultadoTriagem:
    """Resultado da avaliação da vaga pelo Gemini."""
    url: str
    aprovada: bool
    relatorio: str
    analisada_em: datetime = field(default_factory=datetime.now)
