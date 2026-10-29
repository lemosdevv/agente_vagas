from .browser import criar_contexto_navegador, fechar_popups
from .discovery import descobrir_vagas, detectar_portal
from .service import raspar_detalhe_vaga

__all__ = [
    "criar_contexto_navegador",
    "fechar_popups",
    "descobrir_vagas",
    "detectar_portal",
    "raspar_detalhe_vaga",
]
