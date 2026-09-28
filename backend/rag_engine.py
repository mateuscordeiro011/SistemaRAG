"""
Motor RAG otimizado para SistemaRAG
Busca vetorial e processamento de respostas com rastreabilidade
"""

import logging
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_
from datetime import datetime

from models import Chunk, MensagemAtendimento, RespostaChunk, Configuracao
from utils.embedding_client import embedding_client

logger = logging.getLogger(__name__)


class RAGEngine:
    """Motor RAG otimizado com rastreabilidade de fontes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def processar_pergunta(
        self,
        pergunta: str,
        cliente_id: int,
        canal: str = "web",
        usuario_id: Optional[int] = None,
    ) -> MensagemAtendimento:
        """
        Processa uma pergunta completa do recebimento até envio
        
        Args:
            pergunta: Pergunta a processar
            cliente_id: ID do cliente proprietário
            canal: Canal de comunicação (whatsapp, email, web, teste)
            usuario_id: ID do usuário (operador) se aplicável
        
        Returns:
            MensagemAtendimento processada e salva no banco
        """
        try:
            logger.info(f"Iniciando processamento pergunta cliente {cliente_id}")
            
            # 1. Buscar resposta via RAG
            resposta, chunks_detalhes, score_relevancia = await self.buscar_resposta_rag(
                pergunta,
                cliente_id
            )
            
            if not resposta:
                resposta = "Desculpe, não consegui encontrar uma resposta adequada em nossa base de conhecimento."
                score_relevancia = 0.0
            
            # 2. Obter configurações do cliente
            config = self.db.query(Configuracao).filter_by(cliente_id=cliente_id).first()
            limiar = config.limiar_confianca if config else 0.75
            
            # ✅ 3. APLICAR LÓGICA DE LIMIAR DE CONFIANÇA
            if score_relevancia >= limiar:
                # Envio automático
                status = "ENVIADA_AUTOMATICA"
                requer_aprovacao = False
                logger.info(
                    f"Score {score_relevancia:.2f} >= limiar {limiar:.2f} "
                    f"→ Envio automático"
                )
            else:
                # Fila de aprovação humana
                status = "AGUARDANDO_APROVACAO"
                requer_aprovacao = True
                logger.info(
                    f"Score {score_relevancia:.2f} < limiar {limiar:.2f} "
                    f"→ Fila de aprovação"
                )
            
            # 4. Criar objeto de mensagem
            mensagem = MensagemAtendimento(
                cliente_id=cliente_id,
                usuario_id=usuario_id,
                pergunta=pergunta,
                resposta=resposta,
                canal=canal,
                status=status,
                score_relevancia=score_relevancia,
                requer_aprovacao=requer_aprovacao,
                processado_em=datetime.utcnow(),
            )
            
            self.db.add(mensagem)
            self.db.flush()  # Sincronizar ID
            
            # 5. Registrar chunks consultados (rastreabilidade)
            await self._registrar_chunks_consultados(
                mensagem.id,
                chunks_detalhes
            )
            
            self.db.commit()
            
            logger.info(f"Mensagem {mensagem.id} processada com status {status}")
            
            return mensagem
            
        except Exception as e:
            logger.error(f"Erro ao processar pergunta: {e}", exc_info=True)
            self.db.rollback()
            raise
    
    async def buscar_resposta_rag(
        self,
        pergunta: str,
        cliente_id: int,
        max_chunks: Optional[int] = None,
    ) -> Tuple[str, List[dict], float]:
        """
        Busca resposta usando RAG (Retrieval-Augmented Generation)
        
        ✅ OTIMIZADO: Sem N+1 queries!
        
        Args:
            pergunta: Pergunta a processar
            cliente_id: ID do cliente
            max_chunks: Máximo de chunks a usar (default: config.max_chunks_resposta)
        
        Returns:
            Tupla (resposta, chunks_detalhes, score_relevancia)
        """
        try:
            # 1. Obter configurações
            config = self.db.query(Configuracao).filter_by(cliente_id=cliente_id).first()
            max_chunks = max_chunks or (config.max_chunks_resposta if config else 5)
            
            # 2. Gerar embedding da pergunta
            pergunta_embedding = await embedding_client.encode([pergunta])
            pergunta_vec = pergunta_embedding[0]
            
            # ✅ 3. BUSCAR CHUNKS COM SINGLE QUERY (não N+1!)
            chunks = self.db.query(Chunk).filter(
                and_(
                    Chunk.cliente_id == cliente_id,
                    Chunk.deletado == False,
                    Chunk.embedding_vector.isnot(None)
                )
            ).all()
            
            if not chunks:
                logger.warning(f"Nenhum chunk encontrado para cliente {cliente_id}")
                return "", [], 0.0
            
            # ✅ 4. PROCESSAR EMBEDDINGS EM BATCH (cálculo vetorizado)
            embeddings_array = np.array([
                np.frombuffer(c.embedding_vector, dtype=np.float32)
                for c in chunks
            ])
            
            # Cálculo vetorizado de similaridade (muito mais rápido)
            similaridades = self._calcular_similaridade_cosseno(
                pergunta_vec,
                embeddings_array
            )
            
            # 5. Ordenar por relevância
            indices_ordenados = np.argsort(similaridades)[::-1]  # Ordem decrescente
            
            # 6. Selecionar top-K chunks
            top_indices = indices_ordenados[:max_chunks]
            chunks_selecionados = [
                (chunks[i], similaridades[i])
                for i in top_indices
            ]
            
            # 7. Construir resposta
            textos_chunk = "\n\n".join([
                f"[Fonte {idx+1}]\n{chunk.conteudo_texto}"
                for idx, (chunk, _) in enumerate(chunks_selecionados)
            ])
            
            # 8. Gerar resposta com LLM (simulado aqui, integrar com seu LLM)
            resposta = await self._gerar_resposta_com_llm(
                pergunta,
                textos_chunk
            )
            
            # 9. Score de relevância (média dos top chunks)
            score_relevancia = float(np.mean([s for _, s in chunks_selecionados]))
            
            # 10. Preparar detalhes dos chunks consultados
            chunks_detalhes = [
                {
                    "chunk_id": chunk.id,
                    "documento_id": chunk.midia_documento_id,
                    "relevancia_score": float(score),
                    "posicao": idx + 1,
                    "conteudo": chunk.conteudo_texto[:100],  # Preview
                }
                for idx, (chunk, score) in enumerate(chunks_selecionados)
            ]
            
            logger.info(
                f"RAG processado: {len(chunks_selecionados)} chunks "
                f"de {len(chunks)} disponíveis, score={score_relevancia:.2f}"
            )
            
            return resposta, chunks_detalhes, score_relevancia
            
        except Exception as e:
            logger.error(f"Erro no RAG: {e}", exc_info=True)
            return "", [], 0.0
    
    async def _registrar_chunks_consultados(
        self,
        mensagem_id: int,
        chunks_detalhes: List[dict]
    ):
        """
        ✅ NOVO - Registra chunks consultados para rastreabilidade
        
        Args:
            mensagem_id: ID da mensagem
            chunks_detalhes: Lista com detalhes dos chunks
        """
        try:
            for detalhe in chunks_detalhes:
                resposta_chunk = RespostaChunk(
                    mensagem_id=mensagem_id,
                    chunk_id=detalhe["chunk_id"],
                    relevancia_score=detalhe["relevancia_score"],
                    posicao=detalhe["posicao"],
                )
                self.db.add(resposta_chunk)
            
            self.db.commit()
            logger.info(f"Registrados {len(chunks_detalhes)} chunks consultados")
            
        except Exception as e:
            logger.error(f"Erro ao registrar chunks: {e}")
            self.db.rollback()
            raise
    
    @staticmethod
    def _calcular_similaridade_cosseno(
        vetor1: np.ndarray,
        vetores2: np.ndarray
    ) -> np.ndarray:
        """
        Calcula similaridade cosseno de forma vetorizada
        
        MUITO mais rápido que loop Python!
        
        Args:
            vetor1: Vetor pergunta (1D)
            vetores2: Matriz de embeddings (2D)
        
        Returns:
            Array de similaridades [0, 1]
        """
        # Normalizar vetores
        vetor1_norm = vetor1 / (np.linalg.norm(vetor1) + 1e-10)
        vetores2_norm = vetores2 / (np.linalg.norm(vetores2, axis=1, keepdims=True) + 1e-10)
        
        # Produto escalar (similaridade cosseno)
        similaridades = np.dot(vetores2_norm, vetor1_norm)
        
        # Normalizar para [0, 1]
        similaridades = (similaridades + 1) / 2
        
        return similaridades
    
    async def _gerar_resposta_com_llm(
        self,
        pergunta: str,
        contexto: str
    ) -> str:
        """
        Gera resposta usando LLM (placeholder)
        
        Integrar com seu LLM de escolha (Llama2, GPT, Claude, etc)
        
        Args:
            pergunta: Pergunta original
            contexto: Texto dos chunks encontrados
        
        Returns:
            Resposta gerada
        """
        try:
            # Placeholder: integrar com seu LLM
            # Exemplos:
            # - Ollama (self-hosted Llama2)
            # - OpenAI GPT
            # - Anthropic Claude
            # - HuggingFace inference
            
            prompt = f"""Baseado no contexto fornecido, responda a pergunta de forma clara e concisa.

Pergunta: {pergunta}

Contexto:
{contexto}

Resposta:"""
            
            # Aqui você integraria com seu LLM
            # Por enquanto, retorna um placeholder
            resposta = f"Baseando-me nos documentos fornecidos, a resposta para '{pergunta}' é: [resposta a ser gerada pelo LLM]"
            
            return resposta
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return ""


class RAGRepository:
    """Repositório para operações de busca RAG"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def buscar_chunks_cliente(
        self,
        cliente_id: int,
        excluir_documentos: List[int] = None
    ) -> List[Chunk]:
        """
        Busca todos os chunks de um cliente (otimizado)
        
        Args:
            cliente_id: ID do cliente
            excluir_documentos: Lista de IDs de documentos a excluir
        
        Returns:
            Lista de chunks
        """
        query = self.db.query(Chunk).filter(
            and_(
                Chunk.cliente_id == cliente_id,
                Chunk.deletado == False,
                Chunk.embedding_vector.isnot(None)
            )
        )
        
        if excluir_documentos:
            query = query.filter(
                not_(Chunk.midia_documento_id.in_(excluir_documentos))
            )
        
        return query.all()
    
    def obter_chunks_mensagem(self, mensagem_id: int) -> List[dict]:
        """
        Obtém chunks consultados para uma mensagem (com rastreabilidade)
        
        Args:
            mensagem_id: ID da mensagem
        
        Returns:
            Lista de dicts com chunks e scores
        """
        respostas = self.db.query(RespostaChunk).filter_by(
            mensagem_id=mensagem_id
        ).order_by(RespostaChunk.posicao).all()
        
        return [
            {
                "chunk_id": rc.chunk_id,
                "conteudo": rc.chunk.conteudo_texto,
                "relevancia_score": rc.relevancia_score,
                "posicao": rc.posicao,
                "documento_nome": rc.chunk.documento.nome_original,
                "pagina": rc.chunk.numero_pagina,
            }
            for rc in respostas
        ]
    
    def limpar_embeddings_cliente(self, cliente_id: int) -> int:
        """
        Remove embeddings de um cliente (libera espaço)
        
        Args:
            cliente_id: ID do cliente
        
        Returns:
            Número de chunks afetados
        """
        count = self.db.query(Chunk).filter_by(
            cliente_id=cliente_id
        ).update({Chunk.embedding_vector: None})
        
        self.db.commit()
        logger.info(f"Removidos embeddings de {count} chunks")
        return count


# Instância global (usar com cuidado)
_engine_instance = None


def get_rag_engine(db: Session) -> RAGEngine:
    """Factory para obter instância do RAG Engine"""
    return RAGEngine(db)