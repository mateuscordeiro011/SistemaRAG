"""
Módulo de ingestão de documentos para SistemaRAG
Processa documentos, extrai chunks e gera embeddings
"""

import logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import Chunk, MidiaDocumento, RespostaChunk
from utils.embedding_client import embedding_client
from utils.text_splitter import split_text_into_chunks

logger = logging.getLogger(__name__)


async def processar_documento(
    documento_id: int,
    caminho_arquivo: str,
    cliente_id: int,
    db: Session,
    tamanho_chunk: int = 512,
    sobreposicao: int = 50,
) -> dict:
    """
    Processa um documento completo: extração, chunking e embedding
    
    Args:
        documento_id: ID do documento no banco
        caminho_arquivo: Caminho para o arquivo
        cliente_id: ID do cliente proprietário
        db: Sessão SQLAlchemy
        tamanho_chunk: Tokens por chunk
        sobreposicao: Tokens de sobreposição entre chunks
    
    Returns:
        Dict com estatísticas de processamento
    """
    try:
        # 1. Extrair texto do arquivo
        logger.info(f"Iniciando processamento documento {documento_id}")
        texto_completo = _extrair_texto_arquivo(caminho_arquivo)
        
        if not texto_completo or len(texto_completo.strip()) == 0:
            raise ValueError("Arquivo vazio ou sem conteúdo textual")
        
        # 2. Dividir em chunks
        chunks_texto = split_text_into_chunks(
            texto_completo,
            chunk_size=tamanho_chunk,
            overlap=sobreposicao
        )
        
        if not chunks_texto:
            raise ValueError("Falha ao dividir documento em chunks")
        
        logger.info(f"Documento dividido em {len(chunks_texto)} chunks")
        
        # 3. Gerar embeddings
        embeddings = await embedding_client.encode_batch(chunks_texto)
        
        # 4. Criar objetos Chunk
        chunk_objects = []
        for idx, (texto, embedding) in enumerate(zip(chunks_texto, embeddings)):
            chunk = Chunk(
                cliente_id=cliente_id,
                midia_documento_id=documento_id,
                numero_pagina=_estimar_pagina(texto_completo, texto),
                conteudo_texto=texto,
                tamanho_token=len(texto.split()),  # Aproximado
                hash_conteudo=_gerar_hash(texto),
            )
            chunk_objects.append((chunk, embedding))
        
        # ✅ CRÍTICO: Salvar chunks primeiro e sincronizar IDs
        db.bulk_save_objects([c[0] for c in chunk_objects])
        db.flush()  # ✅ Sincronizar IDs gerados do banco de volta aos objetos
        
        # Agora os chunk.id estão preenchidos!
        
        # 5. Salvar embeddings associados aos IDs dos chunks
        _salvar_embeddings_banco(chunk_objects, db)
        
        # 6. Atualizar status do documento
        documento = db.query(MidiaDocumento).filter_by(id=documento_id).first()
        if documento:
            documento.status = 'INDEXADO'
            db.add(documento)
        
        db.commit()
        
        logger.info(f"Documento {documento_id} processado com sucesso")
        
        return {
            "documento_id": documento_id,
            "total_chunks": len(chunk_objects),
            "total_embeddings": len(embeddings),
            "status": "sucesso"
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar documento {documento_id}: {str(e)}")
        
        # Marcar documento com erro
        try:
            documento = db.query(MidiaDocumento).filter_by(id=documento_id).first()
            if documento:
                documento.status = 'ERRO'
                documento.mensagem_erro = str(e)[:500]
                db.add(documento)
            db.commit()
        except:
            pass
        
        raise


def _extrair_texto_arquivo(caminho_arquivo: str) -> str:
    """
    Extrai texto de um arquivo (PDF, DOCX, TXT, MD)
    
    Args:
        caminho_arquivo: Caminho para o arquivo
    
    Returns:
        Texto extraído
    """
    ext = Path(caminho_arquivo).suffix.lower()
    texto = ""
    
    if ext == '.txt' or ext == '.md':
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            texto = f.read()
    
    elif ext == '.pdf':
        try:
            import PyPDF2
            with open(caminho_arquivo, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    texto += page.extract_text()
        except ImportError:
            logger.warning("PyPDF2 não instalado, usando fallback")
            texto = _extrair_pdf_fallback(caminho_arquivo)
    
    elif ext == '.docx':
        try:
            from docx import Document
            doc = Document(caminho_arquivo)
            for paragraph in doc.paragraphs:
                texto += paragraph.text + "\n"
        except ImportError:
            logger.error("python-docx não instalado")
            raise ValueError("Formato DOCX não suportado")
    
    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}")
    
    return texto.strip()


def _extrair_pdf_fallback(caminho_arquivo: str) -> str:
    """Fallback para extração de PDF sem PyPDF2"""
    import subprocess
    
    try:
        # Usar pdftotext se disponível
        resultado = subprocess.run(
            ['pdftotext', caminho_arquivo, '-'],
            capture_output=True,
            text=True,
            timeout=30
        )
        return resultado.stdout
    except Exception as e:
        logger.error(f"Falha em fallback PDF: {e}")
        return ""


def _salvar_embeddings_banco(chunk_embeddings: List[Tuple], db: Session):
    """
    Salva embeddings dos chunks no banco de dados
    
    ✅ IMPORTANTE: Só chama após db.flush() sincronizar os IDs!
    
    Args:
        chunk_embeddings: Lista de tuplas (Chunk, embedding_array)
        db: Sessão SQLAlchemy
    """
    for chunk, embedding in chunk_embeddings:
        # ✅ Agora chunk.id está preenchido!
        if not chunk.id:
            logger.warning(f"Chunk sem ID! Pulando.")
            continue
        
        # Converter embedding para bytes para armazenar
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
        
        chunk.embedding_vector = embedding_bytes
        db.add(chunk)
    
    db.commit()


def _estimar_pagina(texto_completo: str, texto_chunk: str) -> Optional[int]:
    """
    Estima o número de página onde o chunk aparece
    
    Heurística simples: conta quebras de página aproximadas
    """
    pos = texto_completo.find(texto_chunk)
    if pos < 0:
        return None
    
    # Estimar 50 linhas por página
    aprox_linhas = texto_completo[:pos].count('\n')
    aprox_pagina = (aprox_linhas // 50) + 1
    
    return aprox_pagina


def _gerar_hash(texto: str) -> str:
    """
    Gera hash SHA256 do texto para deduplicação
    """
    import hashlib
    return hashlib.sha256(texto.encode()).hexdigest()


async def processar_lote_documentos(
    documento_ids: List[int],
    cliente_id: int,
    db: Session,
) -> dict:
    """
    Processa um lote de documentos
    
    Args:
        documento_ids: Lista de IDs de documentos
        cliente_id: ID do cliente
        db: Sessão SQLAlchemy
    
    Returns:
        Estatísticas consolidadas
    """
    resultados = {
        "total_processados": 0,
        "total_sucesso": 0,
        "total_erro": 0,
        "documentos": []
    }
    
    for doc_id in documento_ids:
        try:
            documento = db.query(MidiaDocumento).filter_by(
                id=doc_id,
                cliente_id=cliente_id
            ).first()
            
            if not documento:
                logger.warning(f"Documento {doc_id} não encontrado")
                continue
            
            resultado = await processar_documento(
                documento_id=doc_id,
                caminho_arquivo=documento.caminho_arquivo,
                cliente_id=cliente_id,
                db=db
            )
            
            resultados["total_sucesso"] += 1
            resultados["documentos"].append(resultado)
            
        except Exception as e:
            logger.error(f"Erro no documento {doc_id}: {e}")
            resultados["total_erro"] += 1
            resultados["documentos"].append({
                "documento_id": doc_id,
                "status": "erro",
                "erro": str(e)
            })
        
        resultados["total_processados"] += 1
    
    return resultados


def deduplicar_chunks(cliente_id: int, db: Session) -> int:
    """
    Remove chunks duplicados (mesmo hash) mantendo o primeiro
    
    Args:
        cliente_id: ID do cliente
        db: Sessão SQLAlchemy
    
    Returns:
        Número de chunks removidos
    """
    # Query para encontrar duplicatas
    duplicatas = db.query(Chunk).filter(
        and_(
            Chunk.cliente_id == cliente_id,
            Chunk.deletado == False
        )
    ).all()
    
    hashes_vistos = {}
    ids_deletar = []
    
    for chunk in duplicatas:
        if chunk.hash_conteudo in hashes_vistos:
            ids_deletar.append(chunk.id)
        else:
            hashes_vistos[chunk.hash_conteudo] = chunk.id
    
    # Marcar como deletados
    db.query(Chunk).filter(Chunk.id.in_(ids_deletar)).update(
        {Chunk.deletado: True}
    )
    db.commit()
    
    logger.info(f"Removidas {len(ids_deletar)} duplicatas para cliente {cliente_id}")
    
    return len(ids_deletar)