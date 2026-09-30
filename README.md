# 🧠 RAG System - Sistema Inteligente de Atendimento com Aprovação Humana

Documentação completa e guide prático para implementação e uso do Sistema RAG (Retrieval Augmented Generation) com Human-in-the-Loop.

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Requisitos e Pré-requisitos](#requisitos-e-pré-requisitos)
4. [Guia de Instalação](#guia-de-instalação)
5. [Explicação File-by-File](#explicação-file-by-file)
6. [Explicação da Engenharia de RAG](#explicação-da-engenharia-de-rag)
7. [Usando o Sistema](#usando-o-sistema)
8. [Extensões Futuras (WhatsApp & Outlook)](#extensões-futuras)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

### O que é o RAG System?

Um sistema completo de **atendimento automatizado com aprovação humana** que:

1. **Ingere documentos** de conhecimento (PDF, DOCX, XLSX, TXT)
2. **Fragmenta e indexa** o conteúdo com embeddings vetoriais
3. **Processa perguntas** via busca semântica (RAG)
4. **Gera respostas** usando LLM (OpenAI GPT)
5. **Exibe para aprovação** em um painel intuitivo
6. **Permite edição e aprovação** antes do envio final
7. **Registra auditoria** completa de todas as ações

### Características Principais

✅ **Arquitetura Multi-tenant** - Suporte para múltiplos clientes independentes
✅ **RAG com Prevenção de Alucinações** - Respostas baseadas apenas no contexto fornecido
✅ **Human-in-the-Loop** - Operadores validam respostas antes do envio
✅ **Pipeline Assíncrono** - Processamento eficiente de documentos
✅ **Auditoria Completa** - Rastreamento de todas as ações
✅ **Dashboard Intuitivo** - Interface React moderna com Tailwind CSS
✅ **Containerizado com Docker** - Deploy fácil e reproduzível
✅ **Pronto para Webhooks** - Estrutura preparada para WhatsApp e Outlook

---

## 🏗️ Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND REACT                           │
│         (Dashboard + Fila de Aprovação + Interface)         │
│                  :3000                                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              FASTAPI BACKEND (Python)                        │
│                    :8000                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • Upload & Ingestão de Documentos                   │   │
│  │  • Pipeline RAG (Busca Semântica + LLM)              │   │
│  │  • Fila de Aprovação (CRUD de Mensagens)             │   │
│  │  • API REST (Endpoints estruturados)                 │   │
│  └──────────────────────────────────────────────────────┘   │
└────────┬────────────────────────┬────────────────────────────┘
         │                        │
         ▼                        ▼
┌──────────────────┐     ┌──────────────────────┐
│   MySQL 8.0      │     │  OpenAI API          │
│   (Dados + VDs)  │     │  (Embeddings + LLM)  │
│   :3306          │     │                      │
└──────────────────┘     └──────────────────────┘
```

### Fluxo de Dados

#### 1. Ingestão de Documentos
```
Upload de Arquivo
       ↓
Validação (tipo, tamanho)
       ↓
Extração de Texto (PDF/DOCX/XLSX/TXT)
       ↓
Fragmentação em Chunks (com overlap)
       ↓
Geração de Embeddings (OpenAI API)
       ↓
Armazenamento no MySQL (chunks + vetores serializados)
       ↓
Status = SUCESSO
```

#### 2. Processamento de Pergunta (RAG)
```
Recebe Pergunta do Cliente
       ↓
Gera Embedding da Pergunta (OpenAI)
       ↓
Busca Semântica (Similaridade Cosseno)
       ↓
Recupera Top-K Chunks Relevantes
       ↓
Constrói Contexto (validação de tokens)
       ↓
Chama LLM com System Prompt + Context
       ↓
Valida Resposta (detecção de alucinações)
       ↓
Salva com Status = AGUARDANDO_APROVACAO
       ↓
Exibe no Dashboard para Operador Humano
```

#### 3. Aprovação Humana
```
Operador Visualiza Resposta IA
       ↓
┌─────────────────────────────┐
│ Escolhe uma ação:          │
│ • Aprovar (com edição)      │
│ • Rejeitar (com motivo)     │
└─────────────────────────────┘
       ↓
Registra Auditoria
       ↓
Atualiza Status (APROVADA / REJEITADA)
       ↓
Marca para Envio (ENVIADA)
```

---

## 📦 Requisitos e Pré-requisitos

### Mínimos

- **Docker & Docker Compose** (recomendado: versão 20.10+)
- **OpenAI API Key** (para embeddings e LLM)
- **Conexão com Internet** (para chamadas OpenAI)

### Recomendados (para desenvolvimento local sem Docker)

- **Python 3.11+**
- **Node.js 18+** e npm
- **MySQL 8.0+**
- **Git**

### Variáveis de Ambiente Essenciais

```bash
# Backend
OPENAI_API_KEY=sk-xxx...
DB_PASSWORD=sua_senha_segura
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

---

## 🚀 Guia de Instalação

### Opção 1: Docker Compose (Recomendado)

#### Passo 1: Clonar o Repositório

```bash
git clone <seu-repositorio> rag-system
cd rag-system
```

#### Passo 2: Configurar Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Editar backend/.env com suas credenciais
nano backend/.env
```

**Valores importantes a configurar:**

```env
OPENAI_API_KEY=sk-sua-chave-aqui
DB_PASSWORD=senha_mysql_segura
DB_ROOT_PASSWORD=senha_root_segura
CORS_ORIGINS=http://localhost:3000,http://seu-dominio.com
```

#### Passo 3: Iniciar os Serviços

```bash
# Build e start
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Passo 4: Verificar Health

```bash
# API Health
curl http://localhost:8000/health

# Frontend
open http://localhost:3000
```

#### Passo 5: Criar Cliente de Teste

```bash
curl -X POST http://localhost:8000/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Cliente Teste",
    "empresa": "Empresa XYZ",
    "descricao": "Cliente para testes"
  }'
```

### Opção 2: Desenvolvimento Local (Sem Docker)

#### Backend

```bash
cd backend

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados (assumindo MySQL já rodando)
mysql -u root -p < schema.sql

# Iniciar servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm start
```

---

## 📄 Explicação File-by-File

### Backend

#### 1. **schema.sql**
**Responsabilidade:** Definição do banco de dados relacional e vetorial

**Tabelas principais:**
- `clientes`: Armazena clientes/empresas (multi-tenant)
- `documentos`: Metadados dos arquivos enviados
- `chunks`: Fragmentos de documentos
- `embeddings`: Vetores de embeddings (serializados como BLOB)
- `mensagens_atendimento`: Transações de atendimento com histórico completo
- `auditoria`: Log de todas as ações

**Views úteis:**
- `vw_fila_aprovacao`: Filtra mensagens aguardando aprovação
- `vw_performance_ia`: Estatísticas diárias
- `vw_documentos_cliente`: Documentos por cliente

**Por que essa estrutura?**
- Normalização: Reduz redundância e garante integridade
- Índices estratégicos: Otimiza queries de busca frequentes
- JSON columns: Flexibilidade para dados variáveis (auditoria)
- Full-text indexes: Busca rápida em textos

#### 2. **models.py**
**Responsabilidade:** ORM (SQLAlchemy) + Schemas Pydantic

**Componentes:**
- **SQLAlchemy Models**: `Cliente`, `Documento`, `Chunk`, `Embedding`, `MensagemAtendimento`, etc.
- **Pydantic Schemas**: Validação de entrada/saída da API

**Padrões:**
- Relacionamentos bidirecionais (lazy loading)
- Cascade deletes (quando cliente é deletado, tudo vai embora)
- Timestamps automáticos (created_at, updated_at)

**Por que separar dados e schemas?**
- ORM mapeia banco de dados
- Schemas validam requisições HTTP
- Permite diferentes representações (DTO pattern)

#### 3. **database.py**
**Responsabilidade:** Configuração de conexão e gerenciamento de sessões

**Funcionalidades:**
```python
- engine: SQLAlchemy engine com pool otimizado
- SessionLocal: Factory de sessões
- get_db(): Dependency injection para FastAPI
- health_check(): Verifica saúde do BD
- init_db(): Cria tabelas na inicialização
```

**Pool Configuration:**
- `pool_size=10`: Mantém 10 conexões ativas
- `max_overflow=20`: Permite até 20 conexões adicionais
- `pool_recycle=3600`: Recicla conexões (evita "gone away" do MySQL)
- `pool_pre_ping=True`: Testa conexão antes de usar

**Por que esse design?**
- Connection pooling: Reutiliza conexões (performance)
- Health checks: Evita erros silenciosos
- Dependency injection: Cada request recebe sua sessão

#### 4. **ingestion.py**
**Responsabilidade:** Pipeline completo de ingestão de documentos

**5 Fases:**

**1. Validação**
```python
validate_file()
- Valida extensão
- Valida tamanho (MAX_FILE_SIZE_MB)
- Retorna (is_valid, error_message)
```

**2. Extração de Texto** (polimórfica por tipo)
```python
extract_text_from_pdf()   → PdfReader (pypdf)
extract_text_from_docx()  → Document (python-docx)
extract_text_from_xlsx()  → Workbook (openpyxl)
extract_text_from_txt()   → open()
```

**3. Fragmentação (Chunking)**
```python
create_chunks(text, chunk_size=1000, overlap=200)
Estratégia:
- Divide em pedaços de ~1000 caracteres
- Mantém 200 caracteres de sobreposição
- Quebra em espaços/newlines (não corta palavras)
Razão: Preserva contexto entre chunks
```

**4. Geração de Embeddings**
```python
generate_embeddings_batch(texts)
- Agrupa em lotes de até 2048 textos
- Chama OpenAI API (text-embedding-ada-002)
- Retorna array numpy de dimensão 1536
```

**5. Persistência**
```python
save_document_to_db()     → Metadados
save_chunks_to_db()       → Chunks
save_embeddings_to_db()   → Vetores (pickle.dumps)
mark_document_complete()  → Status = SUCESSO
```

**Por que essa separação?**
- Modularidade: Cada função tem responsabilidade única
- Reusabilidade: Funções podem ser chamadas independentemente
- Testabilidade: Fácil mockar cada etapa
- Assincronismo: Processamento em background

#### 5. **rag_engine.py**
**Responsabilidade:** Coração do RAG - Busca semântica + LLM

**Pipeline RAG em 5 etapas:**

**1. Embedding da Pergunta**
```python
generate_query_embedding(query)
→ OpenAI API
→ numpy array (1536 dimensões)
```

**2. Busca Semântica**
```python
search_similar_chunks(db, cliente_id, query_embedding)
Algoritmo:
for cada chunk do cliente:
    embedding_chunk = deserialize(blob)
    score = cosine_similarity(query_emb, chunk_emb)
    if score >= MIN_SIMILARITY_SCORE:
        results.append((chunk, score))
sort by score (descendente)
return top_k

Similaridade Cosseno:
  cos(θ) = (a · b) / (||a|| * ||b||)
  Resultado: 0.0 a 1.0
```

**Por que cosseno?**
- Independente de magnitude (apenas direção importa)
- Eficiente em alta dimensionalidade
- Interpretável (ângulo entre vetores)

**3. Construção de Contexto**
```python
build_context(chunks_with_scores)
Estratégia:
- Ordena por relevância
- Inclui chunks até atingir MAX_CONTEXT_LENGTH
- Quebra em espaços (não corta sentences)
- Adiciona metadados (documento, chunk #)
```

**4. Geração de Resposta**
```python
generate_response(db, cliente_id, pergunta, contexto)
System Prompt:
  "Você é um assistente para {cliente}.
   Responda EXCLUSIVAMENTE baseado no contexto.
   Se não souber, diga 'Não tenho essa informação'."
   
User Prompt:
  "[Contexto]
   ---
   Pergunta: {pergunta}"

Configuração LLM:
  temperature=0.3  → Baixa criatividade
  max_tokens=500   → Respostas concisas
  top_p=0.9        → Diversidade controlada
```

**5. Validação de Alucinação**
```python
validate_response(response, context, query)
Checagens:
- Procura por marcadores de alucinação
  ("segundo minha análise", "estudos mostram")
- Verifica se expressa incerteza quando apropriado
- Detecta respostas genéricas
Retorna: (is_valid, validation_msg)
```

**Por que esses guardrails?**
- LLMs tendem a "alucinar" quando fora do contexto
- Validações adicionais aumentam confiabilidade
- System prompt é o primeiro nível de defesa

#### 6. **main.py**
**Responsabilidade:** API REST FastAPI com todos os endpoints

**7 Grupos de Endpoints:**

**A. Health & Status** (Observabilidade)
```
GET  /health           → Status da API
GET  /status           → Estatísticas gerais
GET  /docs             → Documentação Swagger
```

**B. Gerenciamento de Clientes** (Multi-tenant)
```
POST   /clientes             → Criar cliente
GET    /clientes             → Listar clientes
GET    /clientes/{id}        → Detalhes
GET    /clientes/{id}/stats  → Estatísticas
```

**C. Upload & Ingestão de Documentos**
```
POST   /documentos/upload              → Upload arquivo
GET    /documentos/{id}/status         → Status processamento
GET    /documentos/cliente/{id}        → Listar documentos cliente
```

**D. Pipeline RAG (Processamento de Perguntas)**
```
POST   /mensagens/processar  → Processa pergunta através RAG
                              → Retorna resposta + status AGUARDANDO_APROVACAO
```

**E. Fila de Aprovação (Human-in-the-Loop)**
```
GET    /fila-aprovacao                 → Lista mensagens pendentes
POST   /mensagens/{id}/aprovar         → Aprova/Rejeita
POST   /mensagens/{id}/enviar          → Marca como enviada
```

**F. Feedback & Análise**
```
POST   /mensagens/{id}/feedback        → Coleta satisfação
GET    /relatorios/diario              → Relatório de performance
```

**Padrões de Implementação:**

- **Dependency Injection**: `db: Session = Depends(get_db)`
- **Error Handling**: HTTPException com status codes corretos
- **Background Tasks**: `BackgroundTasks` para ingestão assíncrona
- **Pagination**: `skip` e `limit` em listas
- **Logging**: Registra todas as operações críticas

#### 7. **Dockerfile (Backend)**
**Responsabilidade:** Containerizar aplicação Python

**Multi-stage build:**
- Stage 1 (builder): Compila dependências
- Stage 2 (runtime): Imagem final mínima

**Otimizações:**
- Alpine Linux: Imagem mínima (~150MB vs ~900MB)
- Health check: Docker monitora disponibilidade
- EXPOSE: Documentação de porta
- Non-root user: Segurança (implícito em Alpine)

---

### Frontend

#### 1. **package.json**
**Responsabilidade:** Dependências npm e scripts

**Principais dependências:**
- `react`, `react-dom`: Framework
- `react-router-dom`: Roteamento (preparação futura)
- `axios`: Cliente HTTP
- `react-query`: Caching/sincronização de dados
- `tailwindcss`: Styling utilitário
- `date-fns`: Manipulação de datas

#### 2. **services/api.js**
**Responsabilidade:** Camada de API com axios

**Features:**
- Configuração centralizada (baseURL, timeout)
- Interceptadores (para autenticação futura)
- Métodos helper para cada endpoint
- Tratamento automático de 401 (token expirado)

**Por que abstração?**
- Evita duplicação de código
- Facilita mudanças futuras de API
- Centraliza tratamento de erros

#### 3. **components/Dashboard.jsx**
**Responsabilidade:** Componente principal - Fila de Aprovação

**Funcionalidades:**
1. **Listagem de Mensagens**
   - Fetch automático de API
   - Auto-refresh (configurável)
   - Filtros por cliente

2. **Visualização de Detalhes**
   - Pergunta original
   - Resposta IA
   - Contexto recuperado (chunks, score)

3. **Ações do Operador**
   - ✓ Aprovar (com edição opcional)
   - ✕ Rejeitar (com motivo)
   - 📤 Enviar (marca como enviada)

4. **Feedback**
   - Coleta satisfação (1-5)
   - Comentários opcionais

**Estado (React Hooks):**
```javascript
messages          → Array de mensagens da API
selectedMessage   → Mensagem selecionada para detalhes
editedResponse    → Texto editado antes de aprovar
loading           → Indica carregamento
autoRefresh       → Flag de auto-atualização
```

#### 4. **components/Alert.jsx**
**Responsabilidade:** Notificações (sucesso, erro, aviso)

**Features:**
- 4 tipos: success, error, warning, info
- Auto-close opcional
- Cores e ícones distintos
- Dismissible manualmente

#### 5. **components/Loader.jsx**
**Responsabilidade:** Indicador de carregamento

**Padrão:** Spinner animado + mensagem

#### 6. **App.jsx**
**Responsabilidade:** Componente raiz

**Funcionalidades:**
- Verificação de health da API
- Roteamento básico
- Tratamento de erro de conexão

#### 7. **index.css**
**Responsabilidade:** Estilos globais + customizações Tailwind

**Inclui:**
- Reset CSS
- Utilidades customizadas (badges, cards)
- Animações (fadeIn, slideDown)
- Responsive breakpoints

#### 8. **tailwind.config.js**
**Responsabilidade:** Configuração do Tailwind CSS

**Customizações:**
- Paleta de cores adicional
- Extensão de spacing
- Plugins de font

#### 9. **Dockerfile (Frontend)**
**Responsabilidade:** Containerizar React + Nginx

**Multi-stage:**
- Stage 1: Build React
- Stage 2: Nginx servindo arquivos estáticos

**Nginx config:**
- SPA fallback (route /index.html)
- Cache headers para assets estáticos
- Compression (gzip)

---

## 🤖 Explicação da Engenharia de RAG

### O que é RAG?

**RAG (Retrieval Augmented Generation)** = LLM + Base de Conhecimento

```
Pergunta → [Busca no Conhecimento] → [Contexto Relevante]
                                           ↓
                              [LLM gera resposta com contexto]
                                           ↓
                                      Resposta Informada
```

**vs Prompt Engineering Tradicional:**

```
❌ Prompt Tradicional:
   "Qual é a política de reembolso da empresa XYZ?"
   → LLM tenta adivinhar do conhecimento geral
   → Resultado: Genérico ou incorreto

✅ RAG:
   Contexto: [Política de reembolso extraída dos documentos da XYZ]
   Pergunta: "Qual é a política de reembolso?"
   → LLM responde baseado no contexto específico
   → Resultado: Preciso e confiável
```

### Arquitetura de Embeddings

#### O que é um Embedding?

Um **embedding** é uma representação numérica (vetor) de um texto em espaço de alta dimensão.

```
Texto: "Reembolso válido em até 30 dias"
                ↓
        [OpenAI API]
                ↓
Embedding: [0.045, -0.123, 0.789, ..., 0.456]  (1536 dimensões)
                ↓
        Armazenado como BLOB (pickle)
```

**Por que embeddings?**
- Captura significado semântico (não apenas palavras-chave)
- Permite busca por similaridade (não exata)
- Redimensional (1536 dimensões para text-embedding-ada-002)

#### Similaridade Cosseno

Como comparamos se dois textos são similares?

```
Fórmula: cos(θ) = (A · B) / (||A|| * ||B||)

Interpretação:
- cos(0°)   = 1.0  → Vetores idênticos (máxima similaridade)
- cos(90°)  = 0.0  → Vetores ortogonais (não relacionados)
- cos(180°) = -1.0 → Vetores opostos

Normalizado para [0, 1]:
  similaridade = (cos + 1) / 2
  0.0 = não relacionado
  0.5 = meio termo
  1.0 = idêntico
```

**Implementação:**

```python
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    mag_a = np.linalg.norm(a)
    mag_b = np.linalg.norm(b)
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return (np.dot(a, b) / (mag_a * mag_b) + 1) / 2
```

**Por que não outras métricas?**
- Euclidean: Magnitude importa (não queremos)
- Manhattan: Menos interpretável
- Dot Product: Muito dependente de magnitude

### Prevenção de Alucinações

**Problema:** LLMs inventam informações que não estão no contexto

```
❌ Alucinação:
Input:  "Quais são os benefícios da empresa?"
Context: (vazio ou irrelevante)
Output: "A empresa oferece vale refeição, vale transporte,
         assistência médica..." (inventado)

✓ Com guardrails:
Output: "Não tenho essas informações no contexto fornecido."
```

#### Estratégias de Prevenção (em rag_engine.py)

**1. System Prompt Restritivo**
```
"Responda EXCLUSIVAMENTE baseado no contexto fornecido.
 Se a informação não estiver no contexto, diga
 'Não tenho essa informação'."
```

**2. Temperature Baixa**
```python
temperature=0.3  # Em vez de padrão 1.0
# Reduz criatividade/alucinações
# Respostas mais "literais" do contexto
```

**3. Validação Pós-Geração**
```python
validate_response(response, context, query)
# Procura por marcadores de alucinação:
# - "segundo minha análise"
# - "pesquisei e encontrei"
# - "estatísticas mostram"
# → Retorna aviso se detectado
```

**4. Threshold de Relevância**
```python
MIN_SIMILARITY_SCORE = 0.5
# Se chunks recuperados têm score < 0.5
# Recusa responder
# "Desculpe, não encontrei informações relevantes"
```

**5. Limite de Contexto**
```python
MAX_CONTEXT_LENGTH = 4000  # tokens
# Não sufoca LLM com contexto demais
# Usa chunks mais relevantes
```

#### Teste de Confiabilidade

Para validar se seu sistema RAG previne alucinações:

```python
# Teste 1: Pergunta fora do escopo
Input:  "Qual é a capital da Itália?"
Context: (documentos sobre política de empresa)
Expected: "Não tenho essa informação"

# Teste 2: Informação parcial
Input:  "Qual é a data limite para reembolso?"
Context: "Reembolsos são válidos dentro de 30 dias"
Expected: "30 dias" (literal do contexto)

# Teste 3: Ambiguidade
Input:  "Qual é a melhor opção?"
Context: (lista de opções, mas sem recomendação)
Expected: Listar opções sem recomendação

# Teste 4: Negação no contexto
Input:  "Oferecemos seguro de vida?"
Context: "NÃO oferecemos seguro de vida"
Expected: "Não, não oferecemos"
```

### Otimizações de Performance

#### 1. Batch Processing de Embeddings
```python
# ❌ Lento: 100 chamadas API
for texto in textos:
    embedding = openai.Embedding.create(input=texto)

# ✓ Rápido: 1 chamada API
embeddings = openai.Embedding.create(input=textos)  # até 2048
```

#### 2. Caching de Embeddings
```
Query
  ↓
Usar embedding existente (se já processado)
  ↓ (evita nova chamada OpenAI)
Busca Semântica
```

#### 3. Índices de Banco de Dados
```sql
-- Busca rápida de chunks por documento
CREATE INDEX idx_documento_id ON chunks(documento_id);

-- Busca rápida de mensagens por status
CREATE INDEX idx_status ON mensagens_atendimento(status);
```

#### 4. Aproximação com Dimensionalidade Reduzida
Para futura otimização com vetores muito grandes:
```python
# PCA: Reduzir 1536 → 512 dimensões
from sklearn.decomposition import PCA
pca = PCA(n_components=512)
reduced_embeddings = pca.fit_transform(embeddings)
```

---

## 📱 Usando o Sistema

### 1. Criar um Cliente

**Via API:**
```bash
curl -X POST http://localhost:8000/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Acme Corp",
    "empresa": "ACME",
    "descricao": "Empresa de tecnologia"
  }'
```

**Resposta:**
```json
{
  "id": 1,
  "nome": "Acme Corp",
  "empresa": "ACME",
  "ativo": true,
  "data_criacao": "2024-01-15T10:30:00"
}
```

### 2. Upload de Documentos

**Via API:**
```bash
curl -X POST http://localhost:8000/documentos/upload?cliente_id=1 \
  -F "file=@politica_reembolso.pdf"
```

**Processo em Background:**
1. Arquivo validado
2. Texto extraído
3. Chunks criados
4. Embeddings gerados
5. Status atualizado para SUCESSO

**Monitorar Progress:**
```bash
curl http://localhost:8000/documentos/{documento_id}/status
```

### 3. Fazer uma Pergunta (RAG)

**Via API:**
```bash
curl -X POST "http://localhost:8000/mensagens/processar?cliente_id=1&pergunta=Qual%20é%20o%20prazo%20para%20reembolso?"
```

**Resposta:**
```json
{
  "sucesso": true,
  "mensagem_id": 42,
  "resposta": "O prazo para reembolso é de 30 dias...",
  "status": "AGUARDANDO_APROVACAO",
  "chunks_recuperados": 3,
  "score_relevancia": 0.87,
  "tempo_processamento_ms": 2150,
  "custo_api": 0.00145
}
```

### 4. Visualizar Fila de Aprovação

**No Dashboard (http://localhost:3000):**
1. Veja lista de mensagens pendentes
2. Clique em uma para ver detalhes
3. Leia pergunta e resposta IA
4. Edite se necessário
5. Aprove ou rejeite

### 5. Aprovar Mensagem

**Via API:**
```bash
curl -X POST http://localhost:8000/mensagens/42/aprovar \
  -H "Content-Type: application/json" \
  -d '{
    "aprovada": true,
    "resposta_editada": "O prazo é de 30 dias corridos...",
    "operador_id": 1
  }'
```

**Resultado:**
- Status: APROVADA
- Resposta editada salva
- Auditoria registrada

### 6. Enviar Mensagem

**Via API:**
```bash
curl -X POST http://localhost:8000/mensagens/42/enviar
```

**Neste ponto em produção:**
- Dispara webhook para WhatsApp API
- Dispara webhook para Outlook/Email
- Status: ENVIADA

### 7. Coletar Feedback

**Via API (após cliente receber):**
```bash
curl -X POST http://localhost:8000/mensagens/42/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "score_satisfacao": 5,
    "feedback_usuario": "Resposta muito útil!"
  }'
```

### 8. Visualizar Relatórios

**Via API:**
```bash
curl http://localhost:8000/relatorios/diario?dias=7
```

**Retorna:**
```json
{
  "periodo": "últimos 7 dias",
  "total_geral": 145,
  "por_dia": {
    "2024-01-15": {
      "total": 23,
      "aprovadas": 21,
      "rejeitadas": 2,
      "tempo_medio_ms": 2100,
      "score_relevancia_medio": 0.82
    }
  }
}
```

---

## 🔌 Extensões Futuras

### Integração com WhatsApp (Meta Cloud API)

#### Passo 1: Setup Meta Cloud API

```
1. Ir para https://developers.facebook.com
2. Criar app (tipo: Negócios)
3. Adicionar produto "WhatsApp"
4. Gerar token e confirmar número
```

#### Passo 2: Configurar Webhook no Backend

```python
# backend/webhooks.py

from fastapi import WebhookRouter

webhook_router = WebhookRouter()

@webhook_router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    """
    Webhook recebe mensagens do WhatsApp.
    Processa pelo RAG e enfileira para aprovação.
    """
    data = await request.json()
    
    # Validar assinatura Meta
    # if not verify_signature(request, WEBHOOK_SECRET):
    #     return {"error": "Invalid signature"}
    
    # Extrair informações da mensagem
    message_id = data['entry'][0]['changes'][0]['value']['messages'][0]['id']
    sender_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
    texto = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    
    # Processar através RAG
    resultado = process_query(
        db, cliente_id=1, pergunta=texto, canal_id=1
    )
    
    # Enfilerar para aprovação
    mensagem = MensagemAtendimento(
        cliente_id=1,
        canal_id=1,  # WhatsApp
        identificador_externo=message_id,
        pergunta=texto,
        resposta_ia=resultado['resposta'],
        status="AGUARDANDO_APROVACAO"
    )
    db.add(mensagem)
    db.commit()
    
    # Responder confirmação ao WhatsApp
    return {
        "success": True,
        "message": "Mensagem recebida e enfileirada para aprovação"
    }

@webhook_router.get("/whatsapp/webhook")
async def whatsapp_webhook_verify(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    """
    Meta envia verificação ao registrar webhook.
    """
    if hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Invalid verify token"}
```

#### Passo 3: Função para Enviar Resposta Aprovada

```python
# backend/channels/whatsapp.py

import requests

WHATSAPP_API_URL = "https://graph.instagram.com/v18.0"
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_API_TOKEN")

async def enviar_whatsapp(numero_destino: str, mensagem_texto: str):
    """
    Envia resposta aprovada para WhatsApp.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": mensagem_texto}
    }
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp: {e}")
        return False
```

#### Passo 4: Atualizar Endpoint de Envio

```python
# backend/main.py

@app.post("/mensagens/{mensagem_id}/enviar")
async def enviar_mensagem(
    mensagem_id: int,
    db: Session = Depends(get_db)
):
    mensagem = db.query(MensagemAtendimento).get(mensagem_id)
    
    if mensagem.canal_id == 1:  # WhatsApp
        # Enviar para WhatsApp
        sucesso = await enviar_whatsapp(
            numero_destino=mensagem.identificador_externo,
            mensagem_texto=mensagem.resposta_editada or mensagem.resposta_ia
        )
        
        if sucesso:
            mensagem.status = "ENVIADA"
            mensagem.data_envio = datetime.utcnow()
            db.commit()
            return {"sucesso": True, "status": "ENVIADA"}
    
    # ... outros canais
```

#### Passo 5: Atualizar docker-compose.yml

```yaml
# Adicionar variáveis de ambiente
environment:
  WHATSAPP_WEBHOOK_URL: ${WHATSAPP_WEBHOOK_URL}
  WHATSAPP_VERIFY_TOKEN: ${WHATSAPP_VERIFY_TOKEN}
  WHATSAPP_API_TOKEN: ${WHATSAPP_API_TOKEN}
  WHATSAPP_PHONE_NUMBER_ID: ${WHATSAPP_PHONE_NUMBER_ID}
```

### Integração com Outlook (Microsoft Graph API)

#### Passo 1: Registrar Aplicação Azure

```
1. Ir para https://portal.azure.com
2. Azure Active Directory → App registrations
3. Criar novo app
4. Adicionar permissão: Mail.Read, Mail.Send
5. Gerar client secret
```

#### Passo 2: Implementar OAuth2

```python
# backend/auth/microsoft.py

from msal import PublicClientApplication

TENANT_ID = os.getenv("OUTLOOK_TENANT_ID")
CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")

async def get_access_token():
    """
    Obtém token para Microsoft Graph API.
    """
    app = PublicClientApplication(
        client_id=CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}"
    )
    
    # Para app auth (não interativo)
    token_response = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    
    return token_response['access_token']
```

#### Passo 3: Webhook para Receber Emails

```python
# backend/webhooks.py

@app.post("/outlook/webhook")
async def outlook_webhook(request: Request):
    """
    Subscription change notification do Outlook.
    """
    data = await request.json()
    
    # Microsoft envia validation token na primeira chamada
    if 'validationToken' in data:
        return data['validationToken']
    
    # Processar notificações
    for notification in data['value']:
        email_id = notification['resourceData']['id']
        
        # Buscar email via Graph API
        email_data = await fetch_email(email_id)
        
        # Processar através RAG
        resultado = process_query(
            db,
            cliente_id=1,
            pergunta=email_data['subject'] + " " + email_data['bodyPreview'],
            canal_id=2  # Outlook
        )
        
        # Enfileirar
        mensagem = MensagemAtendimento(
            cliente_id=1,
            canal_id=2,
            identificador_externo=email_id,
            pergunta=email_data['bodyPreview'],
            resposta_ia=resultado['resposta'],
            status="AGUARDANDO_APROVACAO"
        )
        db.add(mensagem)
    
    db.commit()
    return {"status": "success"}

async def fetch_email(email_id: str):
    """
    Busca detalhes do email no Outlook.
    """
    token = await get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    url = f"https://graph.microsoft.com/v1.0/me/messages/{email_id}"
    
    response = requests.get(url, headers=headers)
    return response.json()
```

#### Passo 4: Enviar Resposta por Email

```python
# backend/channels/outlook.py

async def enviar_outlook(email_id: str, resposta: str, email_destino: str):
    """
    Envia resposta via Outlook.
    """
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "subject": f"Re: [Assunto original]",
            "body": {
                "contentType": "HTML",
                "content": resposta
            },
            "toRecipients": [{"emailAddress": {"address": email_destino}}],
            "inReplyTo": email_id
        },
        "saveToSentItems": "true"
    }
    
    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar Outlook: {e}")
        return False
```

### Passo 5: Atualizar docker-compose.yml

```yaml
environment:
  OUTLOOK_CLIENT_ID: ${OUTLOOK_CLIENT_ID}
  OUTLOOK_CLIENT_SECRET: ${OUTLOOK_CLIENT_SECRET}
  OUTLOOK_TENANT_ID: ${OUTLOOK_TENANT_ID}
  OUTLOOK_WEBHOOK_URL: ${OUTLOOK_WEBHOOK_URL}
```

---

## 🐛 Troubleshooting

### Docker Compose

#### "Cannot connect to database"

```bash
# Verificar status MySQL
docker-compose logs db

# Reiniciar BD
docker-compose restart db
docker-compose exec db mysql -u root -p<password> -e "SELECT 1;"
```

#### "ConnectionResetError" ao processar documentos

```bash
# Aumentar pool_size em database.py
pool_size=20
max_overflow=30

# Ou reiniciar containers
docker-compose restart backend
```

### API Errors

#### 500 - Error generating embeddings

```bash
# Verificar OpenAI API key
echo $OPENAI_API_KEY

# Testar conectividade
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 400 - Invalid file type

```bash
# Verificar ALLOWED_FILE_TYPES
# Padrão: pdf,docx,xlsx,txt,doc,xls

# Adicionar novo tipo
ALLOWED_FILE_TYPES=pdf,docx,xlsx,txt,pptx,ppt
```

### Frontend Issues

#### "Failed to fetch" no browser

```bash
# Verificar CORS
# Em backend/.env
CORS_ORIGINS=http://localhost:3000,http://seu-dominio.com

# Verificar backend está rodando
curl http://localhost:8000/health
```

#### "Max request size exceeded"

```bash
# Aumentar limite de arquivo
# Em main.py, adicionar:
from fastapi.middleware import gzip
app.add_middleware(gzip.GZIPMiddleware, minimum_size=1000)

# E em .env
MAX_FILE_SIZE_MB=100
```

### Database Issues

#### "MySQL has gone away"

```python
# Já configurado em database.py
pool_recycle=3600
pool_pre_ping=True

# Mas se persistir, aumentar:
pool_recycle=1800  # 30 minutos
```

#### "Disk quota exceeded" (servidor MySQL)

```bash
# Limpar embeddings/chunks antigos
# Adicionar job de cleanup em main.py

from apscheduler.schedulers.background import BackgroundScheduler

@app.on_event("startup")
async def startup():
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_old_documents, "cron", hour=2, minute=0)
    scheduler.start()

def cleanup_old_documents():
    """Remove documentos com 30+ dias sem uso"""
    with get_db_session() as db:
        threshold = datetime.utcnow() - timedelta(days=30)
        db.query(Documento).filter(
            Documento.data_processamento < threshold
        ).delete()
        db.commit()
```

---

## 📊 Monitoramento & Observabilidade

### Logs

```bash
# Backend
docker-compose logs -f backend

# Frontend
docker-compose logs -f frontend

# MySQL
docker-compose logs -f db
```

### Métricas

```bash
# Estatísticas gerais
curl http://localhost:8000/status

# Por cliente
curl http://localhost:8000/clientes/1/statistics

# Relatório diário
curl "http://localhost:8000/relatorios/diario?dias=7"
```

### Health Checks

```bash
# API
curl http://localhost:8000/health

# BD
docker-compose exec db mysqladmin ping -u root -p<password>

# Frontend (Nginx)
curl http://localhost:3000/health
```

---

## 🚀 Deploy em Produção

### Checklist

- [ ] Trocar SECRET_KEY (settings.py)
- [ ] Configurar CORS_ORIGINS (domínios reais)
- [ ] HTTPS habilitado
- [ ] Backups automáticos MySQL
- [ ] Monitoring (Sentry, DataDog, etc)
- [ ] Rate limiting
- [ ] Autenticação real (JWT + DB de usuários)
- [ ] Logs centralizados
- [ ] CI/CD pipeline (GitHub Actions)

### Exemplo docker-compose.prod.yml

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_PASSWORD: ${DB_PASSWORD}
    volumes:
      - mysql_data_prod:/var/lib/mysql
      - ./backups:/backups
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10
    networks:
      - rag_network

  backend:
    image: rag-backend:latest
    restart: always
    environment:
      APP_ENV: production
      DATABASE_URL: mysql+pymysql://${DB_USER}:${DB_PASSWORD}@db:3306/${DB_NAME}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    networks:
      - rag_network
    depends_on:
      db:
        condition: service_healthy

  frontend:
    image: rag-frontend:latest
    restart: always
    networks:
      - rag_network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    networks:
      - rag_network
    depends_on:
      - backend
      - frontend

volumes:
  mysql_data_prod:

networks:
  rag_network:
```

---

## 📚 Recursos Adicionais

- [OpenAI API Docs](https://platform.openai.com/docs)
- [FastAPI Tutorial](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org)
- [Tailwind CSS](https://tailwindcss.com)
- [Docker Compose](https://docs.docker.com/compose)

---

## ✅ Checklist de Implementação

- [ ] Clonar repositório
- [ ] Configurar .env files
- [ ] docker-compose up
- [ ] Verificar health checks
- [ ] Criar cliente de teste
- [ ] Upload documento teste
- [ ] Fazer pergunta teste
- [ ] Aprovar resposta
- [ ] Visualizar no Dashboard
- [ ] Verificar logs e auditoria
- [ ] Configurar webhooks (WhatsApp/Outlook)
- [ ] Deploy em produção

---

**Desenvolvido com ❤️ para automação inteligente de atendimento.**

**Versão: 1.0.0 | Última atualização: 2024-01-15**
