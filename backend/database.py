# ============================================
# DATABASE CONFIGURATION & SESSION MANAGEMENT
# ============================================

import logging
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os

from models import Base

logger = logging.getLogger(__name__)

# ============================================
# DATABASE URL CONSTRUCTION
# ============================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://rag_user:rag_password@db:3306/sistema_rag"
)

# ============================================
# ENGINE CONFIGURATION
# ============================================
# Configurado para melhor performance e reliability em produção

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Conexões persistentes no pool
    max_overflow=20,  # Conexões adicionais quando pool está cheio
    pool_recycle=3600,  # Recicla conexões a cada 1 hora (MySQL default timeout)
    pool_pre_ping=True,  # Verifica conexão antes de usar (evita "gone away")
    echo=False,  # Defina como True para debug SQL
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False
    }
)

# ============================================
# SESSION FACTORY
# ============================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session
)

# ============================================
# EVENT LISTENERS PARA OTIMIZAÇÃO
# ============================================

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Listener para configurações de conexão específicas do MySQL.
    """
    # Garante UTF-8 em toda a conexão
    cursor = dbapi_conn.cursor()
    cursor.execute("SET NAMES utf8mb4")
    cursor.execute("SET CHARACTER SET utf8mb4")
    cursor.execute("SET COLLATION_CONNECTION = utf8mb4_unicode_ci")
    cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES'")
    cursor.close()


#@event.listens_for(engine, "pool_connect")
#def receive_pool_connect(dbapi_conn, connection_record):
#    """
#    Listener executado quando uma conexão é obtida do pool.
#    """
#    logger.debug("Connection obtained from pool")


#@event.listens_for(engine, "pool_disconnect")
#def receive_pool_disconnect(dbapi_conn, connection_record):
##    """
#    Listener executado quando uma conexão é devolvida ao pool.
#    """
#    logger.debug("Connection returned to pool")


#@event.listens_for(engine, "pool_checkout")
#def receive_pool_checkout(dbapi_conn, connection_record, connection_proxy):
#    """
#    Listener executado quando uma conexão é checada do pool.
#    Verifica se a conexão está saudável.
#    """
#    try:
#        dbapi_conn.ping(reconnect=True)
#    except Exception as e:
#        logger.warning(f"Database connection check failed: {e}")


# ============================================
# DATABASE INITIALIZATION
# ============================================

def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    Normalmente chamado na inicialização da aplicação.
    """
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def health_check() -> bool:
    """
    Verifica a saúde da conexão com o banco de dados.
    Útil para health checks de observabilidade.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# ============================================
# SESSION DEPENDENCY INJECTION
# ============================================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection para FastAPI endpoints.
    Fornece uma sessão de banco de dados para cada requisição.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# CONTEXT MANAGERS PARA GERENCIAMENTO DE TRANSAÇÕES
# ============================================

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager para operações de banco de dados sincronizadas.
    Gerencia commit/rollback automaticamente.
    
    Usage:
        with get_db_session() as session:
            user = session.query(User).first()
            user.name = "New Name"
            # Commit automático ao sair do context
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        session.close()


# ============================================
# BULK OPERATIONS PARA PERFORMANCE
# ============================================

def bulk_insert(model_class, records: list[dict], batch_size: int = 1000) -> int:
    """
    Insere múltiplos registros em lotes para melhor performance.
    
    Args:
        model_class: Classe do modelo SQLAlchemy
        records: Lista de dicionários com dados
        batch_size: Tamanho do lote para inserção
        
    Returns:
        Número total de registros inseridos
    """
    if not records:
        return 0
    
    total_inserted = 0
    
    try:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            with get_db_session() as session:
                objects = [model_class(**record) for record in batch]
                session.bulk_insert_mappings(model_class, [record for record in batch])
                total_inserted += len(batch)
                logger.info(f"Inserted batch of {len(batch)} records")
        
        logger.info(f"Bulk insert completed: {total_inserted} records")
        return total_inserted
        
    except Exception as e:
        logger.error(f"Bulk insert failed: {e}")
        raise


# ============================================
# DATABASE CLEANUP & MAINTENANCE
# ============================================

def vacuum_database():
    """
    Executa manutenção de banco de dados (analyze/optimize).
    Deve ser executado periodicamente em produção.
    """
    try:
        with engine.connect() as connection:
            # MySQL OPTIMIZE TABLE melhora performance
            tables = ["mensagens_atendimento", "documentos", "chunks", "embeddings"]
            for table in tables:
                logger.info(f"Optimizing table: {table}")
                connection.execute(text(f"OPTIMIZE TABLE {table}"))
            connection.commit()
        logger.info("Database maintenance completed")
    except Exception as e:
        logger.error(f"Database maintenance failed: {e}")


def drop_all_tables():
    """
    CUIDADO: Deleta todas as tabelas e dados do banco.
    Use apenas em ambiente de desenvolvimento!
    """
    import warnings
    warnings.warn("Dropping all tables - this will delete all data!", UserWarning)
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


# ============================================
# QUERY HELPERS
# ============================================

def count_records(model_class, filter_by: dict = None) -> int:
    """
    Conta registros de um modelo com filtros opcionais.
    """
    with get_db_session() as session:
        query = session.query(model_class)
        if filter_by:
            query = query.filter_by(**filter_by)
        return query.count()


def get_paginated(
    model_class,
    page: int = 1,
    page_size: int = 20,
    filter_by: dict = None,
    order_by = None
) -> tuple[list, int]:
    """
    Retorna registros paginados com total de registros.
    
    Returns:
        (records, total_count)
    """
    with get_db_session() as session:
        query = session.query(model_class)
        
        if filter_by:
            query = query.filter_by(**filter_by)
        
        if order_by is not None:
            query = query.order_by(order_by)
        
        total = query.count()
        
        offset = (page - 1) * page_size
        records = query.offset(offset).limit(page_size).all()
        
        return records, total


# ============================================
# LOGGING CONFIGURAÇÃO
# ============================================

def setup_database_logging():
    """
    Configura logging detalhado para operações de banco de dados.
    Útil para debugging em desenvolvimento.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Habilita SQL logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)


if __name__ == "__main__":
    # Script para testes de conexão
    print("Testing database connection...")
    print(f"Database URL: {DATABASE_URL}")
    
    if health_check():
        print("✓ Database connection successful!")
        init_db()
        print("✓ Database initialized!")
    else:
        print("✗ Database connection failed!")
