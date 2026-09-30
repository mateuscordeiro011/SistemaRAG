"""
Módulo de Integrações para SistemaRAG
Implementa clientes para WhatsApp (Twilio/Meta), Outlook (Microsoft Graph), Email (SMTP)
"""

import os
import logging
import asyncio
import smtplib
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


# ============================================
# CONFIGURAÇÕES
# ============================================

# Twilio WhatsApp
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# Meta Cloud API (WhatsApp Business)
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
META_WEBHOOK_VERIFY_TOKEN = os.getenv("META_WEBHOOK_VERIFY_TOKEN")

# Microsoft Graph (Outlook)
OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID")
OUTLOOK_USER_EMAIL = os.getenv("OUTLOOK_USER_EMAIL")  # Email da caixa de correio a monitorar

# SMTP Email
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", SMTP_USER)


# ============================================
# BASE ADAPTER
# ============================================

class ChannelAdapter(ABC):
    """Interface base para adaptadores de canal"""
    
    @abstractmethod
    async def send_message(self, to: str, body: str, **kwargs) -> Dict[str, Any]:
        """Envia mensagem pelo canal"""
        pass
    
    @abstractmethod
    async def validate_recipient(self, recipient: str) -> bool:
        """Valida se o destinatário é válido para este canal"""
        pass
    
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Nome do canal"""
        pass


# ============================================
# TWILIO WHATSAPP ADAPTER
# ============================================

class TwilioWhatsAppAdapter(ChannelAdapter):
    """Adapter para WhatsApp via Twilio"""
    
    def __init__(self):
        self.client = None
        self._init_client()
    
    def _init_client(self):
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
                logger.info("Twilio client initialized")
            except ImportError:
                logger.warning("twilio package not installed")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
    
    @property
    def channel_name(self) -> str:
        return "whatsapp_twilio"
    
    async def send_message(self, to: str, body: str, **kwargs) -> Dict[str, Any]:
        if not self.client:
            return {"success": False, "error": "Twilio client not configured"}
        
        # WhatsApp tem limite de 1600 caracteres
        if len(body) > 1600:
            body = body[:1597] + "..."
        
        # Formatar número para WhatsApp
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"
        
        try:
            message = await asyncio.to_thread(
                self.client.messages.create,
                body=body,
                from_=TWILIO_WHATSAPP_NUMBER,
                to=to
            )
            
            logger.info(f"WhatsApp message sent via Twilio: SID={message.sid}")
            return {
                "success": True,
                "message_id": message.sid,
                "status": message.status
            }
        except Exception as e:
            logger.error(f"Twilio WhatsApp send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Valida formato de número WhatsApp (+55XXXXXXXXXX)"""
        import re
        # Aceita formato +55XXXXXXXXXX ou whatsapp:+55XXXXXXXXXX
        clean = recipient.replace("whatsapp:", "")
        pattern = r'^\+?\d{10,15}$'
        return bool(re.match(pattern, clean))


# ============================================
# META CLOUD API WHATSAPP ADAPTER
# ============================================

class MetaWhatsAppAdapter(ChannelAdapter):
    """Adapter para WhatsApp via Meta Cloud API (WhatsApp Business API)"""
    
    def __init__(self):
        self.access_token = META_ACCESS_TOKEN
        self.phone_number_id = META_PHONE_NUMBER_ID
        self.base_url = "https://graph.facebook.com/v18.0"
    
    @property
    def channel_name(self) -> str:
        return "whatsapp_meta"
    
    async def send_message(self, to: str, body: str, **kwargs) -> Dict[str, Any]:
        if not self.access_token or not self.phone_number_id:
            return {"success": False, "error": "Meta Cloud API not configured"}
        
        # Limite de 4096 caracteres para mensagens de texto
        if len(body) > 4096:
            body = body[:4093] + "..."
        
        # Remover prefixo whatsapp: se presente
        clean_to = to.replace("whatsapp:", "")
        
        import aiohttp
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_to,
            "type": "text",
            "text": {"body": body}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        message_id = data.get("messages", [{}])[0].get("id")
                        logger.info(f"WhatsApp message sent via Meta: ID={message_id}")
                        return {"success": True, "message_id": message_id, "response": data}
                    else:
                        error_msg = data.get("error", {}).get("message", "Unknown error")
                        logger.error(f"Meta WhatsApp send error: {error_msg}")
                        return {"success": False, "error": error_msg, "response": data}
        except Exception as e:
            logger.error(f"Meta WhatsApp send exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_template_message(self, to: str, template_name: str, language: str = "pt_BR", components: list = None) -> Dict[str, Any]:
        """Envia mensagem usando template aprovado"""
        if not self.access_token or not self.phone_number_id:
            return {"success": False, "error": "Meta Cloud API not configured"}
        
        clean_to = to.replace("whatsapp:", "")
        
        import aiohttp
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language}
            }
        }
        
        if components is not None:
            payload["template"]["components"] = components
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json()
                    if response.status == 200:
                        message_id = data.get("messages", [{}])[0].get("id")
                        return {"success": True, "message_id": message_id}
                    else:
                        return {"success": False, "error": data.get("error", {}).get("message")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def validate_recipient(self, recipient: str) -> bool:
        import re
        clean = recipient.replace("whatsapp:", "")
        pattern = r'^\+?\d{10,15}$'
        return bool(re.match(pattern, clean))
    
    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verifica webhook do Meta"""
        if mode == "subscribe" and token == META_WEBHOOK_VERIFY_TOKEN:
            return challenge
        return None
    
    async def process_webhook(self, payload: Dict[str, Any]) -> list:
        """Processa webhook recebido do WhatsApp"""
        messages = []
        
        try:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        value = change.get("value", {})
                        for msg in value.get("messages", []):
                            messages.append({
                                "id": msg.get("id"),
                                "from": msg.get("from"),
                                "timestamp": msg.get("timestamp"),
                                "type": msg.get("type"),
                                "text": msg.get("text", {}).get("body") if msg.get("type") == "text" else None,
                                "raw": msg
                            })
        except Exception as e:
            logger.error(f"Error processing WhatsApp webhook: {e}")
        
        return messages


# ============================================
# OUTLOOK / MICROSOFT GRAPH ADAPTER
# ============================================

class OutlookAdapter(ChannelAdapter):
    """Adapter para Outlook via Microsoft Graph API"""
    
    def __init__(self):
        self.client_id = OUTLOOK_CLIENT_ID
        self.client_secret = OUTLOOK_CLIENT_SECRET
        self.tenant_id = OUTLOOK_TENANT_ID
        self.user_email = OUTLOOK_USER_EMAIL
        self._access_token = None
        self._token_expires = 0
    
    @property
    def channel_name(self) -> str:
        return "outlook"
    
    async def _get_access_token(self) -> Optional[str]:
        """Obtém token de acesso usando client credentials flow"""
        import time
        import aiohttp
        
        # Verificar se token ainda é válido
        if self._access_token and time.time() < self._token_expires - 300:  # 5 min buffer
            return self._access_token
        
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.error("Outlook credentials not configured")
            return None
        
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._access_token = data["access_token"]
                        self._token_expires = time.time() + data.get("expires_in", 3600)
                        logger.info("Outlook access token obtained")
                        return self._access_token
                    else:
                        error = await response.text()
                        logger.error(f"Failed to get Outlook token: {error}")
                        return None
        except Exception as e:
            logger.error(f"Outlook token error: {e}")
            return None
    
    async def send_message(self, to: str, body: str, subject: str = None, **kwargs) -> Dict[str, Any]:
        token = await self._get_access_token()
        if not token:
            return {"success": False, "error": "Failed to get access token"}
        
        import aiohttp
        
        url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/sendMail"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        original_question = kwargs.get('original_question', 'N/A')
        score_relevancia = kwargs.get('score_relevancia', 'N/A')
        
        # HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #0078d4; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0;">Resposta do Centro de Dúvidas</h2>
                </div>
                <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px;">
                    <div style="background: #f5f5f5; padding: 15px; border-left: 4px solid #0078d4; margin-bottom: 20px;">
                        <strong>Sua Pergunta:</strong>
                        <p style="margin: 10px 0 0 0;">{original_question}</p>
                    </div>
                    <div style="background: #f0f8ff; padding: 15px; border-left: 4px solid #107c10;">
                        <strong>Resposta:</strong>
                        <p style="margin: 10px 0 0 0;">{body}</p>
                    </div>
                    <hr style="margin: 20px 0; border-color: #ddd;">
                    <p style="color: #666; font-size: 12px;">
                        Este é um email automático. Não responda diretamente a esta mensagem.<br>
                        Score de relevância: {score_relevancia}%
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "message": {
                "subject": subject or f"Re: {kwargs.get('original_question', 'Sua pergunta')[:50]}...",
                "body": {
                    "contentType": "HTML",
                    "content": html_body
                },
                "toRecipients": [{"emailAddress": {"address": to}}]
            },
            "saveToSentItems": "true"
        }
        
        # Se for resposta a email existente
        if kwargs.get("in_reply_to"):
            payload["message"]["internetMessageHeaders"] = [
                {"name": "In-Reply-To", "value": kwargs["in_reply_to"]},
                {"name": "References", "value": kwargs["in_reply_to"]}
            ]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 202:
                        logger.info(f"Outlook email sent to {to}")
                        return {"success": True, "message_id": "sent"}
                    else:
                        error = await response.json()
                        logger.error(f"Outlook send error: {error}")
                        return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Outlook send exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def fetch_email(self, message_id: str) -> Optional[Dict]:
        """Busca detalhes de um email específico"""
        token = await self._get_access_token()
        if not token:
            return None
        
        import aiohttp
        
        url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/messages/{message_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Fetch email error: {e}")
            return None
    
    async def list_unread_emails(self, folder: str = "inbox", top: int = 50) -> list:
        """Lista emails não lidos"""
        token = await self._get_access_token()
        if not token:
            return []
        
        import aiohttp
        
        url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/mailFolders/{folder}/messages"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "$filter": "isRead eq false",
            "$top": top,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,bodyPreview,hasAttachments"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("value", [])
                    return []
        except Exception as e:
            logger.error(f"List emails error: {e}")
            return []
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Marca email como lido"""
        token = await self._get_access_token()
        if not token:
            return False
        
        import aiohttp
        
        url = f"https://graph.microsoft.com/v1.0/users/{self.user_email}/messages/{message_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"isRead": True}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=payload, headers=headers) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Mark read error: {e}")
            return False
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Valida formato de email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, recipient))
    
    async def create_subscription(self, notification_url: str, expiration_minutes: int = 60) -> Dict[str, Any]:
        """Cria subscription para receber notificações de novos emails (webhook)"""
        token = await self._get_access_token()
        if not token:
            return {"success": False, "error": "No access token"}
        
        import aiohttp
        from datetime import datetime, timedelta
        
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        
        payload = {
            "changeType": "created",
            "notificationUrl": notification_url,
            "resource": f"users/{self.user_email}/mailFolders('inbox')/messages",
            "expirationDateTime": expiration.isoformat() + "Z",
            "clientState": "sistemarag_webhook_secret"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        logger.info(f"Outlook subscription created: {data.get('id')}")
                        return {"success": True, "subscription": data}
                    else:
                        error = await response.json()
                        return {"success": False, "error": error}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============================================
# SMTP EMAIL ADAPTER
# ============================================

class SMTPEmailAdapter(ChannelAdapter):
    """Adapter para envio de email via SMTP"""
    
    def __init__(self):
        self.server = SMTP_SERVER
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.sender = SENDER_EMAIL
    
    @property
    def channel_name(self) -> str:
        return "email_smtp"
    
    async def send_message(self, to: str, body: str, subject: str = None, **kwargs) -> Dict[str, Any]:
        if not all([self.server, self.port, self.user, self.password]):
            return {"success": False, "error": "SMTP not configured"}
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #2c3e50; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
                    <h2 style="margin: 0;">Resposta do Centro de Dúvidas</h2>
                </div>
                <div style="padding: 20px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px;">
                    <div style="background: #ecf0f1; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px;">
                        <strong>Sua Pergunta:</strong>
                        <p style="margin: 10px 0 0 0;">{kwargs.get('original_question', 'N/A')}</p>
                    </div>
                    <div style="background: #e8f8f5; padding: 15px; border-left: 4px solid #27ae60;">
                        <strong>Resposta:</strong>
                        <p style="margin: 10px 0 0 0;">{body}</p>
                    </div>
                    <hr style="margin: 20px 0; border-color: #ddd;">
                    <p style="color: #95a5a6; font-size: 12px;">
                        Este é um email automático. Não responda diretamente a esta mensagem.<br>
                        Score de relevância: {kwargs.get('score_relevancia', 'N/A')}%
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject or f"Re: {kwargs.get('original_question', 'Sua pergunta')[:50]}..."
        msg["From"] = self.sender
        msg["To"] = to
        
        if kwargs.get("in_reply_to"):
            msg["In-Reply-To"] = kwargs["in_reply_to"]
            msg["References"] = kwargs["in_reply_to"]
        
        # Texto plano
        text_body = f"Resposta do Centro de Dúvidas\n\nPergunta: {kwargs.get('original_question', 'N/A')}\n\nResposta: {body}\n\n---\nEste é um email automático."
        
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        
        try:
            # Usar thread pool para operação síncrona
            await asyncio.to_thread(self._send_smtp, to, msg)
            
            logger.info(f"SMTP email sent to {to}")
            return {"success": True}
        except Exception as e:
            logger.error(f"SMTP send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_smtp(self, to: str, msg):
        """Envia email via SMTP (síncrono)"""
        if not self.user or not self.password:
            raise ValueError("SMTP credentials not configured")
        with smtplib.SMTP(self.server, self.port) as server:
            server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)
    
    async def validate_recipient(self, recipient: str) -> bool:
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, recipient))


# ============================================
# FACTORY
# ============================================

class AdapterFactory:
    """Factory para criar adaptadores de canal"""
    
    _adapters = {}
    
    @classmethod
    def get_adapter(cls, channel: str) -> ChannelAdapter:
        """Retorna instância do adapter para o canal"""
        channel = channel.lower()
        
        if channel not in cls._adapters:
            if channel in ["whatsapp", "whatsapp_twilio", "twilio"]:
                cls._adapters[channel] = TwilioWhatsAppAdapter()
            elif channel in ["whatsapp_meta", "meta", "cloud_api"]:
                cls._adapters[channel] = MetaWhatsAppAdapter()
            elif channel in ["outlook", "microsoft_graph", "graph"]:
                cls._adapters[channel] = OutlookAdapter()
            elif channel in ["email", "smtp", "email_smtp"]:
                cls._adapters[channel] = SMTPEmailAdapter()
            else:
                logger.warning(f"Unknown channel: {channel}, defaulting to email")
                cls._adapters[channel] = SMTPEmailAdapter()
        
        return cls._adapters[channel]
    
    @classmethod
    def register_adapter(cls, channel: str, adapter: ChannelAdapter):
        """Registra um novo adapter"""
        cls._adapters[channel.lower()] = adapter


# Instâncias globais para compatibilidade
twilio_client = TwilioWhatsAppAdapter()
email_client = SMTPEmailAdapter()
meta_whatsapp_client = MetaWhatsAppAdapter()
outlook_client = OutlookAdapter()