"""
Utilitário de divisão de texto para SistemaRAG
Implementa chunking inteligente com overlap preservando contexto
"""

import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    separators: Optional[List[str]] = None
) -> List[str]:
    """
    Divide texto em chunks com overlap preservando estrutura semântica
    
    Args:
        text: Texto completo a ser dividido
        chunk_size: Tamanho máximo de cada chunk (caracteres)
        overlap: Número de caracteres de sobreposição entre chunks
        separators: Lista de separadores em ordem de prioridade
        
    Returns:
        Lista de chunks de texto
    """
    if not text or len(text.strip()) == 0:
        return []
    
    if separators is None:
        separators = [
            "\n\n",  # Parágrafos
            "\n",    # Linhas
            ". ",    # Sentenças
            "! ",    # Exclamações
            "? ",    # Perguntas
            "; ",    # Ponto e vírgula
            ", ",    # Vírgulas
            " ",     # Espaços
            ""       # Caracteres individuais (último recurso)
        ]
    
    # Normalizar whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Se estamos no final do texto
        if end >= len(text):
            chunks.append(text[start:].strip())
            break
        
        # Tentar encontrar o melhor separador
        chunk_text = text[start:end]
        best_split = -1
        best_separator = ""
        
        for separator in separators:
            if separator == "":
                # Último recurso: dividir no meio
                best_split = end
                best_separator = ""
                break
            
            # Procurar separador mais próximo do fim
            pos = chunk_text.rfind(separator)
            if pos != -1:
                best_split = start + pos + len(separator)
                best_separator = separator
                break
        
        if best_split == -1 or best_split <= start:
            # Não encontrou separador, forçar divisão
            best_split = end
        
        chunk = text[start:best_split].strip()
        if chunk:
            chunks.append(chunk)
        
        # Avançar com overlap
        start = best_split - overlap if best_split > overlap else best_split
        
        # Evitar loop infinito
        if start >= len(text):
            break
    
    return [c for c in chunks if c.strip()]


def split_by_tokens(
    text: str,
    max_tokens: int = 500,
    overlap_tokens: int = 50,
    encoding_name: str = "cl100k_base"
) -> List[str]:
    """
    Divide texto por tokens (aproximado) para modelos LLM
    
    Args:
        text: Texto a dividir
        max_tokens: Máximo de tokens por chunk
        overlap_tokens: Tokens de overlap
        encoding_name: Nome do encoding tiktoken
        
    Returns:
        Lista de chunks
    """
    try:
        import tiktoken
        encoding = tiktoken.get_encoding(encoding_name)
    except ImportError:
        logger.warning("tiktoken não instalado, usando divisão por caracteres aproximada")
        # Aproximação: 1 token ≈ 4 caracteres em português
        char_per_token = 4
        return split_text_into_chunks(
            text,
            chunk_size=max_tokens * char_per_token,
            overlap=overlap_tokens * char_per_token
        )
    
    tokens = encoding.encode(text)
    
    if len(tokens) <= max_tokens:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(tokens):
        end = start + max_tokens
        
        if end >= len(tokens):
            chunk_tokens = tokens[start:]
            chunks.append(encoding.decode(chunk_tokens))
            break
        
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        
        # Tentar quebrar em palavra completa
        last_space = chunk_text.rfind(' ')
        if last_space > len(chunk_text) * 0.5:  # Pelo menos metade do chunk
            chunk_text = chunk_text[:last_space]
            # Recalcular tokens
            actual_tokens = encoding.encode(chunk_text)
            end = start + len(actual_tokens)
        
        chunks.append(chunk_text)
        start = end - overlap_tokens
        
        if start >= len(tokens):
            break
    
    return chunks


def create_semantic_chunks(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    min_chunk_size: int = 100
) -> List[str]:
    """
    Cria chunks tentando preservar unidades semânticas (parágrafos, seções)
    
    Args:
        text: Texto completo
        chunk_size: Tamanho alvo do chunk
        overlap: Overlap entre chunks
        min_chunk_size: Tamanho mínimo aceitável
        
    Returns:
        Lista de chunks semanticamente coerentes
    """
    # Primeiro, dividir em parágrafos
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    if not paragraphs:
        return split_text_into_chunks(text, chunk_size, overlap)
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para_size = len(para)
        
        # Se o parágrafo sozinho é maior que chunk_size, dividir
        if para_size > chunk_size:
            # Flush current chunk if any
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # Dividir o parágrafo grande
            sub_chunks = split_text_into_chunks(para, chunk_size, overlap)
            chunks.extend(sub_chunks[:-1])  # Todos menos o último
            current_chunk = [sub_chunks[-1]] if sub_chunks else []
            current_size = len(current_chunk[0]) if current_chunk else 0
        elif current_size + para_size + 2 > chunk_size:  # +2 para \n\n
            # Chunk atual cheio, iniciar novo
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_size = para_size
        else:
            # Adicionar ao chunk atual
            current_chunk.append(para)
            current_size += para_size + 2
    
    # Adicionar último chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    # Aplicar overlap entre chunks se necessário
    if overlap > 0 and len(chunks) > 1:
        overlapped_chunks = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            curr_chunk = chunks[i]
            
            # Pegar final do chunk anterior
            overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
            # Encontrar início de palavra
            space_pos = overlap_text.find(' ')
            if space_pos != -1:
                overlap_text = overlap_text[space_pos+1:]
            
            overlapped_chunks.append(overlap_text + '\n\n' + curr_chunk)
        
        chunks = overlapped_chunks
    
    # Filtrar chunks muito pequenos
    chunks = [c for c in chunks if len(c) >= min_chunk_size]
    
    return chunks


if __name__ == "__main__":
    # Teste rápido
    test_text = """
    Este é o primeiro parágrafo do texto de teste. Ele contém várias sentenças.
    Esta é a segunda sentença. E esta é a terceira sentença do primeiro parágrafo.
    
    Este é o segundo parágrafo. Ele também tem múltiplas sentenças.
    Aqui continuamos o texto. Mais uma sentença.
    
    Terceiro parágrafo com conteúdo diferente. 
    Informações sobre políticas da empresa.
    Regras de reembolso e garantia.
    """ * 10  # Repetir para criar texto maior
    
    print("=== Teste split_text_into_chunks ===")
    chunks = split_text_into_chunks(test_text, chunk_size=500, overlap=100)
    print(f"Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i+1} ({len(chunk)} chars):")
        print(chunk[:200] + "...")
    
    print("\n=== Teste create_semantic_chunks ===")
    semantic_chunks = create_semantic_chunks(test_text, chunk_size=500, overlap=100)
    print(f"Total semantic chunks: {len(semantic_chunks)}")
    for i, chunk in enumerate(semantic_chunks[:3]):
        print(f"\nSemantic Chunk {i+1} ({len(chunk)} chars):")
        print(chunk[:200] + "...")