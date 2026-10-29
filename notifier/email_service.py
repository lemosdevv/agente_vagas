"""
==========================================================
  Serviço de Notificação por E-mail (Notifier)
==========================================================
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from config.settings import SMTP_HOST, SMTP_PORT, TEMPLATES_DIR
from core.models import ResultadoTriagem

log = logging.getLogger("agente_vagas.notifier")


class EmailService:
    """Responsável por renderizar templates HTML e disparar e-mails via SMTP SSL."""

    def __init__(self, remetente: str, senha_app: str) -> None:
        self.remetente = remetente
        self.senha_app = senha_app
        self.template_path = TEMPLATES_DIR / "report_email.html"

    def renderizar_relatorio_html(self, vagas_aprovadas: list[ResultadoTriagem]) -> str:
        """Renderiza os cards das vagas aprovadas no template HTML."""
        cards: list[str] = []

        for i, vaga in enumerate(vagas_aprovadas, start=1):
            linhas = vaga.relatorio.replace("\n", "<br>")
            card = f"""
            <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-left: 5px solid #1a73e8;
                        padding: 18px; margin: 18px 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3 style="color: #1a73e8; margin: 0; font-size: 17px;">
                        🎯 Vaga #{i} (Publicada Hoje)
                    </h3>
                    <span style="background-color: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        Últimas 24h
                    </span>
                </div>
                <div style="font-family: monospace; font-size: 13.5px; line-height: 1.7; color: #202124; background-color: #f8f9fa; padding: 12px; border-radius: 6px;">
                    {linhas}
                </div>
                <div style="margin-top: 14px;">
                    <a href="{vaga.url}" target="_blank"
                       style="display: inline-block; padding: 9px 18px;
                              background-color: #1a73e8; color: #ffffff; text-decoration: none;
                              border-radius: 5px; font-weight: bold; font-size: 13.5px;">
                        Candidatar-se na Vaga ↗
                    </a>
                </div>
            </div>
            """
            cards.append(card)

        template_str = self.template_path.read_text(encoding="utf-8")
        return template_str.replace("{total_vagas}", str(len(vagas_aprovadas))).replace(
            "{cards_html}", "\n".join(cards)
        )

    def enviar_relatorio(
        self, destinatario: str, assunto: str, vagas_aprovadas: list[ResultadoTriagem]
    ) -> bool:
        """Envia o e-mail consolidado para o destinatário."""
        if not vagas_aprovadas:
            log.info("📭 Nenhuma vaga para notificar.")
            return False

        log.info("📧 Enviando e-mail com %d vaga(s) para %s …", len(vagas_aprovadas), destinatario)
        corpo_html = self.renderizar_relatorio_html(vagas_aprovadas)

        msg = MIMEMultipart("alternative")
        msg["From"] = self.remetente
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))

        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
                smtp.login(self.remetente, self.senha_app)
                smtp.send_message(msg)
            log.info("   ✔ E-mail consolidado enviado com sucesso!")
            return True
        except Exception as exc:
            log.error("   ✖ Falha ao enviar e-mail: %s", exc)
            return False
