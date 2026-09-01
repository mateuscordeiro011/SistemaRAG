# ============================================
# SQLALCHEMY MODELS
# ============================================
# Define todas as tabelas como classes Python
# Sincronizado com schema.sql

from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    Float, ForeignKey, Index, LargeBinary, JSON, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Cliente(Base):
    """
    Representa um cliente/empresa que utiliza o sistema RAG.
    Funciona como um tenant em arquitetura multi-tenant.
    """
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    nome = Column(String(255), unique=True, nullable=False)
    empresa = Column(String(255), nullable=False)
    descricao = Column(Text)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documentos = relationship("Documento", back_populates="cliente", cascade="all, delete-orphan")
    mensagens = relationship("MensagemAtendimento", back_populates="cliente", cascade="all, delete-orphan")
    estatisticas = relationship("Estatistica", back_populates="cliente", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Cliente {self.nome} ({self.empresa})>"


class Documento(Base):
    """
    Representa um arquivo de conhecimento enviado por um cliente.
    Armazena metadados, conteúdo e status de processamento.
    Suporta multimodalidade: além de texto, pode conter imagens e diagramas.
    """
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    nome_arquivo = Column(String(255), nullable=False)
    tipo_arquivo = Column(String(50), nullable=False)  # PDF, DOCX, XLSX, TXT
    caminho_arquivo = Column(String(500), nullable=False)
    tamanho_bytes = Column(Integer)
    hash_arquivo = Column(String(255), unique=True)  # SHA-256 para evitar duplicatas
    conteudo_texto = Column(LONGTEXT)
    total_chunks = Column(Integer, default=0)
    total_embeddings = Column(Integer, default=0)
    
    # MULTIMODALIDADE: Campos para suporte a imagens
    contem_imagens = Column(Boolean, default=False)  # Flag se contém imagens/diagramas
    total_imagens = Column(Integer, default=0)  # Contador de imagens extraídas
    metadata_midia = Column(JSON)  # Metadados sobre mídia no documento
    
    status = Column(String(50), default="PROCESSANDO")  # PROCESSANDO, SUCESSO, ERRO
    mensagem_erro = Column(Text)
    data_upload = Column(DateTime, default=datetime.utcnow)
    data_processamento = Column(DateTime)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cliente = relationship("Cliente", back_populates="documentos")
    chunks = relationship("Chunk", back_populates="documento", cascade="all, delete-orphan")
    midias = relationship("MidiaDocumento", back_populates="documento", cascade="all, delete-orphan")

    # Índices
    __table_args__ = (
        Index("idx_cliente_id", "cliente_id"),
        Index("idx_status", "status"),
        Index("idx_hash_arquivo", "hash_arquivo"),
        Index("idx_contem_imagens", "contem_imagens"),
    )

    def __repr__(self):
        return f"<Documento {self.nome_arquivo} ({self.status})>"


class Chunk(Base):
    """
    Fragmento de um documento processado para RAG.
    Cada documento é dividido em múltiplos chunks com overlap.
    """
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True)
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=False)
    numero_chunk = Column(Integer, nullable=False)
    conteudo = Column(Text, nullable=False)
    tamanho_caracteres = Column(Integer)
    pagina = Column(Integer)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relationships
    documento = relationship("Documento", back_populates="chunks")
    embedding = relationship("Embedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")

    # Índices
    __table_args__ = (
        Index("idx_documento_id", "documento_id"),
        Index("idx_numero_chunk", "numero_chunk"),
    )

    def __repr__(self):
        return f"<Chunk {self.documento_id}#{self.numero_chunk}>"


class MidiaDocumento(Base):
    """
    Armazena referências a imagens, diagramas, tabelas e gráficos extraídos de documentos.
    Parte da estratégia multimodal do sistema RAG.
    Cada mídia pode ser sugerida junto com respostas de IA quando visualmente relevante.
    """
    __tablename__ = "midia_documentos"

    id = Column(Integer, primary_key=True)
    documento_id = Column(Integer, ForeignKey("documentos.id"), nullable=False)
    tipo_midia = Column(String(50), nullable=False)  # image, diagram, table, chart, etc
    caminho_arquivo = Column(String(500), nullable=False)  # Caminho relativo ao servidor
    url_publica = Column(String(1000))  # URL acessível externamente (WhatsApp/Outlook)
    nome_arquivo = Column(String(255))
    tamanho_bytes = Column(Integer)
    mime_type = Column(String(100))  # image/png, image/jpeg, etc
    pagina = Column(Integer)  # Página onde foi extraída
    descricao = Column(Text)  # Descrição automática ou manual
    score_relevancia = Column(Numeric(5, 4), default=0)  # Para ordenação de relevância
    data_extracao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documento = relationship("Documento", back_populates="midias")
    mensagens_com_imagem = relationship("MensagemAtendimento", back_populates="imagem_sugerida")

    # Índices
    __table_args__ = (
        Index("idx_documento_id", "documento_id"),
        Index("idx_tipo_midia", "tipo_midia"),
        Index("idx_pagina", "pagina"),
        Index("idx_relevancia", "score_relevancia"),
    )

    def __repr__(self):
        return f"<MidiaDocumento {self.tipo_midia} - {self.nome_arquivo}>"


class Embedding(Base):
    """
    Vetor de embedding de alta dimensão para busca semântica.
    Armazenado como numpy array serializado em BLOB.
    Para máximo desempenho, considere usar pgvector (PostgreSQL).
    """
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), unique=True, nullable=False)
    vetor = Column(LargeBinary, nullable=False)  # numpy array serializado (pickle)
    dimensao = Column(Integer, nullable=False)  # Ex: 1536 para OpenAI
    modelo = Column(String(100), nullable=False)  # Ex: text-embedding-ada-002
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chunk = relationship("Chunk", back_populates="embedding")

    # Índices
    __table_args__ = (
        Index("idx_chunk_id", "chunk_id"),
    )

    def __repr__(self):
        return f"<Embedding chunk_id={self.chunk_id}>"


class Canal(Base):
    """
    Define os canais de comunicação disponíveis (WhatsApp, Outlook, Email, Chat).
    Pré-populado com valores padrão.
    """
    __tablename__ = "canais"

    id = Column(Integer, primary_key=True)
    nome = Column(String(100), unique=True, nullable=False)
    descricao = Column(String(255))
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mensagens = relationship("MensagemAtendimento", back_populates="canal")

    def __repr__(self):
        return f"<Canal {self.nome}>"


class MensagemAtendimento(Base):
    """
    Tabela principal de transações - registra toda interação de atendimento.
    Fluxo de status: RECEBIDA → PROCESSANDO → AGUARDANDO_APROVACAO → APROVADA/REJEITADA → ENVIADA/DESCARTADA
    
    Esta tabela é o núcleo do sistema Human-in-the-Loop com suporte multimodal.
    Permite que respostas incluam imagens, diagramas e anexos quando apropriado.
    """
    __tablename__ = "mensagens_atendimento"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    canal_id = Column(Integer, ForeignKey("canais.id"), nullable=False)
    identificador_externo = Column(String(255))  # WhatsApp ID, Outlook ID, etc

    # ENTRADA (Pergunta)
    pergunta = Column(Text, nullable=False)
    idioma = Column(String(10), default="pt-BR")

    # PROCESSAMENTO RAG
    chunks_recuperados = Column(Integer, default=0)
    score_relevancia = Column(Numeric(5, 4), default=0)  # 0.0 a 1.0
    tempo_processamento_ms = Column(Integer, default=0)

    # RESPOSTA IA (Antes da Aprovação)
    resposta_ia = Column(Text)
    resposta_editada = Column(Text)  # Após edição do operador
    modelo_ia = Column(String(100), default="gpt-3.5-turbo")
    tokens_prompt = Column(Integer, default=0)
    tokens_completion = Column(Integer, default=0)
    custo_api = Column(Numeric(10, 6), default=0)

    # MULTIMODALIDADE: Campos para imagens e anexos
    necessita_visual = Column(Boolean, default=False)  # IA identificou que precisa de visual
    imagem_url = Column(String(1000))  # URL da imagem sugerida pela IA
    imagem_sugerida_id = Column(Integer, ForeignKey("midia_documentos.id", ondelete="SET NULL"))
    imagem_aprovada = Column(Boolean, default=False)  # Operador aprovou a imagem
    anexos_gerados = Column(JSON)  # Array de anexos aprovados: [{url: "...", tipo: "image", descricao: "..."}]

    # APROVAÇÃO HUMANA
    status = Column(String(50), default="RECEBIDA")
    operador_id = Column(Integer, ForeignKey("usuarios.id"))
    motivo_rejeicao = Column(String(500))
    data_aprovacao = Column(DateTime)

    # FEEDBACK & ANÁLISE
    feedback_usuario = Column(String(500))
    score_satisfacao = Column(Integer, default=0)  # 1-5

    # TIMESTAMPS
    data_recebimento = Column(DateTime, default=datetime.utcnow)
    data_processamento = Column(DateTime)
    data_envio = Column(DateTime)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cliente = relationship("Cliente", back_populates="mensagens")
    canal = relationship("Canal", back_populates="mensagens")
    operador = relationship("Usuario", back_populates="mensagens")
    auditorias = relationship("Auditoria", back_populates="mensagem", cascade="all, delete-orphan")
    imagem_sugerida = relationship("MidiaDocumento", back_populates="mensagens_com_imagem")

    # Índices
    __table_args__ = (
        Index("idx_cliente_id", "cliente_id"),
        Index("idx_status", "status"),
        Index("idx_data_recebimento", "data_recebimento"),
        Index("idx_identificador_externo", "identificador_externo"),
        Index("idx_operador_id", "operador_id"),
        Index("idx_necessita_visual", "necessita_visual"),
    )

    def __repr__(self):
        return f"<MensagemAtendimento {self.id} ({self.status})>"


class Auditoria(Base):
    """
    Log de auditoria completo de todas as ações no sistema.
    Rastreia mudanças, aprovações, rejeições e envios.
    """
    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True)
    mensagem_atendimento_id = Column(Integer, ForeignKey("mensagens_atendimento.id"))
    acao = Column(String(100), nullable=False)  # CRIAÇÃO, EDIÇÃO, APROVAÇÃO, REJEIÇÃO, ENVIO
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    descricao = Column(Text)
    dados_anteriores = Column(JSON)
    dados_novos = Column(JSON)
    data_acao = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mensagem = relationship("MensagemAtendimento", back_populates="auditorias")
    usuario = relationship("Usuario")

    # Índices
    __table_args__ = (
        Index("idx_mensagem_id", "mensagem_atendimento_id"),
        Index("idx_data_acao", "data_acao"),
    )

    def __repr__(self):
        return f"<Auditoria {self.acao} @ {self.data_acao}>"


class Usuario(Base):
    """
    Usuário do sistema com papéis de controle de acesso.
    Papéis: admin, supervisor, operador.
    """
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(255))
    papel = Column(String(50), default="operador")  # admin, supervisor, operador
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    ultimo_login = Column(DateTime)

    # Relationships
    mensagens = relationship("MensagemAtendimento", back_populates="operador")

    # Índices
    __table_args__ = (
        Index("idx_username", "username"),
        Index("idx_papel", "papel"),
    )

    def __repr__(self):
        return f"<Usuario {self.username} ({self.papel})>"


class Estatistica(Base):
    """
    Estatísticas pré-computadas por cliente/data para otimizar queries do dashboard.
    Atualizado periodicamente por um job assíncrono.
    """
    __tablename__ = "estatisticas"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    data = Column(DateTime, nullable=False)
    total_mensagens = Column(Integer, default=0)
    mensagens_aprovadas = Column(Integer, default=0)
    mensagens_rejeitadas = Column(Integer, default=0)
    tempo_medio_processamento_ms = Column(Integer, default=0)
    score_satisfacao_medio = Column(Numeric(3, 2), default=0)
    total_tokens_utilisados = Column(Integer, default=0)
    custo_total_api = Column(Numeric(10, 6), default=0)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cliente = relationship("Cliente", back_populates="estatisticas")

    # Índices
    __table_args__ = (
        Index("idx_cliente_data", "cliente_id", "data"),
    )

    def __repr__(self):
        return f"<Estatistica {self.cliente_id} @ {self.data}>"


# ============================================
# PYDANTIC SCHEMAS (Para validação de API)
# ============================================
from pydantic import BaseModel, Field
from typing import Optional


class ClienteCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    empresa: str = Field(..., min_length=1, max_length=255)
    descricao: Optional[str] = None


class ClienteResponse(ClienteCreate):
    id: int
    ativo: bool
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        from_attributes = True


class MensagemCreate(BaseModel):
    cliente_id: int
    canal_id: int
    pergunta: str = Field(..., min_length=1)
    idioma: str = "pt-BR"
    identificador_externo: Optional[str] = None


class MensagemResponse(BaseModel):
    id: int
    cliente_id: int
    canal_id: int
    pergunta: str
    resposta_ia: Optional[str]
    resposta_editada: Optional[str]
    status: str
    score_relevancia: float
    chunks_recuperados: int
    tempo_processamento_ms: int
    score_satisfacao: int
    data_recebimento: datetime
    data_aprovacao: Optional[datetime]
    data_envio: Optional[datetime]

    class Config:
        from_attributes = True


class MensagemAprovacao(BaseModel):
    resposta_editada: Optional[str] = None
    aprovada: bool
    motivo_rejeicao: Optional[str] = None
    operador_id: int


class MensagemFeedback(BaseModel):
    score_satisfacao: int = Field(..., ge=1, le=5)
    feedback_usuario: Optional[str] = None


# ============================================
# SCHEMAS MULTIMODAIS
# ============================================

class AnexoResponse(BaseModel):
    """Resposta com informações sobre um anexo (imagem, documento, etc)"""
    url: str
    tipo: str  # image, document, etc
    descricao: Optional[str] = None
    tamanho_bytes: Optional[int] = None
    mime_type: Optional[str] = None


class MidiaDocumentoResponse(BaseModel):
    """Resposta sobre mídia extraída de documentos"""
    id: int
    documento_id: int
    tipo_midia: str
    url_publica: Optional[str] = None
    nome_arquivo: Optional[str] = None
    descricao: Optional[str] = None
    score_relevancia: float
    pagina: Optional[int] = None
    data_extracao: datetime

    class Config:
        from_attributes = True


class MensagemRespostaComImagem(BaseModel):
    """Resposta da IA com suporte a imagens/anexos multimodais"""
    id: int
    cliente_id: int
    pergunta: str
    resposta_ia: Optional[str]
    status: str
    necessita_visual: bool
    imagem_url: Optional[str] = None
    imagem_sugerida: Optional[MidiaDocumentoResponse] = None
    imagem_aprovada: bool = False
    anexos_gerados: Optional[List[AnexoResponse]] = None
    score_relevancia: float
    chunks_recuperados: int
    tempo_processamento_ms: int
    data_recebimento: datetime

    class Config:
        from_attributes = True


class MensagemAprovacaoComImagens(BaseModel):
    """Payload para aprovar mensagem com imagens/anexos opcionais"""
    resposta_editada: Optional[str] = None
    aprovada: bool
    motivo_rejeicao: Optional[str] = None
    operador_id: int
    imagem_aprovada: bool = False  # Operador aprovou a imagem sugerida
    anexos_aprovados: Optional[List[AnexoResponse]] = None  # Lista de anexos que devem ser inclusos
