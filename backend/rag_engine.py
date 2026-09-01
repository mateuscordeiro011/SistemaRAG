# ============================================
# RAG ENGINE - Retrieval Augmented Generation
# ============================================
# Responsável por:
# 1. Busca semântica de chunks relevantes
# 2. Construção de contexto
# 3. Geração de respostas com LLM
# 4. Prevenção de alucinações
# 5. Rastreamento de tokens e custo

import os
import logging
import pickle
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime

import numpy as np
from sqlalchemy.orm import Session
from openai import OpenAI

from models import (
    Cliente, Documento, Chunk, Embedding, MensagemAtendimento, Canal, MidiaDocumento
)
from database import get_db_session

logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
MIN_SIMILARITY_SCORE = float(os.getenv("MIN_SIMILARITY_SCORE", 0.5))
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", 5))
MIN_RELEVANT_CHUNKS = int(os.getenv("MIN_RELEVANT_CHUNKS", 2))
MAX_CONTEXT_LENGTH = 4000  # Tokens para contexto

# Cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================
# EMBEDDING GENERATION FOR QUERY
# ============================================

def generate_query_embedding(query: str, model: str = OPENAI_EMBEDDING_MODEL) -> np.ndarray:
    """
    Gera embedding para a pergunta do usuário.
    """
    try:
        response = client.embeddings.create(
            input=[query],
            model=model
        )
        embedding = np.array(response.data[0].embedding, dtype=np.float32)
        logger.debug(f"Generated query embedding with dimension {len(embedding)}")
        return embedding
    except Exception as e:
        logger.error(f"Error generating query embedding: {e}")
        raise


# ============================================
# SEMANTIC SEARCH
# ============================================

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Calcula similaridade cosseno entre dois vetores.
    
    Fórmula: cos(θ) = (a · b) / (||a|| * ||b||)
    
    Retorna score entre 0 e 1:
    - 1.0 = vetores idênticos
    - 0.5 = similaridade média
    - 0.0 = vetores ortogonais (não relacionados)
    """
    magnitude_a = np.linalg.norm(a)
    magnitude_b = np.linalg.norm(b)
    
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    
    similarity = np.dot(a, b) / (magnitude_a * magnitude_b)
    # Normalizar para 0-1
    return (similarity + 1) / 2


def search_similar_chunks(
    db: Session,
    cliente_id: int,
    query_embedding: np.ndarray,
    top_k: int = TOP_K_CHUNKS,
    min_score: float = MIN_SIMILARITY_SCORE
) -> List[Tuple[Chunk, float]]:
    """
    Busca chunks similares à query usando similaridade cosseno.
    
    Returns:
        Lista de (Chunk, similarity_score) ordenada por relevância
    """
    try:
        # Buscar documentos processados do cliente
        documentos = db.query(Documento).filter(
            Documento.cliente_id == cliente_id,
            Documento.status == "SUCESSO"
        ).all()
        
        if not documentos:
            logger.warning(f"No processed documents found for cliente {cliente_id}")
            return []
        
        documento_ids = [d.id for d in documentos]
        
        # Buscar chunks dos documentos
        chunks = db.query(Chunk).filter(
            Chunk.documento_id.in_(documento_ids)
        ).all()
        
        if not chunks:
            logger.warning(f"No chunks found for cliente {cliente_id}")
            return []
        
        # Buscar embeddings
        results_with_scores = []
        
        for chunk in chunks:
            embedding_record = db.query(Embedding).filter(
                Embedding.chunk_id == chunk.id
            ).first()
            
            if not embedding_record:
                continue
            
            try:
                # Desserializar embedding
                embedding_vector = pickle.loads(embedding_record.vetor)
                
                # Calcular similaridade
                similarity = cosine_similarity(query_embedding, embedding_vector)
                
                if similarity >= min_score:
                    results_with_scores.append((chunk, similarity))
                    
            except Exception as e:
                logger.error(f"Error processing embedding for chunk {chunk.id}: {e}")
                continue
        
        # Ordenar por relevância (descendente) e limitar a top_k
        results_with_scores.sort(key=lambda x: x[1], reverse=True)
        top_results = results_with_scores[:top_k]
        
        logger.info(f"Found {len(top_results)} relevant chunks (score >= {min_score})")
        return top_results
        
    except Exception as e:
        logger.error(f"Error searching similar chunks: {e}")
        raise


# ============================================
# CONTEXT BUILDING
# ============================================

def build_context(
    chunks_with_scores: List[Tuple[Chunk, float]],
    max_tokens: int = MAX_CONTEXT_LENGTH
) -> Tuple[str, int, float]:
    """
    Constrói contexto a partir dos chunks relevantes.
    Estratégia: incluir chunks de forma ordenada até atingir limite de tokens.
    
    Returns:
        (contexto, numero_chunks_inclusos, score_relevancia_media)
    """
    if not chunks_with_scores:
        return "", 0, 0.0
    
    context_parts = []
    total_tokens = 0
    scores = []
    
    # Aproximação: 1 token ≈ 4 caracteres
    tokens_per_char = 0.25
    
    for chunk, score in chunks_with_scores:
        chunk_tokens = len(chunk.conteudo) * tokens_per_char
        
        # Parar se exceder limite
        if total_tokens + chunk_tokens > max_tokens:
            break
        
        # Formatar chunk com informações de origem
        chunk_text = f"[Documento: {chunk.documento.nome_arquivo} | Chunk #{chunk.numero_chunk}]\n{chunk.conteudo}"
        context_parts.append(chunk_text)
        total_tokens += chunk_tokens
        scores.append(score)
    
    context = "\n\n---\n\n".join(context_parts)
    average_score = np.mean(scores) if scores else 0.0
    
    logger.info(f"Built context from {len(context_parts)} chunks (~{int(total_tokens)} tokens)")
    return context, len(context_parts), average_score


# ============================================
# PROMPT CONSTRUCTION
# ============================================

def build_system_prompt(cliente_nome: str) -> str:
    """
    Sistema prompt que instrui o LLM sobre seu papel.
    Criticamente importante para evitar alucinações.
    """
    return f"""Você é um assistente de atendimento inteligente para a empresa/cliente: {cliente_nome}.

Suas responsabilidades:
1. Responder perguntas baseado EXCLUSIVAMENTE no contexto fornecido
2. Se a informação não estiver no contexto, dizer claramente "Não tenho essa informação"
3. Ser conciso e preciso
4. Usar linguagem profissional e amigável
5. Solicitar esclarecimentos se a pergunta for ambígua

REGRAS CRÍTICAS:
- NUNCA invente informações que não estão no contexto
- NUNCA faça especulações ou suposições
- NUNCA cite fontes que não existem
- Se múltiplas respostas são possíveis, esclareça as opções

Responda em Português (Brasil)."""


def build_user_prompt(query: str, context: str) -> str:
    """
    Prompt do usuário com instrução clara sobre contexto.
    """
    return f"""Contexto disponível:
---
{context}
---

Pergunta do cliente: {query}

Baseando-se EXCLUSIVAMENTE no contexto acima, responda à pergunta."""


# ============================================
# HALLUCINATION PREVENTION
# ============================================

def validate_response(
    response_text: str,
    context: str,
    query: str
) -> Tuple[bool, str]:
    """
    Validações para detectar possíveis alucinações:
    1. Não mencionar documentos não fornecidos
    2. Não fazer referências fora do contexto
    3. Verificar se usa linguagem de incerteza apropriadamente
    
    Returns:
        (is_valid, validation_message)
    """
    # Markers de alucinação potencial
    hallucination_markers = [
        "segundo minha análise geral",
        "pesquisei e encontrei",
        "estudos mostram",
        "em geral é sabido",
        "historicamente",
        "estatísticas mostram",
        "fontes externas",
    ]
    
    response_lower = response_text.lower()
    
    # Verificar marcadores
    for marker in hallucination_markers:
        if marker in response_lower:
            return False, f"Possível alucinação detectada: '{marker}'"
    
    # Verificar se resposta é apropriadamente curta quando não há contexto
    if not context.strip() and len(response_text) > 200:
        return False, "Resposta muito longa para falta de contexto"
    
    # Verificar se reconhece falta de informação apropriadamente
    uncertainty_keywords = [
        "não sei",
        "não tenho informação",
        "não está no contexto",
        "não foi fornecido",
        "não posso confirmar",
    ]
    
    # Se não há contexto relevante, deve expressar incerteza
    if not context.strip():
        has_uncertainty = any(keyword in response_lower for keyword in uncertainty_keywords)
        if not has_uncertainty and not response_text.lower().startswith("não"):
            return False, "Deve expressar incerteza quando não há contexto"
    
    return True, "Validação passada"


# ============================================
# RESPONSE GENERATION
# ============================================

def generate_response(
    db: Session,
    cliente_id: int,
    pergunta: str,
    contexto: str,
    chunks_recuperados: int,
    score_relevancia: float
) -> Dict[str, Any]:
    """
    Gera resposta usando LLM com contexto RAG.
    
    Retorna dicionário com:
    - resposta: texto da resposta
    - tokens_prompt: tokens usados no prompt
    - tokens_completion: tokens usados na resposta
    - custo_api: custo em USD
    - validacao_passou: se passou na validação de alucinação
    """
    
    try:
        # Obter nome do cliente
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        cliente_nome = cliente.nome if cliente else "Usuário"
        
        # Construir prompts
        system_prompt = build_system_prompt(cliente_nome)
        user_prompt = build_user_prompt(pergunta, contexto)
        
        logger.info(f"Calling LLM with model {OPENAI_MODEL}")
        
        # Chamar OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Baixa criatividade para evitar alucinações
            max_tokens=500,
            top_p=0.9,
        )
        
        resposta_texto = response.choices[0].message.content
        
        # Extrair uso de tokens
        tokens_prompt = response.usage.prompt_tokens
        tokens_completion = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens
        
        # Calcular custo aproximado (preços ada-002)
        # Embedding: $0.0001 per 1K tokens
        # Chat: $0.001 / $0.002 per 1K tokens (prompt/completion)
        custo_api = (tokens_prompt * 0.0005 + tokens_completion * 0.0015) / 1000
        
        # Validar resposta
        validacao_passou, validacao_msg = validate_response(resposta_texto, contexto, pergunta)
        
        if not validacao_passou:
            logger.warning(f"Response validation failed: {validacao_msg}")
        
        logger.info(f"Response generated: {tokens_completion} tokens, ${custo_api:.6f}")
        
        return {
            "resposta": resposta_texto,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "total_tokens": total_tokens,
            "custo_api": custo_api,
            "validacao_passou": validacao_passou,
            "validacao_msg": validacao_msg,
            "modelo": OPENAI_MODEL
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise


# ============================================
# MAIN RAG PIPELINE
# ============================================

def process_query(
    db: Session,
    cliente_id: int,
    pergunta: str,
    canal_id: int = 1
) -> Dict[str, Any]:
    """
    Pipeline completo RAG:
    1. Gerar embedding da pergunta
    2. Buscar chunks similares
    3. Construir contexto
    4. Gerar resposta
    5. Validar resposta
    6. Salvar mensagem no BD
    
    Returns:
        Dicionário com resultado completo da processamento
    """
    
    inicio_processamento = datetime.utcnow()
    
    try:
        logger.info(f"Processing query for cliente {cliente_id}: {pergunta[:50]}...")
        
        # 1. Gerar embedding da pergunta
        query_embedding = generate_query_embedding(pergunta)
        
        # 2. Buscar chunks similares
        chunks_similares = search_similar_chunks(
            db, cliente_id, query_embedding,
            top_k=TOP_K_CHUNKS,
            min_score=MIN_SIMILARITY_SCORE
        )
        
        # Verificar se encontrou chunks suficientes
        if len(chunks_similares) < MIN_RELEVANT_CHUNKS:
            logger.warning(f"Insufficient relevant chunks: {len(chunks_similares)} < {MIN_RELEVANT_CHUNKS}")
            
            return {
                "sucesso": False,
                "resposta": "Desculpe, não encontrei informações relevantes para responder sua pergunta. Por favor, reformule ou entre em contato com o suporte.",
                "chunks_recuperados": 0,
                "score_relevancia": 0.0,
                "tempo_processamento_ms": int((datetime.utcnow() - inicio_processamento).total_seconds() * 1000),
                "razao_falha": "insufficient_context"
            }
        
        # 3. Construir contexto
        contexto, chunks_usados, score_relevancia = build_context(chunks_similares)
        
        # 4. Gerar resposta
        resultado_ia = generate_response(
            db, cliente_id, pergunta, contexto,
            len(chunks_similares), score_relevancia
        )
        
        # 4.5 MULTIMODALIDADE: Sugerir imagem para acompanhar a resposta
        sugestao_imagem = suggest_image_for_response(
            db, cliente_id, pergunta, resultado_ia["resposta"], contexto
        )
        
        # 5. Salvar mensagem no BD com status AGUARDANDO_APROVACAO
        canal = db.query(Canal).filter(Canal.id == canal_id).first()
        if not canal:
            canal_id = 1  # Fallback
        
        tempo_processamento_ms = int((datetime.utcnow() - inicio_processamento).total_seconds() * 1000)
        
        mensagem = MensagemAtendimento(
            cliente_id=cliente_id,
            canal_id=canal_id,
            pergunta=pergunta,
            resposta_ia=resultado_ia["resposta"],
            status="AGUARDANDO_APROVACAO",
            chunks_recuperados=len(chunks_similares),
            score_relevancia=score_relevancia,
            tempo_processamento_ms=tempo_processamento_ms,
            modelo_ia=resultado_ia["modelo"],
            tokens_prompt=resultado_ia["tokens_prompt"],
            tokens_completion=resultado_ia["tokens_completion"],
            custo_api=resultado_ia["custo_api"],
            # MULTIMODALIDADE
            necessita_visual=sugestao_imagem["deve_incluir_imagem"],
            imagem_sugerida_id=sugestao_imagem.get("midia_sugerida_id"),
            imagem_url=sugestao_imagem.get("url_imagem")
        )
        db.add(mensagem)
        db.commit()
        db.refresh(mensagem)
        
        logger.info(f"Query processed successfully: message_id={mensagem.id}")
        
        return {
            "sucesso": True,
            "mensagem_id": mensagem.id,
            "resposta": resultado_ia["resposta"],
            "chunks_recuperados": len(chunks_similares),
            "score_relevancia": float(score_relevancia),
            "tempo_processamento_ms": tempo_processamento_ms,
            "tokens_prompt": resultado_ia["tokens_prompt"],
            "tokens_completion": resultado_ia["tokens_completion"],
            "custo_api": float(resultado_ia["custo_api"]),
            "validacao_passou": resultado_ia["validacao_passou"],
            # MULTIMODALIDADE
            "necessita_visual": sugestao_imagem["deve_incluir_imagem"],
            "imagem_sugerida": {
                "url": sugestao_imagem.get("url_imagem"),
                "nome": sugestao_imagem.get("nome_arquivo"),
                "descricao": sugestao_imagem.get("descricao"),
                "tipo": sugestao_imagem.get("tipo_midia"),
                "score": sugestao_imagem.get("score_relevancia")
            } if sugestao_imagem["deve_incluir_imagem"] else None,
            "chunks_details": [
                {
                    "numero": chunk.numero_chunk,
                    "documento": chunk.documento.nome_arquivo,
                    "score": float(score)
                }
                for chunk, score in chunks_similares[:5]
            ]
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        tempo_processamento_ms = int((datetime.utcnow() - inicio_processamento).total_seconds() * 1000)
        
        return {
            "sucesso": False,
            "resposta": "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente.",
            "tempo_processamento_ms": tempo_processamento_ms,
            "razao_falha": str(e)
        }


# ============================================
# UTILITY FUNCTIONS
# ============================================

def get_cliente_statistics(db: Session, cliente_id: int) -> Dict[str, Any]:
    """
    Retorna estatísticas de um cliente.
    """
    try:
        # Contar documentos
        total_docs = db.query(Documento).filter(
            Documento.cliente_id == cliente_id,
            Documento.status == "SUCESSO"
        ).count()
        
        # Contar chunks
        total_chunks = db.query(Chunk).join(Documento).filter(
            Documento.cliente_id == cliente_id
        ).count()
        
        # Contar mensagens
        total_mensagens = db.query(MensagemAtendimento).filter(
            MensagemAtendimento.cliente_id == cliente_id
        ).count()
        
        # Score médio
        from sqlalchemy import func
        avg_score = db.query(func.avg(MensagemAtendimento.score_relevancia)).filter(
            MensagemAtendimento.cliente_id == cliente_id
        ).scalar() or 0.0
        
        return {
            "total_documentos": total_docs,
            "total_chunks": total_chunks,
            "total_mensagens": total_mensagens,
            "score_relevancia_medio": float(avg_score)
        }
        
    except Exception as e:
        logger.error(f"Error getting client statistics: {e}")
        return {}


# ============================================
# MULTIMODAL SUPPORT FUNCTIONS
# ============================================

def detect_visual_need(pergunta: str, resposta: str) -> bool:
    """
    Detecta se a pergunta/resposta se beneficiaria de uma explicação visual.
    
    Palavras-chave indicadoras de necessidade visual:
    - Instruções, procedimentos, passos
    - Diagramas, gráficos, tabelas
    - Layouts, interfaces, estruturas
    - Instalação, montagem, configuração
    - Arquitetura, fluxograma
    
    Args:
        pergunta: Pergunta do usuário
        resposta: Resposta gerada pela IA
    
    Returns:
        True se a resposta seria melhor com uma imagem visual
    """
    
    visual_keywords = [
        # Instalação e Setup
        "instalar", "instalação", "passo a passo", "como instalar",
        "setup", "configurar", "configuração",
        
        # Instruções
        "manual", "guia", "tutorial", "instruções", "como fazer",
        "procedimento", "processo", "etapas", "passos",
        
        # Visuais
        "diagrama", "gráfico", "tabela", "layout", "interface",
        "interface de usuário", "ui", "ux", "tela",
        "estrutura", "arquitetura", "fluxograma", "fluxo",
        
        # Técnicos
        "circuito", "componente", "hardware", "wiring", "fiação",
        "dimensão", "tamanho", "proporção", "escala",
        
        # Localização
        "onde", "localização", "posição", "encontrar",
        
        # Visual explícito
        "imagem", "foto", "ilustração", "desenho", "esboço", "mapa"
    ]
    
    texto_completo = (pergunta + " " + resposta).lower()
    
    # Contar keywords visuais presentes
    visual_count = sum(1 for keyword in visual_keywords if keyword in texto_completo)
    
    # Se houver múltiplas keywords visuais, provavelmente precisa de imagem
    return visual_count >= 2


def find_relevant_images(
    db: Session,
    cliente_id: int,
    pergunta: str,
    contexto: str,
    query_embedding: Optional[np.ndarray] = None,
    limite: int = 5
) -> List[Tuple[Any, float]]:
    """
    Encontra imagens relevantes nos documentos do cliente.
    
    Estratégia de busca:
    1. Buscar por documento dos chunks mais relevantes
    2. Filtrar imagens do mesmo documento
    3. Ordenar por relevância
    
    Args:
        db: Sessão do banco
        cliente_id: ID do cliente
        pergunta: Pergunta do usuário
        contexto: Contexto RAG construído
        query_embedding: Embedding da pergunta (para busca semântica)
        limite: Número máximo de imagens a retornar
    
    Returns:
        Lista de (MidiaDocumento, score_relevancia)
    """
    
    try:
        from sqlalchemy import func
        
        # Encontrar documentos relevantes (aqueles com chunks no contexto)
        documentos_ids = db.query(Documento.id).filter(
            Documento.cliente_id == cliente_id,
            Documento.contem_imagens == True,
            Documento.status == "SUCESSO"
        ).all()
        
        if not documentos_ids:
            logger.debug(f"No documents with images found for cliente {cliente_id}")
            return []
        
        documento_ids_list = [d[0] for d in documentos_ids]
        
        # Buscar mídias dos documentos relevantes
        midias = db.query(MidiaDocumento).filter(
            MidiaDocumento.documento_id.in_(documento_ids_list),
            MidiaDocumento.url_publica.isnot(None)  # Apenas mídias com URL pública
        ).all()
        
        if not midias:
            logger.debug(f"No public media URLs found")
            return []
        
        # Calcular relevância de cada mídia baseado em:
        # 1. Similaridade com a pergunta (keywords)
        # 2. Score armazenado no BD
        # 3. Proximidade com chunks relevantes
        
        resultados_com_score = []
        
        for midia in midias:
            # Score base do banco
            score_base = float(midia.score_relevancia) if midia.score_relevancia else 0.3
            
            # Bonus por keywords na descrição
            descricao_lower = (midia.descricao or "").lower()
            pergunta_lower = pergunta.lower()
            
            bonus_descricao = 0
            if descricao_lower and pergunta_lower:
                # Contar palavras-chave compartilhadas
                palavras_pergunta = set(pergunta_lower.split())
                palavras_descricao = set(descricao_lower.split())
                matches = len(palavras_pergunta & palavras_descricao)
                bonus_descricao = min(matches * 0.1, 0.3)
            
            # Score final
            score_final = min(score_base + bonus_descricao, 1.0)
            
            resultados_com_score.append((midia, score_final))
        
        # Ordenar por relevância e limitar
        resultados_com_score.sort(key=lambda x: x[1], reverse=True)
        top_results = resultados_com_score[:limite]
        
        logger.info(f"Found {len(top_results)} relevant images (limit={limite})")
        return top_results
        
    except Exception as e:
        logger.error(f"Error finding relevant images: {e}")
        return []


def suggest_image_for_response(
    db: Session,
    cliente_id: int,
    pergunta: str,
    resposta_ia: str,
    contexto: str
) -> Dict[str, Any]:
    """
    Sugere uma imagem para acompanhar a resposta.
    
    Retorna dicionário com:
    - deve_incluir_imagem: bool
    - midia_sugerida: MidiaDocumento ou None
    - url_imagem: string com URL pública ou None
    - motivo: string explicando a sugestão
    
    Returns:
        Dict com sugestão de imagem
    """
    
    try:
        # 1. Detectar se a resposta precisa de visual
        necessita_visual = detect_visual_need(pergunta, resposta_ia)
        
        if not necessita_visual:
            return {
                "deve_incluir_imagem": False,
                "midia_sugerida": None,
                "motivo": "Resposta textual é suficiente"
            }
        
        # 2. Procurar imagens relevantes
        imagens_relevantes = find_relevant_images(
            db, cliente_id, pergunta, contexto, limite=1
        )
        
        if not imagens_relevantes:
            return {
                "deve_incluir_imagem": False,
                "midia_sugerida": None,
                "motivo": "Nenhuma imagem relevante encontrada no conhecimento base"
            }
        
        # 3. Selecionar melhor imagem
        midia_top, score = imagens_relevantes[0]
        
        logger.info(f"Suggesting image: {midia_top.nome_arquivo} (score={score:.2f})")
        
        return {
            "deve_incluir_imagem": True,
            "midia_sugerida": midia_top,
            "midia_sugerida_id": midia_top.id,
            "url_imagem": midia_top.url_publica,
            "nome_arquivo": midia_top.nome_arquivo,
            "descricao": midia_top.descricao,
            "tipo_midia": midia_top.tipo_midia,
            "score_relevancia": float(score),
            "motivo": f"Imagem relevante ({midia_top.tipo_midia}) para ilustrar a resposta"
        }
        
    except Exception as e:
        logger.error(f"Error suggesting image: {e}")
        return {
            "deve_incluir_imagem": False,
            "midia_sugerida": None,
            "motivo": f"Erro ao processar: {str(e)}"
        }

