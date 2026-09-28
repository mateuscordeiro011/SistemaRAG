"""
Adapters de Canais para SistemaRAG
Padrão Strategy para desacoplar envio via diferentes canais
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional
import logging
from datetime import datetime

from sqlalchemy.orm import Session
from models import MensagemAtendimento

logger = logging.getLogger(__name__)


class CanalEnum(str, Enum):
    """Canais disponíveis"""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WEB = "web"
    TESTE = "teste"


class MensagemEnvelopeDTO:
    """
    Envelope padrão para transporte de mensagens
    Desacopla o modelo de transporte do canal específico
    """
    def __init__(
        self,
        canal: CanalEnum,
        cliente_id: str,
        pergunta: str,
        usuario_id: Optional[str] = None,
        metadata: dict = None,
    ):
        self.canal = canal
        self.cliente_id = cliente_id
        self.pergunta = pergunta
        self.usuario_id = usuario_id
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class CanalAdapter(ABC):
    """Interface abstrata para adaptadores de canal"""
    
    @abstractmethod
    async def enviar(
        self,
        mensagem: MensagemAtendimento,
        db: Session
    ) -> bool:
        """
        Envia mensagem através do canal
        
        Args:
            mensagem: Objeto MensagemAtendimento com resposta
            db: Sessão do banco de dados
        
        Returns:
            True se enviada com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def validar_destinatario(self, cliente_id: str) -> bool:
        """
        Valida se o destinatário é válido para este canal
        
        Args:
            cliente_id: ID/contato do cliente
        
        Returns:
            True se válido, False caso contrário
        """
        pass


class WhatsAppAdapter(CanalAdapter):
    """Adapter para envio via WhatsApp (Twilio)"""
    
    def __init__(self):
        from integrations import twilio_client
        self.twilio = twilio_client
    
    async def enviar(
        self,
        mensagem: MensagemAtendimento,
        db: Session
    ) -> bool:
        """Envia via Twilio WhatsApp"""
        try:
            # Validar resposta
            if not mensagem.resposta or len(mensagem.resposta) == 0:
                logger.error(f"Mensagem {mensagem.id} sem resposta")
                return False
            
            # WhatsApp limita a 1600 caracteres
            resposta_truncada = mensagem.resposta[:1600]
            
            # Enviar
            resultado = await self.twilio.send_message(
                to=f"whatsapp:{mensagem.cliente_id}",
                body=resposta_truncada
            )
            
            # Atualizar status
            mensagem.status = "ENVIADA_AUTOMATICA"
            mensagem.enviado_em = datetime.utcnow()
            db.add(mensagem)
            db.commit()
            
            logger.info(
                f"Mensagem {mensagem.id} enviada via WhatsApp - "
                f"Message SID: {resultado.sid}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp para {mensagem.id}: {e}")
            
            # Atualizar tentativa
            mensagem.tentativas_envio += 1
            mensagem.ultima_tentativa = datetime.utcnow()
            
            if mensagem.tentativas_envio >= 3:
                mensagem.status = "ERRO_ENVIO"
            
            db.add(mensagem)
            db.commit()
            
            return False
    
    async def validar_destinatario(self, cliente_id: str) -> bool:
        """Valida se é um número de WhatsApp válido"""
        # Cliente_id deve estar no formato +55XXXXXXXXXX
        import re
        padrao = r'^\+\d{10,15}$'
        return bool(re.match(padrao, cliente_id))


class EmailAdapter(CanalAdapter):
    """Adapter para envio via Email (SMTP)"""
    
    def __init__(self):
        from integrations import email_client
        self.email = email_client
    
    async def enviar(
        self,
        mensagem: MensagemAtendimento,
        db: Session
    ) -> bool:
        """Envia via SMTP"""
        try:
            # Validar resposta
            if not mensagem.resposta or len(mensagem.resposta) == 0:
                logger.error(f"Mensagem {mensagem.id} sem resposta")
                return False
            
            # Extrair resumo da pergunta para assunto
            pergunta_resumida = mensagem.pergunta[:50]
            
            # Construir corpo do email em HTML
            corpo_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #007bff; color: white; padding: 20px; border-radius: 5px; }}
                    .content {{ margin: 20px 0; line-height: 1.6; }}
                    .pergunta {{ background: #f5f5f5; padding: 15px; border-left: 4px solid #007bff; }}
                    .resposta {{ background: #f0f8ff; padding: 15px; border-left: 4px solid #28a745; }}
                    .footer {{ color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Resposta do Centro de Dúvidas</h2>
                    </div>
                    <div class="content">
                        <div class="pergunta">
                            <strong>Sua Pergunta:</strong>
                            <p>{mensagem.pergunta}</p>
                        </div>
                        
                        <div class="resposta">
                            <strong>Resposta:</strong>
                            <p>{mensagem.resposta}</p>
                        </div>
                        
                        <div class="footer">
                            <p>Obrigado por usar nosso Centro de Dúvidas!<br/>
                            Este é um email automático. Não responda diretamente.</p>
                            <p>Score de relevância: {mensagem.score_relevancia:.2%}</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Enviar
            resultado = await self.email.send(
                to=mensagem.cliente_id,
                subject=f"Re: {pergunta_resumida}...",
                html=corpo_html
            )
            
            # Atualizar status
            mensagem.status = "ENVIADA_AUTOMATICA"
            mensagem.enviado_em = datetime.utcnow()
            db.add(mensagem)
            db.commit()
            
            logger.info(
                f"Mensagem {mensagem.id} enviada via Email para "
                f"{mensagem.cliente_id}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar Email para {mensagem.id}: {e}")
            
            # Atualizar tentativa
            mensagem.tentativas_envio += 1
            mensagem.ultima_tentativa = datetime.utcnow()
            
            if mensagem.tentativas_envio >= 3:
                mensagem.status = "ERRO_ENVIO"
            
            db.add(mensagem)
            db.commit()
            
            return False
    
    async def validar_destinatario(self, cliente_id: str) -> bool:
        """Valida se é um email válido"""
        import re
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(padrao, cliente_id))


class WebAdapter(CanalAdapter):
    """Adapter para respostas na web (armazenadas no banco)"""
    
    async def enviar(
        self,
        mensagem: MensagemAtendimento,
        db: Session
    ) -> bool:
        """Marca como enviada (é apresentada via API web)"""
        try:
            mensagem.status = "ENVIADA_AUTOMATICA"
            mensagem.enviado_em = datetime.utcnow()
            db.add(mensagem)
            db.commit()
            
            logger.info(f"Mensagem {mensagem.id} marcada como disponível na web")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao marcar mensagem {mensagem.id}: {e}")
            return False
    
    async def validar_destinatario(self, cliente_id: str) -> bool:
        """Web não precisa validar (sempre válido)"""
        return True


class TesteAdapter(CanalAdapter):
    """Adapter para testes (apenas loga)"""
    
    async def enviar(
        self,
        mensagem: MensagemAtendimento,
        db: Session
    ) -> bool:
        """Simula envio para testes"""
        try:
            logger.info(
                f"[TESTE] Mensagem {mensagem.id} enviada para "
                f"{mensagem.cliente_id}: {mensagem.resposta[:100]}"
            )
            
            mensagem.status = "ENVIADA_AUTOMATICA"
            mensagem.enviado_em = datetime.utcnow()
            db.add(mensagem)
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Erro teste para {mensagem.id}: {e}")
            return False
    
    async def validar_destinatario(self, cliente_id: str) -> bool:
        """Teste aceita qualquer valor"""
        return True


class AdapterFactory:
    """
    Factory para criar adaptadores de canal
    Implementa padrão Factory Method
    """
    
    _adapters = {
        CanalEnum.WHATSAPP: WhatsAppAdapter(),
        CanalEnum.EMAIL: EmailAdapter(),
        CanalEnum.WEB: WebAdapter(),
        CanalEnum.TESTE: TesteAdapter(),
    }
    
    @classmethod
    def criar(cls, canal: str) -> CanalAdapter:
        """
        Cria adaptador para um canal
        
        Args:
            canal: Nome do canal (string ou enum)
        
        Returns:
            Instância do adapter apropriado
        
        Raises:
            ValueError se canal não for suportado
        """
        try:
            enum_canal = CanalEnum(canal.lower())
        except ValueError:
            logger.warning(f"Canal desconhecido: {canal}, usando padrão")
            return cls._adapters[CanalEnum.WEB]
        
        return cls._adapters.get(enum_canal, cls._adapters[CanalEnum.WEB])
    
    @classmethod
    def registrar(cls, canal: CanalEnum, adapter: CanalAdapter):
        """
        Registra um novo adapter (para extensibilidade)
        
        Args:
            canal: CanalEnum
            adapter: Instância do adapter
        """
        cls._adapters[canal] = adapter
        logger.info(f"Adapter registrado para canal {canal.value}")