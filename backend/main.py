# ============================================
# FASTAPI APPLICATION - MAIN ROUTES
# ============================================

import os
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
from pathlib import Path

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from models import (
    Base, Cliente, Documento, MensagemAtendimento, Auditoria, Usuario,
    ClienteCreate, ClienteResponse, MensagemCreate, MensagemResponse, MensagemAprovacao,
    MensagemFeedback, MidiaDocumento, MensagemAprovacaoComImagens
)
from database import init_db, health_check, get_db, get_db_session
from ingestion import (
    process_document, validate_file, get_document_status, UPLOAD_DIR, ALLOWED_FILE_TYPES
)
from rag_engine import process_query, get_cliente_statistics
from health import perform_full_health_check, get_quick_status

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# FASTAPI APP INITIALIZATION
# ============================================

app = FastAPI(
    title="RAG System API",
    description="Sistema inteligente de atendimento com aprovação humana",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================
# CORS CONFIGURATION
# ============================================

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# LIFESPAN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Executado na inicialização da aplicação."""
    logger.info("=" * 50)
    logger.info("RAG SYSTEM STARTING UP")
    logger.info("=" * 50)
    
    # Inicializar banco de dados
    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        raise
    
    # Verificar saúde do banco de dados
    if health_check():
        logger.info("✓ Database connection healthy")
    else:
        logger.error("✗ Database connection failed")
        raise RuntimeError("Cannot connect to database")
    
    # Criar diretório de uploads
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"✓ Upload directory ready: {UPLOAD_DIR}")
    
    logger.info("=" * 50)
    logger.info("RAG SYSTEM READY")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar a aplicação."""
    logger.info("RAG SYSTEM SHUTTING DOWN")


# ============================================
# HEALTH & STATUS ENDPOINTS
# ============================================

@app.get("/health")
async def health():
    """
    Verifica saúde da API e suas dependências.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "ok" if health_check() else "error",
        "api_version": "1.0.0"
    }


@app.get("/status")
async def status(db: Session = Depends(get_db)):
    """
    Retorna estatísticas gerais do sistema.
    """
    try:
        total_clientes = db.query(Cliente).filter(Cliente.ativo == True).count()
        total_documentos = db.query(Documento).filter(Documento.status == "SUCESSO").count()
        total_mensagens = db.query(MensagemAtendimento).count()
        
        # Fila de aprovação
        fila_aprovacao = db.query(MensagemAtendimento).filter(
            MensagemAtendimento.status == "AGUARDANDO_APROVACAO"
        ).count()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_clientes": total_clientes,
            "total_documentos": total_documentos,
            "total_mensagens": total_mensagens,
            "fila_aprovacao": fila_aprovacao
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# HEALTH CHECK & DIAGNOSTIC ENDPOINTS
# ============================================

@app.get("/api/v1/health/quick-status")
async def quick_health_status():
    """
    Status rápido do sistema (< 1 segundo).
    
    Retorna:
    - database: OK ou ERROR
    - ai_model: OK ou ERROR
    - status: OK, DEGRADED ou ERROR
    """
    try:
        health_data = get_quick_status()
        return health_data
    except Exception as e:
        logger.error(f"Error getting quick status: {e}")
        return {
            "status": "ERROR",
            "database": "ERROR",
            "ai_model": "ERROR",
            "error": str(e)
        }


@app.get("/api/v1/health/full-diagnostic")
async def full_health_diagnostic():
    """
    Diagnóstico completo do sistema (2-5 segundos).
    
    Executa:
    1. Teste de conexão com banco MySQL
    2. Teste de validação de tabelas
    3. Teste de persistência (escrita/leitura/delete)
    4. Teste de conectividade com OpenAI API
    5. Teste de disponibilidade do modelo de IA
    6. Validação do sistema de arquivos
    
    Retorna relatório detalhado com status de cada componente.
    """
    try:
        logger.info("Starting full health diagnostic...")
        health_report = perform_full_health_check()
        return health_report
    except Exception as e:
        logger.error(f"Error in full health diagnostic: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "UNHEALTHY",
            "error": str(e),
            "checks": {}
        }


@app.get("/api/v1/health/db-test")
async def database_persistence_test():
    """
    Teste específico de persistência de dados no MySQL.
    
    Testa o ciclo completo:
    1. ESCRITA: Cria um registro de teste (cliente)
    2. LEITURA: Recupera o registro escrito
    3. AUDITORIA: Registra o teste em auditoria
    4. LIMPEZA: Deleta registros de teste
    
    Valida que todas as mudanças de status (APROVADO, EDITADO, REJEITADO)
    são persistidas corretamente no banco de dados.
    
    Retorna tempos de resposta para cada operação.
    """
    try:
        from health import check_database_read_write
        
        logger.info("Running database persistence test...")
        is_healthy, message, details = check_database_read_write()
        
        return {
            "status": "OK" if is_healthy else "ERROR",
            "message": message,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in database persistence test: {e}")
        return {
            "status": "ERROR",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/v1/health/ai-model-test")
async def ai_model_test():
    """
    Testa disponibilidade e responsividade do modelo de IA.
    
    Executa uma chamada simples ao modelo para validar:
    - Conectividade com OpenAI API
    - Disponibilidade do modelo configurado
    - Tempo de resposta
    """
    try:
        from health import check_openai_model_availability, check_openai_api
        
        logger.info("Running AI model availability test...")
        api_ok, api_msg, api_time = check_openai_api()
        model_ok, model_msg = check_openai_model_availability()
        
        return {
            "api_status": "OK" if api_ok else "ERROR",
            "api_message": api_msg,
            "api_response_time_ms": api_time,
            "model_status": "OK" if model_ok else "ERROR",
            "model_message": model_msg,
            "overall_status": "OK" if (api_ok and model_ok) else "ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in AI model test: {e}")
        return {
            "api_status": "ERROR",
            "model_status": "ERROR",
            "overall_status": "ERROR",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }



# ============================================
# CLIENTE ENDPOINTS
# ============================================

@app.post("/clientes", response_model=ClienteResponse)
async def criar_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db)
):
    """
    Cria um novo cliente/empresa.
    
    Multi-tenant: cada cliente tem seus próprios documentos e mensagens.
    """
    try:
        # Verificar se cliente já existe
        existing = db.query(Cliente).filter(Cliente.nome == cliente.nome).first()
        if existing:
            raise HTTPException(status_code=400, detail="Cliente já existe")
        
        novo_cliente = Cliente(
            nome=cliente.nome,
            empresa=cliente.empresa,
            descricao=cliente.descricao,
            ativo=True
        )
        db.add(novo_cliente)
        db.commit()
        db.refresh(novo_cliente)
        
        logger.info(f"Novo cliente criado: {novo_cliente.nome}")
        
        return novo_cliente
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating client: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clientes/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna informações de um cliente específico.
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return cliente


@app.get("/clientes")
async def listar_clientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Lista todos os clientes ativos.
    """
    total = db.query(Cliente).filter(Cliente.ativo == True).count()
    clientes = db.query(Cliente).filter(
        Cliente.ativo == True
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "clientes": clientes
    }


@app.get("/clientes/{cliente_id}/statistics")
async def estatisticas_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna estatísticas de um cliente (documentos, mensagens, scores).
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    stats = get_cliente_statistics(db, cliente_id)
    
    return {
        "cliente": {
            "id": cliente.id,
            "nome": cliente.nome,
            "empresa": cliente.empresa
        },
        "estatisticas": stats
    }


# ============================================
# DOCUMENT UPLOAD & PROCESSING
# ============================================

@app.post("/documentos/upload")
async def upload_documento(
    cliente_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload de arquivo de conhecimento com processamento assíncrono.
    
    Workflow:
    1. Validação de arquivo
    2. Salvamento em disco
    3. Processamento em background (extração, chunks, embeddings)
    4. Atualização de status no BD
    """
    
    try:
        # Verificar cliente
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Validar arquivo
        is_valid, error_msg = validate_file(file.filename, file.size)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Salvar arquivo em disco
        file_ext = file.filename.split(".")[-1].lower()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{cliente_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"File uploaded: {safe_filename} ({len(contents)} bytes)")
        
        # Iniciar processamento em background
        background_tasks.add_task(
            process_document,
            cliente_id=cliente_id,
            file_path=file_path,
            filename=file.filename,
            file_type=file_ext
        )
        
        return {
            "mensagem": "Arquivo recebido. Processamento iniciado.",
            "arquivo": file.filename,
            "tamanho_bytes": len(contents),
            "status": "processando"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documentos/{documento_id}/status")
async def status_documento(
    documento_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna status de processamento de um documento.
    """
    try:
        status_info = get_document_status(documento_id)
        if "erro" in status_info:
            raise HTTPException(status_code=404, detail=status_info["erro"])
        return status_info
    except Exception as e:
        logger.error(f"Error getting document status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documentos/cliente/{cliente_id}")
async def listar_documentos_cliente(
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """
    Lista documentos processados de um cliente.
    """
    documentos = db.query(Documento).filter(
        Documento.cliente_id == cliente_id
    ).order_by(desc(Documento.data_upload)).all()
    
    return {
        "cliente_id": cliente_id,
        "total": len(documentos),
        "documentos": [
            {
                "id": doc.id,
                "nome": doc.nome_arquivo,
                "tipo": doc.tipo_arquivo,
                "status": doc.status,
                "total_chunks": doc.total_chunks,
                "tamanho_bytes": doc.tamanho_bytes,
                "data_upload": doc.data_upload.isoformat(),
                "data_processamento": doc.data_processamento.isoformat() if doc.data_processamento else None
            }
            for doc in documentos
        ]
    }


# ============================================
# MAIN RAG ENDPOINTS
# ============================================

@app.post("/mensagens/processar")
async def processar_pergunta(
    cliente_id: int,
    pergunta: str,
    canal_id: int = 1,
    identificador_externo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Processa uma pergunta através do pipeline RAG.
    
    Pipeline:
    1. Validar cliente e canal
    2. Gerar embedding da pergunta
    3. Buscar chunks similares
    4. Construir contexto
    5. Gerar resposta com IA
    6. Salvar com status AGUARDANDO_APROVACAO
    """
    
    try:
        # Validar cliente
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # Validar pergunta
        if not pergunta or len(pergunta.strip()) < 5:
            raise HTTPException(status_code=400, detail="Pergunta muito curta")
        
        logger.info(f"Processing query for cliente {cliente_id}: {pergunta[:50]}")
        
        # Executar pipeline RAG
        resultado = process_query(db, cliente_id, pergunta, canal_id)
        
        if resultado["sucesso"]:
            return {
                "sucesso": True,
                "mensagem_id": resultado["mensagem_id"],
                "resposta": resultado["resposta"],
                "status": "AGUARDANDO_APROVACAO",
                "chunks_recuperados": resultado["chunks_recuperados"],
                "score_relevancia": resultado["score_relevancia"],
                "tempo_processamento_ms": resultado["tempo_processamento_ms"],
                "custo_api": resultado["custo_api"]
            }
        else:
            return {
                "sucesso": False,
                "resposta": resultado["resposta"],
                "tempo_processamento_ms": resultado["tempo_processamento_ms"]
            }
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# APPROVAL QUEUE (Human-in-the-Loop)
# ============================================

@app.get("/fila-aprovacao")
async def fila_aprovacao(
    cliente_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retorna fila de mensagens aguardando aprovação.
    Essencial para o painel do operador.
    """
    query = db.query(MensagemAtendimento).filter(
        MensagemAtendimento.status == "AGUARDANDO_APROVACAO"
    )
    
    if cliente_id:
        query = query.filter(MensagemAtendimento.cliente_id == cliente_id)
    
    total = query.count()
    mensagens = query.order_by(
        MensagemAtendimento.data_recebimento.desc()
    ).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "mensagens": [
            {
                "id": msg.id,
                "cliente": msg.cliente.nome,
                "empresa": msg.cliente.empresa,
                "canal": msg.canal.nome,
                "pergunta": msg.pergunta,
                "resposta_ia": msg.resposta_ia,
                "chunks_recuperados": msg.chunks_recuperados,
                "score_relevancia": float(msg.score_relevancia),
                "data_recebimento": msg.data_recebimento.isoformat(),
                # MULTIMODALIDADE
                "necessita_visual": msg.necessita_visual,
                "imagem_url": msg.imagem_url
            }
            for msg in mensagens
        ]
    }


@app.get("/mensagens/{mensagem_id}/detalhes-completo")
async def obter_detalhes_mensagem_completo(
    mensagem_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna detalhes completos de uma mensagem, incluindo imagens e anexos.
    
    Essencial para o painel do operador visualizar e editar a resposta
    antes de aprovar com elementos multimodais.
    """
    try:
        mensagem = db.query(MensagemAtendimento).filter(
            MensagemAtendimento.id == mensagem_id
        ).first()
        
        if not mensagem:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        
        # Construir resposta com detalhes completos
        imagem_sugerida = None
        if mensagem.imagem_sugerida_id:
            midia = db.query(MidiaDocumento).filter(
                MidiaDocumento.id == mensagem.imagem_sugerida_id
            ).first()
            if midia:
                imagem_sugerida = {
                    "id": midia.id,
                    "url": midia.url_publica,
                    "nome": midia.nome_arquivo,
                    "tipo": midia.tipo_midia,
                    "descricao": midia.descricao,
                    "tamanho_bytes": midia.tamanho_bytes,
                    "pagina": midia.pagina,
                    "score_relevancia": float(midia.score_relevancia)
                }
        
        # Processar anexos armazenados
        anexos_gerados = []
        if mensagem.anexos_gerados:
            import json
            try:
                anexos_gerados = json.loads(mensagem.anexos_gerados)
            except:
                anexos_gerados = []
        
        return {
            "id": mensagem.id,
            "cliente_id": mensagem.cliente_id,
            "cliente": {
                "nome": mensagem.cliente.nome,
                "empresa": mensagem.cliente.empresa
            },
            "canal": mensagem.canal.nome,
            "pergunta": mensagem.pergunta,
            "resposta_ia": mensagem.resposta_ia,
            "resposta_editada": mensagem.resposta_editada,
            "status": mensagem.status,
            "chunks_recuperados": mensagem.chunks_recuperados,
            "score_relevancia": float(mensagem.score_relevancia),
            "tempo_processamento_ms": mensagem.tempo_processamento_ms,
            "custo_api": float(mensagem.custo_api) if mensagem.custo_api else 0,
            "data_recebimento": mensagem.data_recebimento.isoformat(),
            "data_processamento": mensagem.data_processamento.isoformat() if mensagem.data_processamento else None,
            # MULTIMODALIDADE
            "necessita_visual": mensagem.necessita_visual,
            "imagem_sugerida": imagem_sugerida,
            "imagem_aprovada": mensagem.imagem_aprovada,
            "anexos_gerados": anexos_gerados,
            "score_satisfacao": mensagem.score_satisfacao
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message details: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/mensagens/{mensagem_id}/aprovar")
async def aprovar_mensagem(
    mensagem_id: int,
    aprovacao: MensagemAprovacao,
    db: Session = Depends(get_db)
):
    """
    Aprova ou rejeita uma mensagem (com edição opcional).
    
    Flow:
    - Se aprovada: status → APROVADA (pronta para envio)
    - Se rejeitada: status → REJEITADA (com motivo)
    """
    
    try:
        mensagem = db.query(MensagemAtendimento).filter(
            MensagemAtendimento.id == mensagem_id
        ).first()
        
        if not mensagem:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        
        if mensagem.status != "AGUARDANDO_APROVACAO":
            raise HTTPException(
                status_code=400,
                detail=f"Mensagem não está em status AGUARDANDO_APROVACAO (atual: {mensagem.status})"
            )
        
        # Registrar auditoria
        audit_dados_anteriores = {
            "status": mensagem.status,
            "resposta": mensagem.resposta_ia
        }
        
        if aprovacao.aprovada:
            # APROVAÇÃO
            mensagem.status = "APROVADA"
            mensagem.data_aprovacao = datetime.utcnow()
            mensagem.operador_id = aprovacao.operador_id
            
            # Usar resposta editada se fornecida
            if aprovacao.resposta_editada:
                mensagem.resposta_editada = aprovacao.resposta_editada
            
            logger.info(f"Mensagem {mensagem_id} aprovada pelo operador {aprovacao.operador_id}")
            
        else:
            # REJEIÇÃO
            mensagem.status = "REJEITADA"
            mensagem.motivo_rejeicao = aprovacao.motivo_rejeicao
            mensagem.operador_id = aprovacao.operador_id
            mensagem.data_aprovacao = datetime.utcnow()
            
            logger.info(f"Mensagem {mensagem_id} rejeitada: {aprovacao.motivo_rejeicao}")
        
        # Salvar auditoria
        auditoria = Auditoria(
            mensagem_atendimento_id=mensagem_id,
            acao="APROVAÇÃO" if aprovacao.aprovada else "REJEIÇÃO",
            usuario_id=aprovacao.operador_id,
            descricao=f"Mensagem {'aprovada' if aprovacao.aprovada else 'rejeitada'} pelo operador",
            dados_anteriores=audit_dados_anteriores,
            dados_novos={
                "status": mensagem.status,
                "resposta": mensagem.resposta_editada or mensagem.resposta_ia
            }
        )
        db.add(auditoria)
        db.commit()
        
        return {
            "sucesso": True,
            "mensagem_id": mensagem_id,
            "novo_status": mensagem.status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mensagens/{mensagem_id}/aprovar-com-imagens")
async def aprovar_mensagem_com_imagens(
    mensagem_id: int,
    aprovacao: MensagemAprovacaoComImagens,
    db: Session = Depends(get_db)
):
    """
    Aprova uma mensagem com suporte a multimodalidade (imagens/anexos).
    
    Operador pode:
    1. Editar a resposta textual
    2. Aprovar, rejeitar ou alterar a imagem sugerida
    3. Incluir anexos adicionais
    
    Payload esperado:
    {
        "resposta_editada": "Resposta corrigida (opcional)",
        "aprovada": true,
        "motivo_rejeicao": null,
        "operador_id": 1,
        "imagem_aprovada": true,
        "anexos_aprovados": [
            {
                "url": "http://...",
                "tipo": "image",
                "descricao": "Diagrama de instalação"
            }
        ]
    }
    """
    
    try:
        mensagem = db.query(MensagemAtendimento).filter(
            MensagemAtendimento.id == mensagem_id
        ).first()
        
        if not mensagem:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        
        if mensagem.status != "AGUARDANDO_APROVACAO":
            raise HTTPException(
                status_code=400,
                detail=f"Mensagem não está em status AGUARDANDO_APROVACAO (atual: {mensagem.status})"
            )
        
        # Registrar auditoria
        audit_dados_anteriores = {
            "status": mensagem.status,
            "resposta": mensagem.resposta_ia,
            "imagem_sugerida": mensagem.imagem_url
        }
        
        if aprovacao.aprovada:
            # APROVAÇÃO
            mensagem.status = "APROVADA"
            mensagem.data_aprovacao = datetime.utcnow()
            mensagem.operador_id = aprovacao.operador_id
            
            # Usar resposta editada se fornecida
            if aprovacao.resposta_editada:
                mensagem.resposta_editada = aprovacao.resposta_editada
            
            # MULTIMODALIDADE: Processar imagens aprovadas
            mensagem.imagem_aprovada = aprovacao.imagem_aprovada
            
            # Armazenar anexos aprovados em JSON
            if aprovacao.anexos_aprovados:
                import json
                anexos_json = [
                    {
                        "url": anexo.url,
                        "tipo": anexo.tipo,
                        "descricao": anexo.descricao,
                        "tamanho_bytes": anexo.tamanho_bytes,
                        "mime_type": anexo.mime_type
                    }
                    for anexo in aprovacao.anexos_aprovados
                ]
                mensagem.anexos_gerados = json.dumps(anexos_json)
            
            logger.info(
                f"Mensagem {mensagem_id} aprovada pelo operador {aprovacao.operador_id} "
                f"(imagem: {aprovacao.imagem_aprovada}, anexos: {len(aprovacao.anexos_aprovados or [])})"
            )
            
        else:
            # REJEIÇÃO
            mensagem.status = "REJEITADA"
            mensagem.motivo_rejeicao = aprovacao.motivo_rejeicao
            mensagem.operador_id = aprovacao.operador_id
            mensagem.data_aprovacao = datetime.utcnow()
            
            logger.info(f"Mensagem {mensagem_id} rejeitada: {aprovacao.motivo_rejeicao}")
        
        # Salvar auditoria com detalhes de imagens
        auditoria = Auditoria(
            mensagem_atendimento_id=mensagem_id,
            acao="APROVAÇÃO" if aprovacao.aprovada else "REJEIÇÃO",
            usuario_id=aprovacao.operador_id,
            descricao=f"Mensagem {'aprovada' if aprovacao.aprovada else 'rejeitada'} com multimodalidade",
            dados_anteriores=audit_dados_anteriores,
            dados_novos={
                "status": mensagem.status,
                "resposta": mensagem.resposta_editada or mensagem.resposta_ia,
                "imagem_aprovada": aprovacao.imagem_aprovada,
                "total_anexos": len(aprovacao.anexos_aprovados or [])
            }
        )
        db.add(auditoria)
        db.commit()
        
        return {
            "sucesso": True,
            "mensagem_id": mensagem_id,
            "novo_status": mensagem.status,
            "imagem_aprovada": aprovacao.imagem_aprovada,
            "total_anexos": len(aprovacao.anexos_aprovados or []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving message with images: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mensagens/{mensagem_id}/enviar")
async def enviar_mensagem(
    mensagem_id: int,
    db: Session = Depends(get_db)
):
    """
    Marca mensagem aprovada como enviada (simulação de envio via WhatsApp/Email).
    
    Em produção, isso dispararia webhooks reais para Meta Cloud API, Microsoft Graph, etc.
    """
    
    try:
        mensagem = db.query(MensagemAtendimento).filter(
            MensagemAtendimento.id == mensagem_id
        ).first()
        
        if not mensagem:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        
        if mensagem.status != "APROVADA":
            raise HTTPException(
                status_code=400,
                detail=f"Apenas mensagens APROVADAS podem ser enviadas"
            )
        
        # Atualizar status
        mensagem.status = "ENVIADA"
        mensagem.data_envio = datetime.utcnow()
        
        # Registrar auditoria
        auditoria = Auditoria(
            mensagem_atendimento_id=mensagem_id,
            acao="ENVIO",
            descricao="Resposta enviada ao cliente"
        )
        db.add(auditoria)
        db.commit()
        
        logger.info(f"Mensagem {mensagem_id} marcada como enviada")
        
        # TODO: Aqui seria disparado webhook para canal real
        # - WhatsApp: POST to Meta Cloud API
        # - Outlook: POST to Microsoft Graph API
        # - Email: SMTP send
        
        return {
            "sucesso": True,
            "mensagem_id": mensagem_id,
            "novo_status": "ENVIADA",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# FEEDBACK ENDPOINTS
# ============================================

@app.post("/mensagens/{mensagem_id}/feedback")
async def registrar_feedback(
    mensagem_id: int,
    feedback: MensagemFeedback,
    db: Session = Depends(get_db)
):
    """
    Registra feedback do usuário sobre a resposta (satisfação 1-5).
    Essencial para melhorar qualidade do modelo.
    """
    
    try:
        mensagem = db.query(MensagemAtendimento).filter(
            MensagemAtendimento.id == mensagem_id
        ).first()
        
        if not mensagem:
            raise HTTPException(status_code=404, detail="Mensagem não encontrada")
        
        mensagem.score_satisfacao = feedback.score_satisfacao
        mensagem.feedback_usuario = feedback.feedback_usuario
        db.commit()
        
        logger.info(f"Feedback registered for message {mensagem_id}: score {feedback.score_satisfacao}")
        
        return {
            "sucesso": True,
            "mensagem_id": mensagem_id,
            "score_satisfacao": feedback.score_satisfacao
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ANALYTICS & REPORTING
# ============================================

@app.get("/relatorios/diario")
async def relatorio_diario(
    cliente_id: Optional[int] = None,
    dias: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Relatório de performance diária (últimos N dias).
    """
    
    data_inicio = datetime.utcnow() - timedelta(days=dias)
    
    query = db.query(MensagemAtendimento).filter(
        MensagemAtendimento.data_recebimento >= data_inicio
    )
    
    if cliente_id:
        query = query.filter(MensagemAtendimento.cliente_id == cliente_id)
    
    mensagens = query.all()
    
    # Agrupar por data
    by_date = {}
    for msg in mensagens:
        data = msg.data_recebimento.date().isoformat()
        if data not in by_date:
            by_date[data] = {
                "total": 0,
                "aprovadas": 0,
                "rejeitadas": 0,
                "tempo_medio_ms": 0,
                "score_relevancia_medio": 0.0,
                "score_satisfacao_medio": 0.0
            }
        
        by_date[data]["total"] += 1
        if msg.status == "APROVADA":
            by_date[data]["aprovadas"] += 1
        elif msg.status == "REJEITADA":
            by_date[data]["rejeitadas"] += 1
    
    # Calcular médias
    for data, stats in by_date.items():
        msgs_data = [m for m in mensagens if m.data_recebimento.date().isoformat() == data]
        if msgs_data:
            stats["tempo_medio_ms"] = sum(m.tempo_processamento_ms for m in msgs_data) // len(msgs_data)
            stats["score_relevancia_medio"] = sum(float(m.score_relevancia) for m in msgs_data) / len(msgs_data)
            stats["score_satisfacao_medio"] = sum(m.score_satisfacao for m in msgs_data if m.score_satisfacao) / max(1, len([m for m in msgs_data if m.score_satisfacao]))
    
    return {
        "periodo": f"últimos {dias} dias",
        "total_geral": len(mensagens),
        "por_dia": by_date
    }


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )


# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/")
async def root():
    """
    Endpoint raiz com informações da API.
    """
    return {
        "nome": "RAG System API",
        "versao": "1.0.0",
        "descricao": "Sistema inteligente de atendimento com aprovação humana",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "status": "/status"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
