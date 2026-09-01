# ============================================
# TEST SUITE - API FastAPI
# ============================================
# Testes para endpoints principais da API
# Executar com: pytest test_api.py -v

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db, Base
from models import Cliente, Documento, MensagemAtendimento

# ============================================
# FIXTURES
# ============================================

# Database de teste em memória
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ============================================
# TESTS - Health & Status
# ============================================

def test_health():
    """Testa endpoint /health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


def test_status():
    """Testa endpoint /status"""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert "total_clientes" in data
    assert "total_mensagens" in data


# ============================================
# TESTS - Clientes
# ============================================

def test_criar_cliente():
    """Testa criação de cliente"""
    response = client.post(
        "/clientes",
        json={
            "nome": "Cliente Teste",
            "empresa": "Empresa XYZ",
            "descricao": "Cliente para testes"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "Cliente Teste"
    assert data["empresa"] == "Empresa XYZ"
    assert data["ativo"] == True


def test_criar_cliente_duplicado():
    """Testa validação de cliente duplicado"""
    # Criar primeiro
    client.post(
        "/clientes",
        json={
            "nome": "Cliente Duplicado",
            "empresa": "Empresa ABC"
        }
    )
    
    # Tentar criar novamente
    response = client.post(
        "/clientes",
        json={
            "nome": "Cliente Duplicado",
            "empresa": "Empresa ABC"
        }
    )
    assert response.status_code == 400


def test_obter_cliente():
    """Testa obtenção de cliente"""
    # Criar cliente
    create_response = client.post(
        "/clientes",
        json={
            "nome": "Cliente Get Test",
            "empresa": "Empresa Test"
        }
    )
    cliente_id = create_response.json()["id"]
    
    # Obter cliente
    response = client.get(f"/clientes/{cliente_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cliente_id
    assert data["nome"] == "Cliente Get Test"


def test_listar_clientes():
    """Testa listagem de clientes"""
    response = client.get("/clientes")
    assert response.status_code == 200
    data = response.json()
    assert "clientes" in data
    assert "total" in data


def test_estatisticas_cliente():
    """Testa estatísticas de cliente"""
    # Criar cliente
    create_response = client.post(
        "/clientes",
        json={
            "nome": "Cliente Stats",
            "empresa": "Empresa Stats"
        }
    )
    cliente_id = create_response.json()["id"]
    
    # Obter estatísticas
    response = client.get(f"/clientes/{cliente_id}/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "cliente" in data
    assert "estatisticas" in data


# ============================================
# TESTS - Documentos
# ============================================

def test_listar_documentos_cliente():
    """Testa listagem de documentos"""
    # Criar cliente
    create_response = client.post(
        "/clientes",
        json={
            "nome": "Cliente Docs",
            "empresa": "Empresa Docs"
        }
    )
    cliente_id = create_response.json()["id"]
    
    # Listar documentos
    response = client.get(f"/documentos/cliente/{cliente_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["cliente_id"] == cliente_id
    assert "documentos" in data


# ============================================
# TESTS - Fila de Aprovação
# ============================================

def test_fila_aprovacao_vazia():
    """Testa fila de aprovação vazia"""
    response = client.get("/fila-aprovacao")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["mensagens"] == []


# ============================================
# TESTS - Validações
# ============================================

def test_cliente_nao_encontrado():
    """Testa erro 404 para cliente não encontrado"""
    response = client.get("/clientes/9999")
    assert response.status_code == 404


def test_parametros_invalidos():
    """Testa validação de parâmetros"""
    response = client.post(
        "/clientes",
        json={
            "nome": "",  # Nome vazio
            "empresa": "Test"
        }
    )
    assert response.status_code != 200


# ============================================
# TESTS - Relatórios
# ============================================

def test_relatorio_diario():
    """Testa geração de relatório diário"""
    response = client.get("/relatorios/diario?dias=7")
    assert response.status_code == 200
    data = response.json()
    assert "periodo" in data
    assert "por_dia" in data


# ============================================
# CLEANUP
# ============================================

@pytest.fixture(autouse=True)
def cleanup():
    """Limpa banco de dados entre testes"""
    yield
    # Limpar depois de cada teste
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ============================================
# EXECUTAR TESTES
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
