"""
Modelos SQLAlchemy e DTOs para SistemaRAG
Define estrutura do banco de dados e schemas de validação
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, LONGBLOB, Enum, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()


# ============================================
# MODELOS SQLAlchemy (Banco de Dados)
# ============================================

class Cliente(Base):
    """Modelo de cliente do sistema"""
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nome_cliente = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255))
    telefone = Column(String(20))
    data_criacao = Column(DateTime, default=datetime.utcnow)
    ativo = Column(Boolean, default=True, index=True)
    
    # Relacionamentos
    usuarios = relationship("Usuario", back_populates="cliente", cascade="all, delete-orphan")
    documentos = relationship("MidiaDocumento", back_populates="cliente", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="cliente", cascade="all, delete-orphan")
    mensagens = relationship("MensagemAtendimento", back_populates="cliente", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="cliente", cascade="all, delete-orphan")
    configuracoes = relationship("Configuracao", back_populates="cliente", uselist=False, cascade="all, delete-orphan")


class Usuario(Base):
    """Modelo de usuário/operador"""
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    senha_hash = Column(String(255), nullable=False)
    papel = Column(String(20), default="operador", index=True)  # admin, operador, leitor
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="usuarios")
    mensagens = relationship("MensagemAtendimento", back_populates="usuario")


class MidiaDocumento(Base):
    """Modelo de documento/arquivo enviado"""
    __tablename__ = "midia_documentos"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    nome_original = Column(String(255), nullable=False)
    nome_armazenado = Column(String(255), nullable=False)
    caminho_arquivo = Column(String(500))
    tipo_documento = Column(String(20), default="outro")  # pdf, docx, txt, md
    tamanho_bytes = Column(Integer)
    status = Column(String(20), default="ENVIADO", index=True)  # ENVIADO, PROCESSANDO, INDEXADO, ERRO
    mensagem_erro = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow, index=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deletado = Column(Boolean, default=False)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="documentos")
    chunks = relationship("Chunk", back_populates="documento", cascade="all, delete-orphan")


class Chunk(Base):
    """Modelo de pedaço de documento (chunk)"""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    midia_documento_id = Column(Integer, ForeignKey("midia_documentos.id"), nullable=False, index=True)
    numero_pagina = Column(Integer)
    conteudo_texto = Column(Text, nullable=False)
    embedding_vector = Column(LONGBLOB)  # Armazena embedding em binário (float32)
    tamanho_token = Column(Integer)
    hash_conteudo = Column(String(64), index=True)  # SHA256
    criado_em = Column(DateTime, default=datetime.utcnow)
    deletado = Column(Boolean, default=False, index=True)
    
    # Índices
    __table_args__ = (
        Index('idx_cliente_deletado', 'cliente_id', 'deletado'),
        Index('idx_documento_deletado', 'midia_documento_id', 'deletado'),
    )
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="chunks")
    documento = relationship("MidiaDocumento", back_populates="chunks")
    respostas_chunks = relationship("RespostaChunk", back_populates="chunk", cascade="all, delete-orphan")


class MensagemAtendimento(Base):
    """Modelo de mensagem/pergunta recebida"""
    __tablename__ = "mensagens_atendimento"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    pergunta = Column(Text, nullable=False)
    resposta = Column(Text)
    canal = Column(String(20), default="web", index=True)  # whatsapp, email, web, teste
    status = Column(String(30), default="RECEBIDA", index=True)  # RECEBIDA, PROCESSANDO_RAG, AGUARDANDO_APROVACAO, ENVIADA_AUTOMATICA, ENVIADA_MANUAL, REJEITADA, ERRO_ENVIO
    score_relevancia = Column(Float, index=True)
    requer_aprovacao = Column(Boolean, default=True)
    motivo_rejeicao = Column(Text)
    tentativas_envio = Column(Integer, default=0)
    ultima_tentativa = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, index=True)
    processado_em = Column(DateTime, nullable=True)
    enviado_em = Column(DateTime, nullable=True)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="mensagens")
    usuario = relationship("Usuario", back_populates="mensagens")
    chunks_consultados = relationship("RespostaChunk", back_populates="mensagem", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="mensagem", cascade="all, delete-orphan")


class RespostaChunk(Base):
    """
    ✅ NOVO - Tabela de rastreabilidade
    Armazena quais chunks foram usados em cada resposta
    Permite rastrear as fontes consultadas
    """
    __tablename__ = "resposta_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    mensagem_id = Column(Integer, ForeignKey("mensagens_atendimento.id"), nullable=False, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False, index=True)
    relevancia_score = Column(Float, nullable=False, index=True)
    posicao = Column(Integer, nullable=False)  # Ordem de uso (1º, 2º, 3º)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    mensagem = relationship("MensagemAtendimento", back_populates="chunks_consultados")
    chunk = relationship("Chunk", back_populates="respostas_chunks")


class Log(Base):
    """Modelo de log do sistema"""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    mensagem_id = Column(Integer, ForeignKey("mensagens_atendimento.id"), nullable=True)
    tipo = Column(String(20), default="INFO", index=True)  # INFO, WARN, ERROR, DEBUG
    descricao = Column(Text)
    dados_json = Column(JSON)
    origem = Column(String(255))  # Endpoint ou função
    ip_origem = Column(String(45))  # IPv4 ou IPv6
    criado_em = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="logs")
    mensagem = relationship("MensagemAtendimento", back_populates="logs")


class Configuracao(Base):
    """Modelo de configurações por cliente"""
    __tablename__ = "configuracoes"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, unique=True, index=True)
    limiar_confianca = Column(Float, default=0.75)
    max_chunks_resposta = Column(Integer, default=5)
    modelo_embedding = Column(String(100), default="sentence-transformers/all-MiniLM-L6-v2")
    modelo_rag = Column(String(100), default="llama2")
    timeout_processamento = Column(Integer, default=30)  # segundos
    max_tentativas_envio = Column(Integer, default=3)
    intervalo_retry_segundos = Column(Integer, default=300)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    cliente = relationship("Cliente", back_populates="configuracoes")


# ============================================
# DTOs Pydantic (Validação e Serialização)
# ============================================

class CanalEnum(str, PyEnum):
    """Canais de comunicação disponíveis"""
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WEB = "web"
    TESTE = "teste"


class ClienteBase(BaseModel):
    """DTO base de cliente"""
    nome_cliente: str = Field(..., min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None


class ClienteCreate(ClienteBase):
    """DTO para criar cliente"""
    pass


class ClienteResponse(ClienteBase):
    """DTO para resposta de cliente"""
    id: int
    data_criacao: datetime
    ativo: bool
    
    class Config:
        from_attributes = True


class MensagemEnvelopeDTO(BaseModel):
    """
    ✅ Envelope padrão para transporte de mensagens
    Desacopla o modelo de transporte do canal específico
    """
    canal: CanalEnum = Field(..., description="Canal de comunicação")
    cliente_id: str = Field(..., description="ID/contato do cliente")
    pergunta: str = Field(..., min_length=1, max_length=5000, description="Pergunta a processar")
    usuario_id: Optional[str] = None
    metadata: dict = {}
    
    class Config:
        use_enum_values = True


class MensagemCreate(BaseModel):
    """DTO para criar mensagem"""
    cliente_id: str
    pergunta: str = Field(..., min_length=1, max_length=5000)
    canal: str = Field(default="web")
    usuario_id: Optional[int] = None


class RespostaChunkResponse(BaseModel):
    """DTO para chunk consultado em uma resposta"""
    id: int
    chunk_id: int
    conteudo_texto: str
    relevancia_score: float
    posicao: int
    pagina: Optional[int] = None
    documento_nome: str
    
    class Config:
        from_attributes = True


class MensagemResponse(BaseModel):
    """DTO para resposta de mensagem"""
    id: int
    cliente_id: str
    pergunta: str
    resposta: Optional[str] = None
    canal: str
    status: str
    score_relevancia: Optional[float] = None
    requer_aprovacao: bool
    criado_em: datetime
    enviado_em: Optional[datetime] = None
    chunks_consultados: Optional[List[RespostaChunkResponse]] = []
    
    class Config:
        from_attributes = True


class MensagemApproveDTO(BaseModel):
    """DTO para aprovar mensagem"""
    resposta: str = Field(..., min_length=1)
    observacoes: Optional[str] = None


class MensagemRejectDTO(BaseModel):
    """DTO para rejeitar mensagem"""
    motivo: str = Field(..., min_length=1)


class DocumentoUploadResponse(BaseModel):
    """DTO para resposta de upload"""
    documento_id: int
    nome: str
    tamanho_bytes: int
    status_url: str
    criado_em: datetime


class ConfiguracaoResponse(BaseModel):
    """DTO para configurações"""
    cliente_id: int
    limiar_confianca: float
    max_chunks_resposta: int
    modelo_embedding: str
    modelo_rag: str
    timeout_processamento: int
    
    class Config:
        from_attributes = True


class EstatisticasResponse(BaseModel):
    """DTO para estatísticas"""
    total_mensagens: int
    enviadas_automaticas: int
    enviadas_manual: int
    aguardando_aprovacao: int
    rejeitadas: int
    score_medio: float
    total_documentos: int
    total_chunks: int


class HealthResponse(BaseModel):
    """DTO para health check"""
    status: str
    timestamp: datetime
    database: Optional[str] = None
    version: str = "1.0.0"


# ============================================
# SCHEMAS PARA PAGINAÇÃO
# ============================================

class PaginationParams(BaseModel):
    """Parâmetros de paginação"""
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: str = Field(default="criado_em")
    order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Resposta paginada genérica"""
    items: List
    total: int
    skip: int
    limit: int
    total_pages: int