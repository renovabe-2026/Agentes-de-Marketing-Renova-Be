"""Envia resultados dos agentes por email via SMTP."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _format_html(task: str, results: dict[str, str]) -> str:
    """Formata os resultados em HTML para email."""
    agents_html = ""
    for agent_name, result in results.items():
        result_escaped = result.replace("\n", "<br>")
        agents_html += f"""
        <div style="margin-bottom: 24px; padding: 16px; background: #f8f9fa;
                     border-left: 4px solid #4CAF50; border-radius: 4px;">
            <h3 style="margin: 0 0 12px 0; color: #2e7d32;">{agent_name}</h3>
            <div style="color: #333; line-height: 1.6;">{result_escaped}</div>
        </div>
        """

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;
                  padding: 20px; color: #333;">
        <div style="background: #1a237e; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="margin: 0; font-size: 20px;">Renova Be - Agentes de Marketing</h1>
            <p style="margin: 8px 0 0 0; opacity: 0.9;">Resultado da execucao de tarefa</p>
        </div>

        <div style="padding: 20px; border: 1px solid #e0e0e0; border-top: none;
                     border-radius: 0 0 8px 8px;">
            <div style="background: #e3f2fd; padding: 12px 16px; border-radius: 4px;
                        margin-bottom: 24px;">
                <strong>Tarefa:</strong> {task}
            </div>

            <h2 style="color: #1a237e; border-bottom: 2px solid #e0e0e0;
                       padding-bottom: 8px;">Resultados por Agente</h2>

            {agents_html}
        </div>

        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 20px;">
            Gerado automaticamente pelo sistema de Agentes de Marketing - Renova Be
        </p>
    </body>
    </html>
    """


def _format_plain(task: str, results: dict[str, str]) -> str:
    """Formata os resultados em texto puro."""
    lines = [
        "RENOVA BE - AGENTES DE MARKETING",
        "=" * 40,
        f"\nTarefa: {task}\n",
        "-" * 40,
    ]
    for agent_name, result in results.items():
        lines.append(f"\n>> {agent_name}\n")
        lines.append(result)
        lines.append("\n" + "-" * 40)
    return "\n".join(lines)


def send_email(
    task: str,
    results: dict[str, str],
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    email_from: str,
    email_to: str,
) -> None:
    """Envia os resultados dos agentes por email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Renova Be Agentes] Resultado: {task[:80]}"
    msg["From"] = email_from
    msg["To"] = email_to

    plain = _format_plain(task, results)
    html = _format_html(task, results)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(email_from, [email_to], msg.as_string())

    logger.info("Email enviado para %s", email_to)
