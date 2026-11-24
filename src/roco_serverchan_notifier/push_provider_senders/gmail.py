from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from ..push_http import HttpSession
from ..push_models import NotificationMessage, ProviderConfig, PushResult


def send_gmail(
    provider: ProviderConfig, message: NotificationMessage, session: HttpSession, timeout: int
) -> PushResult:
    sender = provider.config["email"]
    recipient = provider.config.get("to") or sender
    password = "".join(provider.config["app_password"].split())
    email = EmailMessage()
    email["From"] = sender
    email["To"] = recipient
    email["Subject"] = message.title
    email.set_content(message.markdown or message.body)
    result_fields = (provider.id, provider.name, provider.type)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=timeout, context=ssl.create_default_context()) as smtp:
            smtp.login(sender, password)
            smtp.send_message(email, from_addr=sender, to_addrs=[recipient])
    except smtplib.SMTPAuthenticationError as exc:
        return PushResult(*result_fields, False, "Gmail SMTP 验证失败，请检查应用专用密码", exc.smtp_code)
    except smtplib.SMTPResponseException as exc:
        return PushResult(*result_fields, False, f"Gmail SMTP 拒绝邮件（{exc.smtp_code}）", exc.smtp_code)
    except OSError as exc:
        return PushResult(*result_fields, False, f"Gmail SMTP 连接或发送失败（{type(exc).__name__}）")

    return PushResult(*result_fields, True, "Gmail SMTP 已接受邮件")
