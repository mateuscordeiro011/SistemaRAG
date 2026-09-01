# ============================================
# HEALTH CHECK & DIAGNOSTIC MODULE
# ============================================
# Responsável por validar a saúde de todos os serviços:
# - Conectividade com MySQL
# - Responsividade do modelo de IA
# - Integridade de diretórios de arquivos
# - Teste de persistência de dados

import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any
from pathlib import Path
import json
import tempfile

from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI

from models import (
    Base, Cliente, Documento, MensagemAtendimento,
    Usuario, Auditoria
)
from database import SessionLocal, engine

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "backend/uploads")
REQUIRED_DIRECTORIES = [
    UPLOAD_DIR,
    "backend/logs",
]

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================
# DATABASE HEALTH CHECKS
# ============================================

def check_database_connection() -> Tuple[bool, str, int]:
    """
    Verifica se a conexão com o MySQL está ativa.
    
    Returns:
        (is_healthy, message, response_time_ms)
    """
    try:
        db = SessionLocal()
        start_time = time.time()
        
        # Execute a simple query
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        response_time_ms = int((time.time() - start_time) * 1000)
        db.close()
        
        logger.info(f"✓ Database connection OK ({response_time_ms}ms)")
        return True, "Database connection successful", response_time_ms
        
    except Exception as e:
        error_msg = f"Database connection failed: {str(e)}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg, 0


def check_database_tables() -> Tuple[bool, Dict[str, Any]]:
    """
    Valida que todas as tabelas esperadas existem e contêm dados.
    
    Returns:
        (is_healthy, details_dict)
    """
    try:
        db = SessionLocal()
        
        tables_status = {}
        
        # Verificar cada tabela
        table_checks = [
            ("clientes", Cliente),
            ("documentos", Documento),
            ("mensagens_atendimento", MensagemAtendimento),
            ("usuarios", Usuario),
            ("auditoria", Auditoria),
        ]
        
        all_healthy = True
        
        for table_name, model_class in table_checks:
            try:
                count = db.query(model_class).count()
                tables_status[table_name] = {
                    "status": "OK",
                    "row_count": count
                }
            except Exception as e:
                tables_status[table_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
                all_healthy = False
        
        db.close()
        return all_healthy, tables_status
        
    except Exception as e:
        logger.error(f"Error checking database tables: {e}")
        return False, {"error": str(e)}


def check_database_read_write() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executa um teste completo de escrita e leitura no banco.
    Cria um registro de teste temporário para validar persistência.
    
    Returns:
        (is_healthy, message, details_dict)
    """
    db = SessionLocal()
    test_client = None
    test_auditoria = None
    
    try:
        start_time = time.time()
        
        # 1. ESCRITA: Criar cliente de teste
        test_client_name = f"HEALTH_TEST_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        test_client = Cliente(
            nome=test_client_name,
            empresa="Health Check Test Company",
            descricao="Temporary test record for persistence validation",
            ativo=True
        )
        db.add(test_client)
        db.commit()
        
        write_time = int((time.time() - start_time) * 1000)
        test_client_id = test_client.id
        
        logger.info(f"✓ Database WRITE successful (cliente_id={test_client_id}, {write_time}ms)")
        
        # 2. LEITURA: Recuperar cliente
        read_start = time.time()
        retrieved_client = db.query(Cliente).filter(
            Cliente.id == test_client_id
        ).first()
        
        read_time = int((time.time() - read_start) * 1000)
        
        if not retrieved_client:
            raise Exception("Written record could not be read back")
        
        logger.info(f"✓ Database READ successful ({read_time}ms)")
        
        # 3. AUDITORIA: Registrar teste
        test_auditoria = Auditoria(
            acao="HEALTH_CHECK_TEST",
            descricao="Persistent storage validation test",
            dados_novos=json.dumps({
                "test_client_id": test_client_id,
                "write_time_ms": write_time,
                "read_time_ms": read_time
            })
        )
        db.add(test_auditoria)
        db.commit()
        
        logger.info(f"✓ Database AUDITORIA successful")
        
        # 4. LIMPEZA: Remover registros de teste
        db.delete(test_auditoria)
        db.delete(retrieved_client)
        db.commit()
        
        logger.info(f"✓ Database CLEANUP successful")
        
        total_time = int((time.time() - start_time) * 1000)
        
        details = {
            "test_client_id": test_client_id,
            "write_time_ms": write_time,
            "read_time_ms": read_time,
            "cleanup_successful": True,
            "total_time_ms": total_time
        }
        
        return True, "Database read-write-delete cycle successful", details
        
    except Exception as e:
        logger.error(f"Database persistence test failed: {e}")
        
        # Tentar limpar registros de teste
        try:
            if test_auditoria and test_auditoria.id:
                db.query(Auditoria).filter(Auditoria.id == test_auditoria.id).delete()
            if test_client and test_client.id:
                db.query(Cliente).filter(Cliente.id == test_client.id).delete()
            db.commit()
        except:
            db.rollback()
        
        return False, f"Database persistence test failed: {str(e)}", {"error": str(e)}
        
    finally:
        db.close()


# ============================================
# AI MODEL HEALTH CHECKS
# ============================================

def check_openai_api() -> Tuple[bool, str, int]:
    """
    Verifica responsividade da API OpenAI.
    Realiza um embedding de teste simples.
    
    Returns:
        (is_healthy, message, response_time_ms)
    """
    try:
        start_time = time.time()
        
        # Test embedding generation (lightweight operation)
        response = client.embeddings.create(
            input=["Health check test"],
            model="text-embedding-ada-002"
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        if response and len(response.data) > 0:
            logger.info(f"✓ OpenAI API connection OK ({response_time_ms}ms)")
            return True, "OpenAI API responsive", response_time_ms
        else:
            return False, "OpenAI API returned empty response", response_time_ms
            
    except Exception as e:
        error_msg = f"OpenAI API check failed: {str(e)}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg, 0


def check_openai_model_availability(model_name: str = OPENAI_MODEL) -> Tuple[bool, str]:
    """
    Verifica disponibilidade do modelo de IA específico.
    Tenta uma chamada bem simples ao modelo.
    
    Args:
        model_name: Nome do modelo (ex: gpt-3.5-turbo)
    
    Returns:
        (is_healthy, message)
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Respond with 'OK' only."}
            ],
            max_tokens=5,
            temperature=0
        )
        
        if response and response.choices:
            logger.info(f"✓ OpenAI model '{model_name}' is available")
            return True, f"Model {model_name} is available and responsive"
        else:
            return False, f"Model {model_name} returned empty response"
            
    except Exception as e:
        error_msg = f"Model check failed for {model_name}: {str(e)}"
        logger.error(f"✗ {error_msg}")
        return False, error_msg


# ============================================
# FILE SYSTEM HEALTH CHECKS
# ============================================

def check_file_system() -> Tuple[bool, Dict[str, Any]]:
    """
    Verifica integridade do sistema de arquivos.
    Valida que diretórios necessários existem e são graváveis.
    
    Returns:
        (is_healthy, details_dict)
    """
    filesystem_status = {}
    all_healthy = True
    
    for directory in REQUIRED_DIRECTORIES:
        try:
            path = Path(directory)
            
            # Criar diretório se não existir
            path.mkdir(parents=True, exist_ok=True)
            
            # Testar permissão de escrita
            test_file = path / ".healthcheck"
            test_file.write_text(f"Health check at {datetime.utcnow().isoformat()}")
            
            disk_usage = os.statvfs(directory)
            free_space_gb = (disk_usage.f_bavail * disk_usage.f_frsize) / (1024 ** 3)
            
            filesystem_status[directory] = {
                "status": "OK",
                "writable": True,
                "free_space_gb": round(free_space_gb, 2)
            }
            
            # Limpar arquivo de teste
            test_file.unlink()
            
        except Exception as e:
            filesystem_status[directory] = {
                "status": "ERROR",
                "writable": False,
                "error": str(e)
            }
            all_healthy = False
    
    return all_healthy, filesystem_status


# ============================================
# COMPREHENSIVE HEALTH CHECK
# ============================================

def perform_full_health_check() -> Dict[str, Any]:
    """
    Realiza diagnóstico completo do sistema.
    
    Returns:
        Dicionário com status de todos os serviços
    """
    health_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "HEALTHY",
        "checks": {}
    }
    
    # 1. Database Connection
    logger.info("=" * 50)
    logger.info("HEALTH CHECK: Database Connection")
    db_conn_ok, db_conn_msg, db_conn_time = check_database_connection()
    health_report["checks"]["database_connection"] = {
        "status": "OK" if db_conn_ok else "ERROR",
        "message": db_conn_msg,
        "response_time_ms": db_conn_time
    }
    if not db_conn_ok:
        health_report["overall_status"] = "UNHEALTHY"
    
    # 2. Database Tables
    logger.info("=" * 50)
    logger.info("HEALTH CHECK: Database Tables")
    db_tables_ok, db_tables_status = check_database_tables()
    health_report["checks"]["database_tables"] = {
        "status": "OK" if db_tables_ok else "ERROR",
        "details": db_tables_status
    }
    if not db_tables_ok:
        health_report["overall_status"] = "UNHEALTHY"
    
    # 3. Database Read-Write-Delete
    logger.info("=" * 50)
    logger.info("HEALTH CHECK: Database Persistence")
    db_rwd_ok, db_rwd_msg, db_rwd_details = check_database_read_write()
    health_report["checks"]["database_persistence"] = {
        "status": "OK" if db_rwd_ok else "ERROR",
        "message": db_rwd_msg,
        "details": db_rwd_details
    }
    if not db_rwd_ok:
        health_report["overall_status"] = "UNHEALTHY"
    
    # 4. OpenAI API
    logger.info("=" * 50)
    logger.info("HEALTH CHECK: OpenAI API Connectivity")
    openai_ok, openai_msg, openai_time = check_openai_api()
    health_report["checks"]["openai_api"] = {
        "status": "OK" if openai_ok else "ERROR",
        "message": openai_msg,
        "response_time_ms": openai_time
    }
    if not openai_ok:
        health_report["overall_status"] = "DEGRADED"  # Degraded, not critical
    
    # 5. OpenAI Model
    logger.info("=" * 50)
    logger.info("HEALTH CHECK: AI Model Availability")
    model_ok, model_msg = check_openai_model_availability()
    health_report["checks"]["ai_model"] = {
        "status": "OK" if model_ok else "ERROR",
        "message": model_msg,
        "model": OPENAI_MODEL
    }
    if not model_ok:
        health_report["overall_status"] = "DEGRADED"
    
    # 6. File System
    logger.info("=" * 50)
    logger.info("HEALTH CHECK: File System")
    fs_ok, fs_status = check_file_system()
    health_report["checks"]["file_system"] = {
        "status": "OK" if fs_ok else "ERROR",
        "details": fs_status
    }
    if not fs_ok:
        health_report["overall_status"] = "UNHEALTHY"
    
    logger.info("=" * 50)
    logger.info(f"HEALTH CHECK COMPLETE: {health_report['overall_status']}")
    logger.info("=" * 50)
    
    return health_report


def get_quick_status() -> Dict[str, Any]:
    """
    Status rápido do sistema (sem testes de escrita/leitura).
    Usado em polling frequente.
    """
    status = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "OK"
    }
    
    # Apenas verificações rápidas
    db_ok, _, db_time = check_database_connection()
    openai_ok, _, openai_time = check_openai_api()
    
    status["database"] = "OK" if db_ok else "ERROR"
    status["database_response_ms"] = db_time
    status["ai_model"] = "OK" if openai_ok else "ERROR"
    status["ai_response_ms"] = openai_time
    
    if not db_ok or not openai_ok:
        status["status"] = "DEGRADED"
    
    return status
